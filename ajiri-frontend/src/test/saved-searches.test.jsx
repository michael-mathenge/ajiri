import { beforeEach, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen, fireEvent, waitFor } from './test-utils'
import SavedSearches from '../pages/SavedSearches'
import apiClient from '../api/client'

vi.mock('../api/client', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
beforeEach(() => vi.resetAllMocks())
const search = {
  id: 'synthetic-search',
  revision: 3,
  name: 'Python roles',
  q: 'Python',
  location: 'Kenya',
  job_type: '',
  in_app_frequency: 'daily',
  email_frequency: 'off',
}
function show(entry = '/saved-searches') {
  render(
    <MemoryRouter initialEntries={[entry]}>
      <SavedSearches />
    </MemoryRouter>
  )
}

it('prefills current query but defaults both channels off and never grants email consent', async () => {
  apiClient.get.mockResolvedValue({ data: { count: 0, results: [] } })
  apiClient.post.mockResolvedValue({ data: { id: 'new' } })
  show('/saved-searches?q=Python&location=Kenya&job_type=contract')
  await screen.findByText('No saved searches yet.')
  expect(screen.getByLabelText('Job keywords')).toHaveValue('Python')
  expect(screen.getByLabelText('In-app frequency')).toHaveValue('off')
  expect(
    screen.getByLabelText('Email frequency (sending disabled)')
  ).toHaveValue('off')
  fireEvent.change(screen.getByLabelText('Search name'), {
    target: { value: 'My search' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Save search' }))
  expect(await screen.findByRole('status')).toHaveTextContent(
    'does not authorize or send email'
  )
  expect(apiClient.post).toHaveBeenCalledWith('/jobs/saved-searches/', {
    name: 'My search',
    q: 'Python',
    location: 'Kenya',
    job_type: 'contract',
    in_app_frequency: 'off',
    email_frequency: 'off',
  })
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})

it('edits with the displayed revision and keeps every returned validation message', async () => {
  apiClient.get.mockResolvedValue({ data: { results: [search] } })
  apiClient.patch.mockRejectedValue({
    response: {
      data: {
        q: ['Too many words.', 'Each word must be shorter.'],
        detail: 'Reload the current revision.',
      },
    },
  })
  show()
  fireEvent.click(
    await screen.findByRole('button', { name: 'Edit Python roles' })
  )
  fireEvent.change(
    screen.getByLabelText('Email frequency (sending disabled)'),
    { target: { value: 'weekly' } }
  )
  fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
  await screen.findByText('Too many words.')
  expect(screen.getByText('Each word must be shorter.')).toBeVisible()
  expect(screen.getByLabelText('Job keywords')).toHaveAttribute(
    'aria-describedby',
    'saved-search-q-error'
  )
  expect(screen.getByText('Job keywords:')).toBeVisible()
  expect(screen.getByText('Reload the current revision.')).toBeVisible()
  expect(apiClient.patch).toHaveBeenCalledWith(
    '/jobs/saved-searches/synthetic-search/',
    expect.objectContaining({ expected_revision: 3, email_frequency: 'weekly' })
  )
  expect(apiClient.patch).toHaveBeenCalledTimes(1)
})

it('removes only the selected private search without a send request', async () => {
  apiClient.get.mockResolvedValue({ data: { results: [search] } })
  apiClient.delete.mockResolvedValue({ status: 204 })
  show()
  fireEvent.click(
    await screen.findByRole('button', { name: 'Remove Python roles' })
  )
  expect(await screen.findByRole('status')).toHaveTextContent(
    'future checks are stopped'
  )
  expect(apiClient.delete).toHaveBeenCalledWith(
    '/jobs/saved-searches/synthetic-search/'
  )
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('hides expired matches and never follows arbitrary pagination URLs', async () => {
  apiClient.get.mockImplementation((url) =>
    Promise.resolve({
      data: url.includes('/matches/')
        ? {
            results: [
              {
                id: 1,
                title: 'Expired role',
                publication: {
                  status: 'published',
                  available_until: '2000-01-01',
                },
              },
            ],
            next: url.includes('page=2')
              ? null
              : 'https://untrusted.invalid/ignored',
            previous: null,
          }
        : { results: [search], next: null },
    })
  )
  show()
  fireEvent.click(
    await screen.findByRole('button', { name: 'Show matches for Python roles' })
  )
  await screen.findByText(/No current matches yet/)
  expect(screen.queryByText('Expired role')).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Next matches' }))
  await waitFor(() =>
    expect(apiClient.get).toHaveBeenCalledWith(
      '/jobs/saved-searches/synthetic-search/matches/?page=2',
      expect.any(Object)
    )
  )
  expect(
    apiClient.get.mock.calls.some(([url]) => url.startsWith('https:'))
  ).toBe(false)
})

it('shows a request failure rather than claiming there are no saved searches', async () => {
  apiClient.get.mockRejectedValue({
    response: {
      data: { detail: 'Saved searches are temporarily unavailable.' },
    },
  })
  show()
  await screen.findByText('Saved searches are temporarily unavailable.')
  expect(screen.queryByText('No saved searches yet.')).not.toBeInTheDocument()
})
