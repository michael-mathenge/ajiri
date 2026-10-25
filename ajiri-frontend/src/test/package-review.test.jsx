import { beforeEach, expect, it, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor } from './test-utils'
import { MemoryRouter } from 'react-router-dom'
import apiClient from '../api/client'
import ApplicationPackageReview from '../components/ApplicationPackageReview'
import ApplicationPackageEditor from '../components/ApplicationPackageEditor'

vi.mock('../api/client', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
const statement =
  'I reviewed these saved documents. This does not authorize sending.'
const review = {
  id: 'package-1',
  revision: 1,
  cv_version: 'cv1',
  content_sha256: 'a'.repeat(64),
  job_context: {
    title: 'Saved engineer',
    company_name: 'Example',
    description: 'Saved job context',
    requirements: '',
    application_method: 'external_link',
  },
  previews: {
    cv: [
      { style: 'Title', text: 'Test Applicant' },
      { style: 'Normal', text: '<script>literal text</script>' },
    ],
    'cover-letter': [{ style: 'Normal', text: 'Exact saved letter' }],
  },
  approval: null,
  is_latest: true,
  approvable: true,
  approval_statement: statement,
}
beforeEach(() => {
  vi.resetAllMocks()
  apiClient.get.mockResolvedValue({ data: review })
  apiClient.post.mockResolvedValue({
    data: {
      approval: {
        policy_version: 'application-documents-v1',
        content_sha256: review.content_sha256,
      },
    },
  })
})
const view = (props = {}) => (
  <ApplicationPackageReview
    applicationId={7}
    packageId="package-1"
    revision={1}
    disabled={false}
    {...props}
  />
)
const open = async () => {
  render(view())
  fireEvent.click(
    screen.getByRole('button', { name: 'Review saved package revision 1' })
  )
  await screen.findByText('Exact saved letter')
}

it('previews literal stored text and requires an explicit unchecked document-only approval', async () => {
  await open()
  expect(screen.getByText('<script>literal text</script>')).toBeVisible()
  expect(screen.getByRole('checkbox')).not.toBeChecked()
  expect(
    screen.getByRole('button', { name: 'Approve saved documents' })
  ).toBeDisabled()
  expect(
    screen.getByRole('button', { name: 'Download saved package CV' })
  ).toBeVisible()
  expect(apiClient.post).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.click(
    screen.getByRole('button', { name: 'Approve saved documents' })
  )
  expect(await screen.findByRole('status')).toHaveTextContent(
    'Document approval recorded for revision 1'
  )
  expect(apiClient.post).toHaveBeenCalledExactlyOnceWith(
    '/jobs/applications/7/packages/package-1/approve/',
    {
      expected_revision: 1,
      content_sha256: review.content_sha256,
      approval: true,
    }
  )
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  expect(
    screen.queryByRole('button', { name: /Send application/ })
  ).not.toBeInTheDocument()
})

it('working edits clear the preview and checkbox instead of carrying approval forward', async () => {
  const page = render(view())
  fireEvent.click(
    screen.getByRole('button', { name: 'Review saved package revision 1' })
  )
  await screen.findByText('Exact saved letter')
  fireEvent.click(screen.getByRole('checkbox'))
  page.rerender(view({ disabled: true }))
  expect(screen.queryByText('Exact saved letter')).not.toBeInTheDocument()
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  page.rerender(view())
  fireEvent.click(
    screen.getByRole('button', { name: 'Review saved package revision 1' })
  )
  expect(await screen.findByRole('checkbox')).not.toBeChecked()
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('ignores a delayed response after switching package revisions', async () => {
  let resolve
  apiClient.get.mockReturnValueOnce(
    new Promise((done) => {
      resolve = done
    })
  )
  const page = render(view())
  fireEvent.click(
    screen.getByRole('button', { name: 'Review saved package revision 1' })
  )
  page.rerender(view({ packageId: 'package-2', revision: 2 }))
  await act(async () => {
    resolve({ data: review })
  })
  expect(screen.queryByText('Exact saved letter')).not.toBeInTheDocument()
  expect(
    screen.getByRole('button', { name: 'Review saved package revision 2' })
  ).toBeEnabled()
})

it('reconciles an uncertain approval by GET without automatically sending another POST', async () => {
  await open()
  apiClient.post.mockRejectedValueOnce(new Error('offline'))
  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.click(
    screen.getByRole('button', { name: 'Approve saved documents' })
  )
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Approval could not be confirmed'
  )
  expect(
    screen.getByRole('button', { name: 'Approve saved documents' })
  ).toBeDisabled()
  apiClient.get.mockResolvedValue({
    data: {
      ...review,
      approval: { policy_version: 'application-documents-v1' },
    },
  })
  fireEvent.click(
    screen.getByRole('button', { name: 'Review saved package revision 1' })
  )
  expect(await screen.findByRole('status')).toHaveTextContent(
    'Document approval recorded'
  )
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})

it('stale rejection requires a fresh review and does not retry or erase the saved package', async () => {
  await open()
  apiClient.post.mockRejectedValue({
    response: { status: 409, data: { detail: 'A newer revision exists.' } },
  })
  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.click(
    screen.getByRole('button', { name: 'Approve saved documents' })
  )
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'A newer revision exists.'
  )
  expect(screen.getByRole('checkbox')).not.toBeChecked()
  expect(
    screen.getByRole('button', { name: 'Approve saved documents' })
  ).toBeDisabled()
  expect(screen.getByText('Exact saved letter')).toBeVisible()
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})

it('labels historical approval without offering a new approval or send action', async () => {
  apiClient.get.mockResolvedValue({
    data: {
      ...review,
      is_latest: false,
      approvable: false,
      approval: { policy_version: 'application-documents-v1' },
    },
  })
  await open()
  expect(screen.getByRole('status')).toHaveTextContent(
    'this approval is historical'
  )
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('places separate email permission before long approved document previews without fetching or authorizing', async () => {
  apiClient.get.mockResolvedValue({
    data: {
      ...review,
      approval: { policy_version: 'application-documents-v1' },
      job_context: { ...review.job_context, application_method: 'email' },
    },
  })
  await open()
  const next = screen.getByRole('heading', {
    name: 'Next: review your email plan',
  })
  const savedCV = screen.getByRole('heading', { name: 'Saved CV' })
  expect(
    next.compareDocumentPosition(savedCV) & Node.DOCUMENT_POSITION_FOLLOWING
  ).toBeTruthy()
  expect(
    screen.getByRole('button', {
      name: 'Review email plan / check authorization status',
    })
  ).toBeEnabled()
  expect(apiClient.get).toHaveBeenCalledExactlyOnceWith(
    '/jobs/applications/7/packages/package-1/'
  )
  expect(apiClient.post).not.toHaveBeenCalled()
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  fireEvent.click(
    screen.getByRole('button', { name: 'Go to email permission controls' })
  )
  expect(next).toHaveFocus()
})

it('moves focus to the separate permission step after personal document approval without authorizing or sending', async () => {
  apiClient.get.mockResolvedValue({
    data: {
      ...review,
      job_context: { ...review.job_context, application_method: 'email' },
    },
  })
  await open()
  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.click(
    screen.getByRole('button', { name: 'Approve saved documents' })
  )
  await waitFor(() =>
    expect(
      screen.getByRole('heading', { name: 'Next: review your email plan' })
    ).toHaveFocus()
  )
  expect(apiClient.post).toHaveBeenCalledTimes(1)
  expect(apiClient.post.mock.calls[0][0]).toBe(
    '/jobs/applications/7/packages/package-1/approve/'
  )
  expect(apiClient.get).toHaveBeenCalledTimes(1)
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
})

it('never offers the next permission step for a historical email revision', async () => {
  apiClient.get.mockResolvedValue({
    data: {
      ...review,
      is_latest: false,
      approvable: false,
      approval: { policy_version: 'application-documents-v1' },
      job_context: { ...review.job_context, application_method: 'email' },
    },
  })
  await open()
  expect(
    screen.queryByRole('heading', { name: 'Next: review your email plan' })
  ).not.toBeInTheDocument()
  expect(
    screen.queryByRole('button', {
      name: 'Review email plan / check authorization status',
    })
  ).not.toBeInTheDocument()
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('does not expose preview, downloads or approval when stored-file verification fails', async () => {
  apiClient.get.mockRejectedValue({
    response: { status: 503, data: { detail: 'Saved package unavailable.' } },
  })
  render(view())
  fireEvent.click(
    screen.getByRole('button', { name: 'Review saved package revision 1' })
  )
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Saved package unavailable'
  )
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  expect(
    screen.queryByRole('button', { name: 'Download saved package CV' })
  ).not.toBeInTheDocument()
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('reviews the explicitly saved package from the editor and clears approval on a CV edit', async () => {
  apiClient.get.mockImplementation((url) =>
    Promise.resolve({
      data: url.includes('cv-versions')
        ? {
            versions: [
              { id: 'cv1', revision: 1 },
              { id: 'cv2', revision: 2 },
            ],
          }
        : url.endsWith('package-1/')
          ? review
          : {
              results: [
                {
                  ...review,
                  letter_text: 'Exact saved letter',
                  email_subject: '',
                  email_body: '',
                },
              ],
              count: 1,
              latest_revision: 1,
              context_sha256: 'abc',
              editable: true,
              job_context: review.job_context,
            },
    })
  )
  render(
    <MemoryRouter>
      <ApplicationPackageEditor applicationId={7} />
    </MemoryRouter>
  )
  fireEvent.click(
    screen.getByRole('button', { name: 'Choose CV and edit cover letter' })
  )
  fireEvent.click(
    await screen.findByRole('button', {
      name: 'Review saved package revision 1',
    })
  )
  await screen.findByText('Exact saved letter')
  fireEvent.click(screen.getByRole('checkbox'))
  fireEvent.change(screen.getByLabelText('Approved CV version'), {
    target: { value: 'cv2' },
  })
  await waitFor(() =>
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  )
  expect(apiClient.post).not.toHaveBeenCalled()
})
