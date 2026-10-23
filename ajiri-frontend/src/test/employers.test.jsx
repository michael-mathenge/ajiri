import { beforeEach, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from './test-utils'
import Employers from '../pages/Employers'
import EmployerReview from '../pages/EmployerReview'
import apiClient from '../api/client'
vi.mock('../api/client', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
beforeEach(() => vi.resetAllMocks())

it('loads older organisation pages without following remote pagination URLs', async () => {
  apiClient.get.mockImplementation((url) =>
    Promise.resolve({
      data: url.includes('/organisations/')
        ? {
            results: [
              {
                id: url.includes('page=2') ? 2 : 1,
                name: url.includes('page=2')
                  ? 'Second organisation'
                  : 'First organisation',
                status: 'pending',
              },
            ],
            next: url.includes('page=2')
              ? null
              : 'https://untrusted.invalid/ignored',
            previous: url.includes('page=2') ? 'previous' : null,
          }
        : { results: [] },
    })
  )
  render(<Employers />)
  await screen.findByText('First organisation: pending')
  fireEvent.click(screen.getByRole('button', { name: 'Next organisations' }))
  await screen.findByText('Second organisation: pending')
  expect(apiClient.get).toHaveBeenCalledWith(
    '/jobs/employers/organisations/?page=2',
    expect.any(Object)
  )
  expect(
    apiClient.get.mock.calls.some(([url]) => url.startsWith('https:'))
  ).toBe(false)
})

it('submits an organisation for review without claiming publication or payment', async () => {
  apiClient.get.mockResolvedValue({ data: { results: [] } })
  apiClient.post.mockResolvedValue({ data: { id: 1, status: 'pending' } })
  render(<Employers />)
  await screen.findByText('No vacancies submitted.')
  fireEvent.change(screen.getByLabelText('Organisation name'), {
    target: { value: 'Synthetic team' },
  })
  fireEvent.change(screen.getByLabelText('Official website'), {
    target: { value: 'https://example.invalid' },
  })
  fireEvent.click(
    screen.getByRole('button', { name: 'Submit organisation for review' })
  )
  expect(await screen.findByRole('status')).toHaveTextContent(
    'not published yet'
  )
  expect(apiClient.post).toHaveBeenCalledWith(
    '/jobs/employers/organisations/',
    { name: 'Synthetic team', website: 'https://example.invalid' }
  )
  expect(screen.getByText(/Job seekers never pay/)).toBeVisible()
})

it('shows verification failures and never retries a submission automatically', async () => {
  apiClient.get.mockRejectedValue({
    response: {
      status: 403,
      data: { detail: 'Verify your account email first.' },
    },
  })
  render(<Employers />)
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Verify your account email first.'
  )
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('requires an explicit staff decision and evidence before sending review', async () => {
  apiClient.get.mockResolvedValue({
    data: {
      organisations: [
        { id: 7, name: 'Synthetic org', website: 'https://example.invalid' },
      ],
      drafts: [],
    },
  })
  apiClient.post.mockResolvedValue({ data: { status: 'reviewed' } })
  render(<EmployerReview />)
  await screen.findByRole('heading', { name: 'Synthetic org' })
  expect(apiClient.post).not.toHaveBeenCalled()
  fireEvent.change(screen.getByLabelText('Decision'), {
    target: { value: 'approve' },
  })
  fireEvent.change(screen.getByLabelText('Review reason and evidence'), {
    target: { value: 'Synthetic independent source review' },
  })
  fireEvent.click(
    screen.getByRole('button', { name: 'Record review of Synthetic org' })
  )
  await waitFor(() =>
    expect(apiClient.post).toHaveBeenCalledWith(
      '/jobs/employers/organisations/7/review/',
      {
        approve: true,
        reason: 'Synthetic independent source review',
      }
    )
  )
})
