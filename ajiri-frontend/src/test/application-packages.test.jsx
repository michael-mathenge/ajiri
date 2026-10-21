import { beforeEach, afterEach, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from './test-utils'
import { MemoryRouter } from 'react-router-dom'
import apiClient from '../api/client'
import ApplicationPackageEditor from '../components/ApplicationPackageEditor'

vi.mock('../api/client', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
const job = {
  title: 'Developer',
  company_name: 'Example',
  description: '<script>literal</script>',
  requirements: 'Python',
  application_method: 'email',
}
const listing = {
  results: [],
  count: 0,
  next: null,
  previous: null,
  latest_revision: 0,
  job_context: job,
  context_sha256: 'abc',
  editable: true,
}
const row = {
  id: 'saved',
  revision: 1,
  cv_version: 'cv1',
  letter_text: 'Saved letter',
  email_subject: 'Subject',
  email_body: 'Body',
}
beforeEach(() => {
  vi.resetAllMocks()
  apiClient.get.mockImplementation((url) =>
    Promise.resolve({
      data: url.includes('cv-versions')
        ? {
            versions: [
              { id: 'cv1', revision: 1 },
              { id: 'cv2', revision: 2 },
            ],
          }
        : listing,
    })
  )
})
afterEach(() => vi.restoreAllMocks())
const open = async () => {
  render(
    <MemoryRouter>
      <ApplicationPackageEditor applicationId={7} />
    </MemoryRouter>
  )
  fireEvent.click(
    screen.getByRole('button', { name: 'Choose CV and edit cover letter' })
  )
  await screen.findByLabelText('Approved CV version')
}
const edit = () => {
  fireEvent.change(screen.getByLabelText('Approved CV version'), {
    target: { value: 'cv1' },
  })
  fireEvent.change(screen.getByLabelText('Working cover letter'), {
    target: { value: 'Exact edited letter' },
  })
}

it('requires explicit CV selection, shows literal job context and saves only on request', async () => {
  await open()
  expect(screen.getByLabelText('Approved CV version')).toHaveValue('')
  expect(screen.getByText('<script>literal</script>')).toBeVisible()
  expect(
    screen.getByRole('button', { name: 'Save new package revision' })
  ).toBeDisabled()
  edit()
  expect(apiClient.post).not.toHaveBeenCalled()
  apiClient.post.mockResolvedValue({ data: row })
  fireEvent.click(
    screen.getByRole('button', { name: 'Save new package revision' })
  )
  expect(await screen.findByRole('status')).toHaveTextContent(
    'Saved package revision 1'
  )
  expect(apiClient.post).toHaveBeenCalledExactlyOnceWith(
    '/jobs/applications/7/packages/',
    {
      cv_version: 'cv1',
      expected_revision: 0,
      context_sha256: 'abc',
      letter_text: 'Exact edited letter',
      email_subject: '',
      email_body: '',
    }
  )
  expect(
    screen.queryByRole('button', { name: /Send application|Approve documents/ })
  ).not.toBeInTheDocument()
})

it('drafts from the chosen approved CV and highlights missing information without saving', async () => {
  await open()
  fireEvent.change(screen.getByLabelText('Approved CV version'), {
    target: { value: 'cv2' },
  })
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  apiClient.post.mockResolvedValue({
    data: {
      letter_text: 'Neutral draft',
      job_context: job,
      context_sha256: 'fresh',
      missing_information: ['CV summary'],
    },
  })
  fireEvent.click(
    screen.getByRole('button', { name: 'Draft letter from selected CV' })
  )
  await waitFor(() =>
    expect(screen.getByLabelText('Working cover letter')).toHaveValue(
      'Neutral draft'
    )
  )
  expect(screen.getByRole('status')).toHaveTextContent('Missing: CV summary')
  expect(apiClient.post).toHaveBeenCalledExactlyOnceWith(
    '/jobs/applications/7/package-draft/',
    { cv_version: 'cv2' }
  )
})

it('loads an older job-specific letter as a working copy and saves a fresh latest revision', async () => {
  apiClient.get.mockImplementation((url) =>
    Promise.resolve({
      data: url.includes('cv-versions')
        ? { versions: [{ id: 'cv1', revision: 1 }] }
        : {
            ...listing,
            count: 2,
            latest_revision: 2,
            results: [
              { ...row, id: 'newer', revision: 2, letter_text: 'Newer' },
              row,
            ],
          },
    })
  )
  await open()
  fireEvent.change(
    screen.getByLabelText('Saved cover-letter revision for this job'),
    { target: { value: 'saved' } }
  )
  expect(screen.getByLabelText('Working cover letter')).toHaveValue(
    'Saved letter'
  )
  apiClient.post.mockResolvedValue({ data: { ...row, revision: 3 } })
  fireEvent.click(
    screen.getByRole('button', { name: 'Save new package revision' })
  )
  await waitFor(() =>
    expect(apiClient.post).toHaveBeenCalledWith(
      '/jobs/applications/7/packages/',
      expect.objectContaining({
        expected_revision: 2,
        letter_text: 'Saved letter',
      })
    )
  )
})

it('does not retry uncertain saves and requires reload before another mutation', async () => {
  await open()
  edit()
  apiClient.post.mockRejectedValue(new Error('offline'))
  fireEvent.click(
    screen.getByRole('button', { name: 'Save new package revision' })
  )
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Save could not be confirmed'
  )
  expect(
    screen.getByRole('button', { name: 'Save new package revision' })
  ).toBeDisabled()
  expect(apiClient.post).toHaveBeenCalledTimes(1)
  vi.spyOn(window, 'confirm').mockReturnValue(false)
  fireEvent.click(
    screen.getByRole('button', { name: 'Reload saved revisions' })
  )
  expect(apiClient.get).toHaveBeenCalledTimes(2)
  expect(screen.getByLabelText('Working cover letter')).toHaveValue(
    'Exact edited letter'
  )
  window.confirm.mockReturnValue(true)
  fireEvent.click(
    screen.getByRole('button', { name: 'Reload saved revisions' })
  )
  await waitFor(() =>
    expect(screen.getByLabelText('Working cover letter')).toHaveValue('')
  )
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})

it('preserves edits and renders every validation message without an automatic retry', async () => {
  await open()
  edit()
  apiClient.post.mockRejectedValue({
    response: {
      status: 400,
      data: { letter_text: ['Shorten this.', 'Remove unsupported text.'] },
    },
  })
  fireEvent.click(
    screen.getByRole('button', { name: 'Save new package revision' })
  )
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Shorten this. Remove unsupported text.'
  )
  expect(screen.getByLabelText('Working cover letter')).toHaveAttribute(
    'aria-invalid',
    'true'
  )
  expect(screen.getByLabelText('Working cover letter')).toHaveValue(
    'Exact edited letter'
  )
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})

it('shows read-only state and guards unsaved browser exits', async () => {
  await open()
  edit()
  const event = new Event('beforeunload', { cancelable: true })
  window.dispatchEvent(event)
  expect(event.defaultPrevented).toBe(true)
})

it('does not expose editing controls for blocked applications', async () => {
  apiClient.get.mockImplementation((url) =>
    Promise.resolve({
      data: url.includes('cv-versions')
        ? { versions: [] }
        : { ...listing, editable: false },
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
  expect(
    await screen.findByText(
      'This application cannot be edited in its current state.'
    )
  ).toBeVisible()
  expect(
    screen.queryByLabelText('Working cover letter')
  ).not.toBeInTheDocument()
})
