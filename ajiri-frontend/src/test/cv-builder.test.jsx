import { beforeEach, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from './test-utils'
import { MemoryRouter } from 'react-router-dom'
import CVBuilder, { CVEditor, CVPreview } from '../pages/CVBuilder'
import apiClient from '../api/client'
import { downloadFile } from '../lib/download'

vi.mock('../api/client', () => ({
  default: { get: vi.fn(), patch: vi.fn(), post: vi.fn() },
}))
vi.mock('../lib/download', () => ({ downloadFile: vi.fn() }))
const content = {
  schema_version: 1,
  contact: {
    name: 'Test Applicant',
    email: 'test@example.invalid',
    phone: '',
    location: '',
  },
  headline: '',
  summary: 'Test summary',
  skills: [],
  employment: [],
  education: [],
  certifications: [],
  projects: [],
}
const draft = {
  content,
  revision: 1,
  content_sha256: 'a'.repeat(64),
  preview: {
    name: 'Test Applicant',
    headline: '',
    contact: 'test@example.invalid',
    sections: [
      {
        title: 'Summary',
        entries: [{ heading: '', paragraphs: ['Test summary'], bullets: [] }],
      },
    ],
  },
  approval_id: null,
  versions: [],
}
const page = (ui = <CVEditor initial={structuredClone(draft)} />) =>
  render(<MemoryRouter>{ui}</MemoryRouter>)
beforeEach(() => vi.resetAllMocks())

it('starts explicitly and does not create a draft on GET', async () => {
  apiClient.get.mockResolvedValue({ data: { content: null } })
  apiClient.post.mockResolvedValue({ data: structuredClone(draft) })
  page(<CVBuilder />)
  const start = await screen.findByRole('button', { name: 'Start my CV' })
  expect(apiClient.post).not.toHaveBeenCalled()
  fireEvent.click(start)
  expect(await screen.findByLabelText('Full name')).toHaveValue(
    'Test Applicant'
  )
  expect(apiClient.post).toHaveBeenCalledWith('/profiles/me/cv-draft/', {})
})

it('previews saved content and requires explicit consent before approving and downloading', async () => {
  apiClient.post.mockResolvedValue({
    data: { approval_id: 'version-1', revision: 1 },
  })
  page()
  expect(screen.queryByRole('article')).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Save and preview CV' }))
  expect(await screen.findByRole('article')).toHaveTextContent('Test summary')
  expect(
    screen.getByRole('heading', { name: 'Review revision 1' })
  ).toHaveFocus()
  const approve = screen.getByRole('button', {
    name: 'Approve this CV version',
  })
  expect(approve).toBeDisabled()
  expect(apiClient.post).not.toHaveBeenCalled()
  fireEvent.click(
    screen.getByLabelText('I have reviewed this CV and approve this version.')
  )
  fireEvent.click(approve)
  fireEvent.click(
    await screen.findByRole('button', {
      name: 'Download approved CV (revision 1)',
    })
  )
  await waitFor(() =>
    expect(downloadFile).toHaveBeenCalledWith(
      '/profiles/me/cv-versions/version-1/download/',
      'Ajiri_CV.docx'
    )
  )
  expect(apiClient.post).toHaveBeenCalledWith(
    '/profiles/me/cv-draft/approve/',
    { expected_revision: 1, content_sha256: 'a'.repeat(64), approval: true }
  )
})

it('saves structured sections without inventing entries and resets approval after edits', async () => {
  apiClient.patch.mockImplementation((_, payload) =>
    Promise.resolve({
      data: {
        ...structuredClone(draft),
        content: payload.content,
        revision: 2,
      },
    })
  )
  page(
    <CVEditor
      initial={{ ...structuredClone(draft), approval_id: 'version-1' }}
    />
  )
  fireEvent.click(screen.getByRole('button', { name: 'Add work experience' }))
  fireEvent.change(screen.getByLabelText('Role (work experience 1)'), {
    target: { value: 'Engineer' },
  })
  fireEvent.change(screen.getByLabelText('Employer (work experience 1)'), {
    target: { value: 'Test Team' },
  })
  fireEvent.change(
    screen.getByLabelText('Achievements (one per line) (work experience 1)'),
    { target: { value: 'Built a tool.\nHelped a team.' } }
  )
  expect(screen.getByRole('status')).toHaveTextContent('Unsaved changes')
  expect(
    screen.queryByRole('button', { name: /Download approved CV/ })
  ).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Save and preview CV' }))
  await screen.findByText(
    'Revision 2 saved. Review the preview before approving.'
  )
  expect(apiClient.patch).toHaveBeenCalledWith(
    '/profiles/me/cv-draft/',
    expect.objectContaining({
      expected_revision: 1,
      content: expect.objectContaining({
        employment: [
          expect.objectContaining({
            title: 'Engineer',
            organisation: 'Test Team',
            achievements: ['Built a tool.', 'Helped a team.'],
          }),
        ],
        education: [],
      }),
    })
  )
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('keeps edits on conflict and prevents repeated stale saves', async () => {
  apiClient.patch.mockRejectedValue({
    response: { status: 409, data: { detail: 'The CV changed.' } },
  })
  page()
  fireEvent.change(screen.getByLabelText('Full name'), {
    target: { value: 'Unsaved Name' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Save and preview CV' }))
  expect(await screen.findByText(/Another change was saved/)).toBeVisible()
  expect(screen.getByLabelText('Full name')).toHaveValue('Unsaved Name')
  expect(
    screen.getByRole('button', { name: 'Save and preview CV' })
  ).toBeDisabled()
  expect(apiClient.patch).toHaveBeenCalledTimes(1)
})

it('renders every nested validation message and retains the draft', async () => {
  apiClient.patch.mockRejectedValue({
    response: {
      status: 400,
      data: {
        employment: [
          { title: ['Required.'], organisation: ['Enter an employer.'] },
        ],
      },
    },
  })
  page()
  fireEvent.change(screen.getByLabelText('Full name'), {
    target: { value: 'Retained Name' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Save and preview CV' }))
  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent('Work experience 1 — Role: Required.')
  expect(alert).toHaveTextContent(
    'Work experience 1 — Employer: Enter an employer.'
  )
  await waitFor(() =>
    expect(screen.getByLabelText('CV save errors')).toHaveFocus()
  )
  expect(screen.getByLabelText('Full name')).toHaveValue('Retained Name')
})

it('brings repeated save errors into view and identifies the exact optional entry', async () => {
  const scroll = vi.fn()
  const original = HTMLElement.prototype.scrollIntoView
  HTMLElement.prototype.scrollIntoView = scroll
  try {
    apiClient.patch.mockRejectedValue({
      response: {
        status: 400,
        data: {
          employment: [
            {},
            {
              title: ['This field may not be blank.'],
              organisation: ['This field may not be blank.'],
            },
          ],
          education: [{ institution: ['This field may not be blank.'] }],
        },
      },
    })
    page()
    fireEvent.change(screen.getByLabelText('Full name'), {
      target: { value: 'Retained Name' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save and preview CV' }))
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(
      'Work experience 2 — Role: This field may not be blank.'
    )
    expect(alert).toHaveTextContent(
      'Work experience 2 — Employer: This field may not be blank.'
    )
    expect(alert).toHaveTextContent(
      'Education 1 — Institution: This field may not be blank.'
    )
    await waitFor(() =>
      expect(screen.getByLabelText('CV save errors')).toHaveFocus()
    )
    expect(scroll).toHaveBeenCalledWith({ block: 'start', behavior: 'auto' })
    fireEvent.click(screen.getByRole('button', { name: 'Save and preview CV' }))
    await waitFor(() => expect(apiClient.patch).toHaveBeenCalledTimes(2))
    await waitFor(() =>
      expect(screen.getByLabelText('CV save errors')).toHaveFocus()
    )
    expect(screen.getByLabelText('Full name')).toHaveValue('Retained Name')
    expect(apiClient.post).not.toHaveBeenCalled()
  } finally {
    HTMLElement.prototype.scrollIntoView = original
  }
})

it('labels earlier versions separately and escapes preview text', () => {
  page(
    <CVEditor
      initial={{
        ...structuredClone(draft),
        revision: 2,
        versions: [{ id: 'old', revision: 1 }],
      }}
    />
  )
  expect(
    screen.getByRole('button', { name: 'Download earlier revision 1' })
  ).toBeVisible()
  const { container } = render(
    <CVPreview preview={{ ...draft.preview, name: '<script>bad()</script>' }} />
  )
  expect(within(container).getByText('<script>bad()</script>')).toBeVisible()
  expect(container.querySelector('script')).toBeNull()
})

it('adds and removes optional entries without requiring employment for a first CV', () => {
  page()
  fireEvent.click(screen.getByRole('button', { name: 'Add education' }))
  expect(screen.getByLabelText('Qualification (education 1)')).toBeVisible()
  fireEvent.click(screen.getByRole('button', { name: 'Remove education 1' }))
  expect(
    screen.queryByLabelText('Qualification (education 1)')
  ).not.toBeInTheDocument()
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('chooses readable months and typed years, clears dates and handles current employment', async () => {
  apiClient.patch.mockImplementation((_, payload) =>
    Promise.resolve({
      data: {
        ...structuredClone(draft),
        content: payload.content,
        revision: 2,
      },
    })
  )
  page()
  fireEvent.click(screen.getByRole('button', { name: 'Add work experience' }))
  fireEvent.change(screen.getByLabelText('Role (work experience 1)'), {
    target: { value: 'Developer' },
  })
  fireEvent.change(screen.getByLabelText('Employer (work experience 1)'), {
    target: { value: 'Test Team' },
  })
  const month = screen.getByLabelText('Start month (work experience 1) — month')
  expect(within(month).getByRole('option', { name: 'September' })).toHaveValue(
    '09'
  )
  fireEvent.change(month, { target: { value: '09' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save and preview CV' }))
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Choose both a month'
  )
  expect(apiClient.patch).not.toHaveBeenCalled() // A partial date cannot be silently saved as empty.
  fireEvent.change(
    screen.getByLabelText('Start month (work experience 1) — year'),
    { target: { value: '2018' } }
  )
  fireEvent.change(
    screen.getByLabelText('End month (work experience 1) — month'),
    { target: { value: '06' } }
  )
  fireEvent.change(
    screen.getByLabelText('End month (work experience 1) — year'),
    { target: { value: '2020' } }
  )
  fireEvent.click(
    screen.getByLabelText('I currently work here (work experience 1)')
  )
  expect(
    screen.getByLabelText('End month (work experience 1) — year')
  ).toBeDisabled()
  fireEvent.click(screen.getByRole('button', { name: 'Save and preview CV' }))
  await screen.findByText(
    'Revision 2 saved. Review the preview before approving.'
  )
  expect(apiClient.patch).toHaveBeenCalledWith(
    '/profiles/me/cv-draft/',
    expect.objectContaining({
      content: expect.objectContaining({
        employment: [
          expect.objectContaining({ start: '2018-09', end: '', current: true }),
        ],
      }),
    })
  )
  fireEvent.click(
    screen.getByRole('button', {
      name: 'Clear start month (work experience 1)',
    })
  )
  expect(month).toHaveValue('')
  expect(
    screen.getByLabelText('Start month (work experience 1) — year')
  ).toHaveValue(null)
})

it('loads saved certificate months and preserves expiry while editing the issue year', () => {
  const initial = structuredClone(draft)
  initial.content.certifications = [
    {
      id: 'cert-one',
      name: 'Test certificate',
      issuer: 'Test institute',
      issued: '2024-02',
      expiry: '2028-11',
      description: '',
    },
  ]
  page(<CVEditor initial={initial} />)
  expect(
    screen.getByLabelText('Issued month (certifications 1) — month')
  ).toHaveValue('02')
  expect(
    screen.getByLabelText('Issued month (certifications 1) — year')
  ).toHaveValue(2024)
  fireEvent.change(
    screen.getByLabelText('Issued month (certifications 1) — year'),
    { target: { value: '2025' } }
  )
  expect(
    screen.getByLabelText('Expiry month (certifications 1) — month')
  ).toHaveValue('11')
  expect(
    screen.getByLabelText('Expiry month (certifications 1) — year')
  ).toHaveValue(2028)
})

it('warns before leaving with unsaved changes and retains edits if cancelled', () => {
  const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
  page(
    <>
      <CVEditor initial={structuredClone(draft)} />
      <a href="/profile">Leave editor</a>
    </>
  )
  fireEvent.change(screen.getByLabelText('Full name'), {
    target: { value: 'Unsaved Name' },
  })
  fireEvent.click(screen.getByRole('link', { name: 'Leave editor' }))
  expect(confirm).toHaveBeenCalledWith(
    'You have unsaved CV changes. Leave without saving?'
  )
  expect(screen.getByLabelText('Full name')).toHaveValue('Unsaved Name')
  const event = new Event('beforeunload', { cancelable: true })
  window.dispatchEvent(event)
  expect(event.defaultPrevented).toBe(true)
  confirm.mockRestore()
})
