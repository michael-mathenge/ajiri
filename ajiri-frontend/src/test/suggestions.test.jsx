import { beforeEach, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen, fireEvent, waitFor, within } from './test-utils'
import Suggestions from '../pages/Suggestions'
import RecommendationAction from '../components/RecommendationAction'
import apiClient from '../api/client'

vi.mock('../api/client', () => ({ default: { get: vi.fn(), patch: vi.fn() } }))
beforeEach(() => vi.resetAllMocks())
const job = {
  id: 7,
  title: 'Synthetic current role',
  company_name: 'Synthetic',
  match_score: 50,
  can_apply: true,
  choice_revision: 0,
  publication: {
    status: 'published',
    available_until: '2099-01-01',
    closes_at: '2099-01-01',
  },
}

it('shows low-score suggestions, dismisses one explicitly and restores it with the current revision', async () => {
  let dismissed = false
  let revision = 0
  apiClient.get.mockImplementation((url) =>
    Promise.resolve({
      data:
        url === '/profiles/me/'
          ? { skills: [{ id: 1 }] }
          : url.includes('/dismissed/')
            ? {
                count: dismissed ? 1 : 0,
                results: dismissed ? [{ job, revision, dismissed }] : [],
              }
            : {
                count: dismissed ? 0 : 1,
                results: dismissed
                  ? []
                  : [{ ...job, choice_revision: revision }],
              },
    })
  )
  apiClient.patch.mockImplementation((_url, values) => {
    expect(values.expected_revision).toBe(revision)
    dismissed = values.dismissed
    revision += 1
    return Promise.resolve({ data: { job, revision, dismissed } })
  })
  render(
    <MemoryRouter initialEntries={['/suggestions']}>
      <Suggestions />
    </MemoryRouter>
  )
  const dismiss = await screen.findByRole('button', {
    name: 'Dismiss suggestion: Synthetic current role',
  })
  expect(
    screen.getByRole('heading', { name: 'Synthetic current role', exact: true })
  ).toBeVisible()
  expect(screen.getByRole('link', { name: 'Browse all jobs' })).toHaveAttribute(
    'href',
    '/'
  )
  fireEvent.click(dismiss)
  const region = screen.getByRole('region', { name: 'Dismissed suggestions' })
  const restore = await within(region).findByRole('button', {
    name: 'Restore suggestion: Synthetic current role',
  })
  expect(
    screen.queryByRole('button', {
      name: 'Dismiss suggestion: Synthetic current role',
    })
  ).not.toBeInTheDocument()
  expect(apiClient.patch).toHaveBeenCalledWith('/jobs/7/suggestion-choice/', {
    expected_revision: 0,
    dismissed: true,
  })
  fireEvent.click(restore)
  await screen.findByRole('button', {
    name: 'Dismiss suggestion: Synthetic current role',
  })
  expect(apiClient.patch).toHaveBeenLastCalledWith(
    '/jobs/7/suggestion-choice/',
    { expected_revision: 1, dismissed: false }
  )
  expect(apiClient.patch).toHaveBeenCalledTimes(2)
})

it('blocks mutation retries until an explicit current-state read succeeds and keeps all errors', async () => {
  apiClient.patch
    .mockRejectedValueOnce({
      response: { data: { dismissed: ['Choice changed.', 'Refresh first.'] } },
    })
    .mockResolvedValue({ data: {} })
  apiClient.get
    .mockRejectedValueOnce({
      response: { data: { detail: 'Read temporarily unavailable.' } },
    })
    .mockResolvedValue({ data: { revision: 3, dismissed: false } })
  render(<RecommendationAction job={job} revision={0} />)
  fireEvent.click(
    screen.getByRole('button', {
      name: 'Dismiss suggestion: Synthetic current role',
    })
  )
  await screen.findByText('Choice changed.')
  expect(screen.getByText('Refresh first.')).toBeVisible()
  expect(
    screen.getByRole('button', {
      name: 'Dismiss suggestion: Synthetic current role',
    })
  ).toBeDisabled()
  expect(apiClient.patch).toHaveBeenCalledTimes(1)
  expect(apiClient.get).not.toHaveBeenCalled()
  fireEvent.click(
    screen.getByRole('button', {
      name: 'Refresh suggestions before trying again',
    })
  )
  await screen.findByText('Read temporarily unavailable.')
  expect(
    screen.getByRole('button', {
      name: 'Dismiss suggestion: Synthetic current role',
    })
  ).toBeDisabled()
  fireEvent.click(
    screen.getByRole('button', {
      name: 'Refresh suggestions before trying again',
    })
  )
  await waitFor(() =>
    expect(
      screen.getByRole('button', {
        name: 'Dismiss suggestion: Synthetic current role',
      })
    ).toBeEnabled()
  )
  fireEvent.click(
    screen.getByRole('button', {
      name: 'Dismiss suggestion: Synthetic current role',
    })
  )
  await waitFor(() => expect(apiClient.patch).toHaveBeenCalledTimes(2))
  expect(apiClient.patch).toHaveBeenLastCalledWith(
    '/jobs/7/suggestion-choice/',
    { expected_revision: 3, dismissed: true }
  )
})
