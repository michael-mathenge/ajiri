import { beforeEach, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor } from './test-utils'
import { createApiQueryClient, retryRead } from '../api/queryClient'
import { useApiQuery, useApiInvalidation } from '../hooks/useApiQuery'
import { AuthProvider } from '../components/AppShell'
import { useAuth } from '../hooks/useAuth'
import apiClient from '../api/client'
import { MemoryRouter } from 'react-router-dom'
import Profile from '../pages/Profile'
import JobList from '../pages/JobList'

vi.mock('../api/client', () => ({ default: { get: vi.fn(), patch: vi.fn() } }))
beforeEach(() => {
  vi.resetAllMocks()
  localStorage.clear()
})

function Resource({ url = '/profiles/me/' }) {
  const { data, loading, error } = useApiQuery(url)
  const invalidate = useApiInvalidation()
  return (
    <div>
      {loading ? 'Loading' : error || data.name}
      <button onClick={invalidate}>Refresh reads</button>
    </div>
  )
}

it('deduplicates concurrent reads and reuses fresh data across navigation', async () => {
  apiClient.get.mockResolvedValue({ data: { name: 'Synthetic profile' } })
  const view = render(
    <>
      <Resource />
      <Resource />
    </>
  )
  expect(await screen.findAllByText('Synthetic profile')).toHaveLength(2)
  expect(apiClient.get).toHaveBeenCalledTimes(1)
  view.rerender(<p>Other page</p>)
  view.rerender(<Resource />)
  expect(await screen.findByText('Synthetic profile')).toBeVisible()
  expect(apiClient.get).toHaveBeenCalledTimes(1)
  apiClient.get.mockResolvedValue({ data: { name: 'Updated profile' } })
  fireEvent.click(screen.getByRole('button', { name: 'Refresh reads' }))
  expect(await screen.findByText('Updated profile')).toBeVisible()
  expect(apiClient.get).toHaveBeenCalledTimes(2)
})

it('cancels obsolete URLs so late responses cannot replace current filters', async () => {
  let resolveOld
  apiClient.get.mockImplementation((url) =>
    url === '/jobs/?q=old'
      ? new Promise((resolve) => {
          resolveOld = resolve
        })
      : Promise.resolve({ data: { name: 'New results' } })
  )
  const view = render(<Resource url="/jobs/?q=old" />)
  await waitFor(() => expect(apiClient.get).toHaveBeenCalledTimes(1))
  const oldSignal = apiClient.get.mock.calls[0][1].signal
  view.rerender(<Resource url="/jobs/?q=new" />)
  expect(await screen.findByText('New results')).toBeVisible()
  expect(oldSignal.aborted).toBe(true)
  resolveOld({ data: { name: 'Old results' } })
  expect(screen.queryByText('Old results')).not.toBeInTheDocument()
})

it('bounds read retries and never retries validation, auth or rate-limit failures', async () => {
  for (const status of [400, 401, 403, 404, 409, 429]) {
    expect(retryRead(0, { response: { status } })).toBe(false)
  }
  expect(retryRead(0, { response: { status: 503 } })).toBe(true)
  expect(retryRead(1, new Error('network'))).toBe(false)
  const client = createApiQueryClient()
  client.setDefaultOptions({ queries: { retry: retryRead, retryDelay: 0 } })
  const read = vi
    .fn()
    .mockRejectedValueOnce(new Error('network'))
    .mockResolvedValue('recovered')
  expect(
    await client.fetchQuery({ queryKey: ['synthetic'], queryFn: read })
  ).toBe('recovered')
  expect(read).toHaveBeenCalledTimes(2)
  client.clear()
  expect(createApiQueryClient().getDefaultOptions().mutations.retry).toBe(false)
})

function Session() {
  const { signedIn, setSignedIn } = useAuth()
  return signedIn ? (
    <>
      <Resource />
      <button onClick={() => setSignedIn(false)}>Leave account</button>
    </>
  ) : (
    <button onClick={() => setSignedIn(true)}>Enter next account</button>
  )
}

it('clears private cache between accounts without changing token interceptors', async () => {
  localStorage.setItem('access_token', 'synthetic-test-session')
  apiClient.get
    .mockResolvedValueOnce({ data: { name: 'First account' } })
    .mockResolvedValueOnce({ data: { name: 'Second account' } })
  render(
    <AuthProvider>
      <Session />
    </AuthProvider>
  )
  expect(await screen.findByText('First account')).toBeVisible()
  fireEvent.click(screen.getByRole('button', { name: 'Leave account' }))
  expect(screen.queryByText('First account')).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Enter next account' }))
  expect(screen.queryByText('First account')).not.toBeInTheDocument()
  expect(await screen.findByText('Second account')).toBeVisible()
  expect(apiClient.get).toHaveBeenCalledTimes(2)
})

it('drops private data when another tab changes the account session', async () => {
  localStorage.setItem('access_token', 'synthetic-session-one')
  apiClient.get
    .mockResolvedValueOnce({ data: { name: 'First tab account' } })
    .mockResolvedValueOnce({ data: { name: 'New tab account' } })
  render(
    <AuthProvider>
      <Session />
    </AuthProvider>
  )
  expect(await screen.findByText('First tab account')).toBeVisible()
  act(() =>
    window.dispatchEvent(
      new StorageEvent('storage', {
        key: 'access_token',
        oldValue: 'synthetic-session-one',
        newValue: 'synthetic-session-two',
      })
    )
  )
  expect(screen.queryByText('First tab account')).not.toBeInTheDocument()
  expect(await screen.findByText('New tab account')).toBeVisible()
})

it('refreshes skill matches after a successful profile save', async () => {
  let saved = false
  apiClient.get.mockImplementation((url) =>
    Promise.resolve({
      data:
        url === '/profiles/me/'
          ? {
              full_name: 'Synthetic applicant',
              email: 'synthetic@example.invalid',
              skills: saved ? [{ name: 'Python' }] : [],
            }
          : url.startsWith('/jobs/?')
            ? {
                count: 1,
                results: [
                  {
                    id: 1,
                    title: 'Synthetic job',
                    company_name: 'Synthetic team',
                    publication: { status: 'published', closes_at: '2099-01-01T00:00:00Z' },
                    match_score: saved ? 75 : 0,
                  },
                ],
              }
            : {
                enabled: false,
                confirmed: false,
                policy_version: 'synthetic-policy',
              },
    })
  )
  apiClient.patch.mockImplementation(() => {
    saved = true
    return Promise.resolve({ data: {} })
  })
  render(
    <MemoryRouter>
      <Profile />
      <JobList />
    </MemoryRouter>
  )
  expect(
    await screen.findByRole('link', { name: 'Add skills to see matches' })
  ).toBeVisible()
  fireEvent.change(await screen.findByLabelText('Skills (comma separated)'), {
    target: { value: 'Python' },
  })
  fireEvent.click(
    screen.getByRole('button', { name: 'Save profile', exact: true })
  )
  expect(await screen.findByText('75% skill match')).toBeVisible()
  expect(
    screen.queryByRole('link', { name: 'Add skills to see matches' })
  ).not.toBeInTheDocument()
  expect(apiClient.patch).toHaveBeenCalledTimes(1)
})
