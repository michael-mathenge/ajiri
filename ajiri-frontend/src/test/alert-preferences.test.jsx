import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, expect, test, vi } from 'vitest'
import AlertPreferences from '../components/AlertPreferences'
import AlertUnsubscribe from '../pages/AlertUnsubscribe'
import api from '../api/client'
vi.mock('../api/client', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
beforeEach(() => { vi.resetAllMocks() })

test('legacy enabled preference is not prechecked consent; saving is explicit', async () => {
  api.get.mockResolvedValue({ data: { enabled: true, confirmed: false, eligible: false, policy_version: 'job-alert-email-v1' } })
  api.post.mockResolvedValue({ data: { enabled: true, confirmed: true } })
  render(<AlertPreferences />)
  const box = await screen.findByRole('checkbox')
  await waitFor(() => expect(box).toBeEnabled())
  expect(box).not.toBeChecked(); expect(api.post).not.toHaveBeenCalled()
  fireEvent.click(box); fireEvent.click(screen.getByRole('button', { name: 'Save email choice' }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/profiles/me/alert-preferences/', expect.objectContaining({ enabled: true, policy_version: 'job-alert-email-v1' })))
})

test('failed save reuses same decision key and does not silently disable a session', async () => {
  api.get.mockResolvedValue({ data: { enabled: false, confirmed: false, policy_version: 'job-alert-email-v1' } })
  api.post.mockRejectedValue(new Error('network'))
  render(<AlertPreferences />)
  await waitFor(() => expect(screen.getByRole('checkbox')).toBeEnabled())
  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.click(screen.getByRole('button', { name: 'Save email choice' }))
  await screen.findByText(/could not be confirmed/)
  fireEvent.click(screen.getByRole('button', { name: 'Save email choice' }))
  await waitFor(() => expect(api.post).toHaveBeenCalledTimes(2))
  expect(api.post.mock.calls[0][1].decision_id).toBe(api.post.mock.calls[1][1].decision_id)
})

test('opening unsubscribe fragment never submits before explicit confirmation', async () => {
  api.post.mockResolvedValue({ data: { unsubscribed: true } })
  render(<MemoryRouter initialEntries={['/unsubscribe#token=synthetic-token']}><AlertUnsubscribe /></MemoryRouter>)
  expect(api.post).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: 'Turn off email job alerts' }))
  await screen.findByText(/Email job alerts are off/)
  expect(api.post).toHaveBeenCalledTimes(1)
  expect(api.post).toHaveBeenCalledWith('/profiles/alert-unsubscribe/', { token: 'synthetic-token', confirm: true })
})

test('saving consent never claims that disabled delivery sent an email', async () => {
  api.get.mockResolvedValue({ data: { enabled: false, confirmed: false, policy_version: 'job-alert-email-v1', delivery_status: 'disabled' } })
  api.post.mockResolvedValue({ data: { enabled: true, confirmed: true, delivery_status: 'disabled' } })
  render(<AlertPreferences />)
  await waitFor(() => expect(screen.getByRole('checkbox')).toBeEnabled())
  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.click(screen.getByRole('button', { name: 'Save email choice' }))
  await screen.findByText('Email choice recorded. Delivery is currently disabled for this account.')
  expect(screen.getByText(/Email delivery is currently disabled/)).toBeVisible()
})
