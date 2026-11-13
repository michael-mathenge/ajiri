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
    'Organisation received for staff review.'
  )
  expect(apiClient.post).toHaveBeenCalledWith(
    '/jobs/employers/organisations/',
    { name: 'Synthetic team', website: 'https://example.invalid' }
  )
  expect(screen.getByText(/Job seekers never pay/)).toBeVisible()
})

it('keeps the same vacancy decision on an unknown response and changes it only after success', async () => {
  apiClient.get.mockImplementation((url) =>
    Promise.resolve({
      data: {
        results: url.includes('/organisations/')
          ? [{ id: 1, name: 'Synthetic team', status: 'approved' }]
          : [],
      },
    })
  )
  apiClient.post
    .mockRejectedValueOnce({
      response: { data: { detail: 'Outcome unknown. Refresh review status.' } },
    })
    .mockResolvedValue({ data: { id: 1, status: 'pending' } })
  render(<Employers />)
  await screen.findByRole('heading', { name: 'New vacancy' })
  const fill = () => {
    fireEvent.change(screen.getByLabelText('Job title'), {
      target: { value: 'Synthetic role' },
    })
    fireEvent.change(screen.getByLabelText('Location (include country)'), {
      target: { value: 'Nairobi, Kenya' },
    })
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Synthetic responsibilities' },
    })
    fireEvent.change(screen.getByLabelText('Official application URL'), {
      target: { value: 'https://example.invalid/apply' },
    })
    fireEvent.change(
      screen.getByLabelText('Closing date and time (your local time)'),
      { target: { value: '2027-01-01T17:00' } }
    )
  }
  fill()
  fireEvent.click(
    screen.getByRole('button', { name: 'Submit vacancy for review' })
  )
  await screen.findByText('Outcome unknown. Refresh review status.')
  expect(apiClient.post).toHaveBeenCalledTimes(1)
  const first = apiClient.post.mock.calls[0][1]
  expect(first.submission_id).toMatch(/^[0-9a-f-]{36}$/)
  expect(screen.getByLabelText('Job title')).toHaveValue('Synthetic role')
  fireEvent.click(
    screen.getByRole('button', { name: 'Submit vacancy for review' })
  )
  await screen.findByText(
    'Vacancy received. Check its review status before submitting it again.'
  )
  expect(apiClient.post.mock.calls[1][1]).toEqual(first)
  await waitFor(() =>
    expect(
      screen.getByRole('button', { name: 'Submit vacancy for review' })
    ).toBeEnabled()
  )
  fill()
  fireEvent.click(
    screen.getByRole('button', { name: 'Submit vacancy for review' })
  )
  await waitFor(() => expect(apiClient.post).toHaveBeenCalledTimes(3))
  expect(apiClient.post.mock.calls[2][1].submission_id).not.toBe(
    first.submission_id
  )
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
