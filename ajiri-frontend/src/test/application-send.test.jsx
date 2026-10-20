import { beforeEach, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import apiClient from '../api/client'
import ApplicationSendPanel from '../components/ApplicationSendPanel'
import ApplicationPackageReview from '../components/ApplicationPackageReview'

vi.mock('../api/client', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
const plan = { schema_version: 1, package_id: 'package-1', revision: 1,
  recipient: 'owner-controlled@example.invalid', reply_to: 'applicant@example.invalid',
  sender: 'platform@example.invalid', sender_name: 'Ajiri', subject: '[AJIRI PILOT] Synthetic job',
  body: 'Exact saved email <literal>', copy_to_self: false, retry_of: null,
  attachments: [{ role: 'cv', filename: 'Applicant_CV_Company.docx', size: 30000 },
    { role: 'cover-letter', filename: 'Applicant_Cover_Letter_Company.docx', size: 31000 }] }
const preview = { plan, plan_sha256: 'a'.repeat(64), dispatch_enabled: false, disabled_reason: 'Pilot activation is pending final approval.' }
const record = { ...preview, id: 'authorization-1', request_key: 'request-1', state: 'authorized',
  expires_at: '2026-10-21T12:00:00Z', attempt: null }
const button = () => screen.getByRole('button', { name: 'Review email plan / check authorization status' })
const view = (props = {}) => <ApplicationSendPanel applicationId={7} packageId="package-1" {...props} />
const open = async () => {
  render(view())
  fireEvent.click(button())
  await screen.findByText('Exact saved email <literal>')
}
const authorize = async () => {
  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.click(screen.getByRole('button', { name: 'Record authorization (does not send)' }))
  await screen.findByText('Authorized; no dispatch recorded.')
}
beforeEach(() => {
  vi.resetAllMocks()
  apiClient.get.mockImplementation(async (url) => ({ data: url.endsWith('send-plan/') ? preview
    : url.endsWith('send-authorizations/') ? { results: [] } : record }))
  apiClient.post.mockResolvedValue({ data: record })
})

it('separates document approval, exact plan review and unchecked authorization without dispatch', async () => {
  await open()
  expect(screen.getByRole('checkbox')).not.toBeChecked()
  expect(screen.getByRole('button', { name: 'Record authorization (does not send)' })).toBeDisabled()
  expect(screen.getByText(/Copies: OFF/)).toBeVisible()
  expect(screen.getByText(/Applicant_CV_Company.docx/)).toBeVisible()
  expect(screen.getByText('Pilot activation is pending final approval.')).toBeVisible()
  expect(apiClient.post).not.toHaveBeenCalled()
  await authorize()
  expect(apiClient.post).toHaveBeenCalledExactlyOnceWith('/jobs/applications/7/send-authorizations/', {
    request_key: expect.any(String), package_id: 'package-1', expected_revision: 1,
    plan_sha256: preview.plan_sha256, authorization: true,
  })
  expect(screen.getByRole('button', { name: 'Send this authorized application' })).toBeDisabled()
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
})

it('requires a separate explicit send action and labels provider acceptance accurately', async () => {
  apiClient.get.mockImplementation(async (url) => ({ data: url.endsWith('send-plan/') ? { ...preview, dispatch_enabled: true } : { results: [] } }))
  apiClient.post.mockResolvedValueOnce({ data: { ...record, dispatch_enabled: true } })
  await open(); await authorize()
  expect(apiClient.post).toHaveBeenCalledTimes(1)
  apiClient.post.mockResolvedValueOnce({ data: { ...record, state: 'dispatch_started', attempt: { id: 'attempt-1', state: 'accepted' } } })
  fireEvent.click(screen.getByRole('button', { name: 'Send this authorized application' }))
  expect(await screen.findByText('Accepted by the email provider. Inbox delivery is not confirmed.')).toBeVisible()
  expect(apiClient.post).toHaveBeenLastCalledWith('/jobs/applications/7/send-authorizations/authorization-1/dispatch/', {})
  expect(screen.queryByRole('button', { name: 'Send this authorized application' })).not.toBeInTheDocument()
})

it('does not automatically repeat lost authorization and reconciles using its exact request key', async () => {
  await open()
  apiClient.post.mockRejectedValueOnce(new Error('offline'))
  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.click(screen.getByRole('button', { name: 'Record authorization (does not send)' }))
  await screen.findByRole('alert')
  const key = apiClient.post.mock.calls[0][1].request_key
  expect(screen.getByRole('checkbox')).not.toBeChecked()
  expect(screen.getByRole('button', { name: 'Record authorization (does not send)' })).toBeDisabled()
  apiClient.get.mockResolvedValueOnce({ data: record })
  fireEvent.click(button())
  await screen.findByText('Authorized; no dispatch recorded.')
  expect(apiClient.get).toHaveBeenLastCalledWith('/jobs/applications/7/send-authorizations/', { params: { request_key: key } })
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})

it('reconciles a missing request key by read-only history and never repeats the mutation', async () => {
  await open()
  apiClient.post.mockRejectedValueOnce(new Error('offline'))
  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.click(screen.getByRole('button', { name: 'Record authorization (does not send)' }))
  await screen.findByRole('alert')
  apiClient.get.mockRejectedValueOnce({ response: { status: 404 } }).mockResolvedValueOnce({ data: { results: [record] } })
  fireEvent.click(button())
  await screen.findByText('Authorized; no dispatch recorded.')
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})

it('single-flights rapid authorization clicks while a reply is pending', async () => {
  await open()
  let resolve
  apiClient.post.mockReturnValueOnce(new Promise((done) => { resolve = done }))
  fireEvent.click(screen.getByRole('checkbox'))
  const action = screen.getByRole('button', { name: 'Record authorization (does not send)' })
  fireEvent.click(action); fireEvent.click(action)
  expect(apiClient.post).toHaveBeenCalledTimes(1)
  await act(async () => { resolve({ data: record }) })
  expect(await screen.findByText('Authorized; no dispatch recorded.')).toBeVisible()
})

it('withdraws explicitly and requires a new plan review before another authorization', async () => {
  await open(); await authorize()
  apiClient.post.mockResolvedValueOnce({ data: { ...record, state: 'withdrawn' } })
  fireEvent.click(screen.getByRole('button', { name: 'Withdraw authorization' }))
  await waitFor(() => expect(screen.queryByText('Exact saved email <literal>')).not.toBeInTheDocument())
  expect(apiClient.post).toHaveBeenLastCalledWith('/jobs/applications/7/send-authorizations/authorization-1/withdraw/', {})
  apiClient.get.mockResolvedValueOnce({ data: { ...record, state: 'withdrawn' } }).mockResolvedValueOnce({ data: preview })
  fireEvent.click(button())
  expect(await screen.findByRole('checkbox')).not.toBeChecked()
})

it('unknown and pending receipts block sending and never claim inbox delivery or offer retries', async () => {
  apiClient.get.mockResolvedValueOnce({ data: { results: [{ ...record, state: 'dispatch_started', attempt: { id: 'attempt-1', state: 'unknown' } }] } })
  await open()
  expect(screen.getByText('Delivery outcome unknown. Sending is blocked pending operator reconciliation.')).toBeVisible()
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Review one manual retry' })).not.toBeInTheDocument()
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('a definite failure requires a new reviewed plan and unchecked permission for the one retry', async () => {
  apiClient.get.mockResolvedValueOnce({ data: { results: [{ ...record, state: 'dispatch_started', attempt: { id: 'attempt-1', state: 'definite_failure' } }] } })
  await open()
  apiClient.get.mockResolvedValueOnce({ data: { ...preview, plan: { ...plan, retry_of: 'attempt-1' } } })
  fireEvent.click(screen.getByRole('button', { name: 'Review one manual retry' }))
  expect(await screen.findByRole('checkbox')).not.toBeChecked()
  expect(apiClient.get).toHaveBeenLastCalledWith('/jobs/applications/7/send-plan/', { params: { retry_of: 'attempt-1' } })
  await authorize()
  expect(apiClient.post.mock.calls[0][1].retry_of).toBe('attempt-1')
})

it('a failed retry never offers a retry chain', async () => {
  apiClient.get.mockResolvedValueOnce({ data: { results: [{ ...record, plan: { ...plan, retry_of: 'initial-attempt' },
    state: 'dispatch_started', attempt: { id: 'retry-attempt', state: 'definite_failure' } }] } })
  await open()
  expect(screen.queryByRole('button', { name: 'Review one manual retry' })).not.toBeInTheDocument()
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
})

it('revision changes discard pending review, checkbox and delayed responses', async () => {
  const page = render(view())
  fireEvent.click(button())
  await screen.findByRole('checkbox')
  fireEvent.click(screen.getByRole('checkbox'))
  page.rerender(view({ packageId: 'package-2' }))
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  let resolve
  apiClient.get.mockReturnValueOnce(new Promise((done) => { resolve = done }))
  fireEvent.click(button())
  page.rerender(view({ packageId: 'package-3' }))
  await act(async () => { resolve({ data: { results: [record] } }) })
  expect(screen.queryByText('Exact saved email <literal>')).not.toBeInTheDocument()
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('lost dispatch replies reconcile by GET without a second send action', async () => {
  apiClient.post.mockResolvedValueOnce({ data: { ...record, dispatch_enabled: true } })
  await open(); await authorize()
  apiClient.post.mockRejectedValueOnce(new Error('offline'))
  fireEvent.click(screen.getByRole('button', { name: 'Send this authorized application' }))
  await screen.findByRole('alert')
  expect(screen.getByRole('button', { name: 'Send this authorized application' })).toBeDisabled()
  apiClient.get.mockResolvedValueOnce({ data: { ...record, state: 'dispatch_started', attempt: { id: 'attempt-1', state: 'reserved' } } })
  fireEvent.click(button())
  expect(await screen.findByText('Sending or outcome pending. Check the receipt; do not send again.')).toBeVisible()
  expect(apiClient.post).toHaveBeenCalledTimes(2)
})

it('only exposes email authorization after approval of the latest saved email package', async () => {
  const review = { revision: 1, approval: null, is_latest: true, approvable: false,
    job_context: { application_method: 'email', title: 'Test', company_name: 'Company' },
    previews: { cv: [], 'cover-letter': [] } }
  apiClient.get.mockResolvedValueOnce({ data: review })
  const page = render(<ApplicationPackageReview applicationId={7} packageId="package-1" revision={1} />)
  fireEvent.click(screen.getByRole('button', { name: 'Review saved package revision 1' }))
  await screen.findByText('Saved package revision 1')
  expect(screen.queryByRole('region', { name: 'Application email authorization' })).not.toBeInTheDocument()
  apiClient.get.mockResolvedValueOnce({ data: { ...review, approval: { policy_version: 'application-documents-v1' } } })
  fireEvent.click(screen.getByRole('button', { name: 'Review saved package revision 1' }))
  expect(await screen.findByRole('region', { name: 'Application email authorization' })).toBeVisible()
  page.rerender(<ApplicationPackageReview applicationId={7} packageId="package-1" revision={1} disabled />)
  expect(screen.queryByRole('region', { name: 'Application email authorization' })).not.toBeInTheDocument()
})
