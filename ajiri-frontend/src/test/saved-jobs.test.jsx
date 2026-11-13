import { beforeEach, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen, fireEvent, waitFor } from './test-utils'
import SavedJobs from '../pages/SavedJobs'
import SavedJobButton from '../components/SavedJobButton'
import apiClient from '../api/client'

vi.mock('../api/client', () => ({
  default: { get: vi.fn(), put: vi.fn(), delete: vi.fn() },
}))
beforeEach(() => vi.resetAllMocks())

it('saves exactly one explicit reference and then removes only that saved job', async () => {
  let saved = false
  apiClient.get.mockImplementation(() =>
    Promise.resolve({
      data: { job_id: 7, saved, saved_at: saved ? '2027-01-01' : null },
    })
  )
  apiClient.put.mockImplementation(() => {
    saved = true
    return Promise.resolve({ data: { saved } })
  })
  apiClient.delete.mockImplementation(() => {
    saved = false
    return Promise.resolve({ status: 204 })
  })
  render(<SavedJobButton jobId={7} />)
  fireEvent.click(await screen.findByRole('button', { name: 'Save job' }))
  await screen.findByRole('button', { name: 'Remove saved job' })
  expect(apiClient.put).toHaveBeenCalledWith('/jobs/7/saved/', {})
  expect(apiClient.put).toHaveBeenCalledTimes(1)
  fireEvent.click(screen.getByRole('button', { name: 'Remove saved job' }))
  await screen.findByRole('button', { name: 'Save job' })
  expect(apiClient.delete).toHaveBeenCalledWith('/jobs/7/saved/')
})

it('labels unavailable references honestly and retains safe source links without preparation controls', async () => {
  apiClient.get.mockResolvedValue({
    data: {
      count: 1,
      results: [
        {
          job: {
            id: 7,
            title: 'Unverified reference',
            company_name: 'Synthetic',
            can_apply: false,
          },
          saved_at: '2027-01-01',
          reference_url: 'https://example.invalid/source',
        },
      ],
    },
  })
  render(
    <MemoryRouter>
      <SavedJobs />
    </MemoryRouter>
  )
  await screen.findByRole('heading', {
    name: 'Unverified reference, Synthetic',
  })
  expect(
    screen.getByText(/Reference only: current availability is not verified/)
  ).toBeVisible()
  expect(
    screen.queryByRole('link', { name: 'View current job' })
  ).not.toBeInTheDocument()
  expect(
    screen.getByRole('link', {
      name: 'Open saved source reference (opens in a new tab)',
    })
  ).toHaveAttribute('rel', 'noopener noreferrer')
  expect(apiClient.put).not.toHaveBeenCalled()
})

it('keeps all failed-save messages and never retries a mutation automatically', async () => {
  apiClient.get.mockResolvedValue({ data: { saved: false } })
  apiClient.put.mockRejectedValue({
    response: {
      data: {
        detail: 'Could not confirm saved status.',
        job: ['No current evidence.', 'Refresh first.'],
      },
    },
  })
  render(<SavedJobButton jobId={7} />)
  fireEvent.click(await screen.findByRole('button', { name: 'Save job' }))
  await screen.findByText('No current evidence.')
  expect(screen.getByText('Refresh first.')).toBeVisible()
  expect(screen.getByText('Could not confirm saved status.')).toBeVisible()
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Save job' })).toBeEnabled()
  )
  expect(apiClient.put).toHaveBeenCalledTimes(1)
})
