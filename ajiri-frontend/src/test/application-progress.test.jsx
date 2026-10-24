import { beforeEach, expect, it, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from './test-utils'
import { MemoryRouter } from 'react-router-dom'
import ApplicationProgress from '../components/ApplicationProgress'
import Applications from '../pages/Applications'
import { useApiInvalidation } from '../hooks/useApiQuery'
import apiClient from '../api/client'

vi.mock('../api/client', () => ({
  default: { get: vi.fn(), patch: vi.fn(), post: vi.fn() },
}))
vi.mock('../components/ApplicationPackageEditor', () => ({
  default: () => <p>Document review</p>,
}))
beforeEach(() => vi.resetAllMocks())
const app = {
  id: 8,
  progress_stage: 'not_reported',
  progress_note: '',
  progress_revision: 0,
}

it('keeps user reports separate and sends only a revision-checked private update', async () => {
  const update = vi.fn()
  apiClient.patch.mockResolvedValue({
    data: { ...app, progress_stage: 'interview', progress_revision: 1 },
  })
  render(<ApplicationProgress application={app} onUpdate={update} />)
  expect(screen.getByText(/not confirmation from an employer/)).toBeVisible()
  fireEvent.change(screen.getByLabelText('Your progress'), {
    target: { value: 'interview' },
  })
  fireEvent.change(screen.getByLabelText('Private note (optional)'), {
    target: { value: 'Synthetic note' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Save my update' }))
  await waitFor(() => expect(update).toHaveBeenCalled())
  expect(apiClient.patch).toHaveBeenCalledWith(
    '/jobs/applications/8/progress/',
    {
      stage: 'interview',
      note: 'Synthetic note',
      expected_revision: 0,
    }
  )
  expect(apiClient.post).not.toHaveBeenCalled()
  expect(screen.getByRole('status')).toHaveTextContent(
    'No application was sent'
  )
})

it('shows every validation message with accessible labels', async () => {
  apiClient.patch.mockRejectedValue({
    response: {
      status: 400,
      data: { note: ['Too long', 'Choose a stage'], stage: ['Invalid choice'] },
    },
  })
  render(<ApplicationProgress application={app} onUpdate={vi.fn()} />)
  fireEvent.click(screen.getByRole('button', { name: 'Save my update' }))
  await screen.findByText(/Too long/)
  expect(screen.getByRole('alert')).toHaveTextContent('Choose a stage')
  expect(screen.getByRole('alert')).toHaveTextContent('Invalid choice')
  expect(screen.getByLabelText('Private note (optional)')).toHaveAttribute(
    'aria-describedby',
    'progress-8-note-error'
  )
})

it('does not retry a revision conflict or claim success', async () => {
  apiClient.patch.mockRejectedValue({
    response: { status: 409, data: { detail: 'Reload before saving again.' } },
  })
  const update = vi.fn()
  render(
    <ApplicationProgress
      application={{ ...app, progress_revision: 4 }}
      onUpdate={update}
    />
  )
  fireEvent.click(screen.getByRole('button', { name: 'Save my update' }))
  expect(await screen.findByText(/Reload before saving again/)).toBeVisible()
  expect(apiClient.patch).toHaveBeenCalledTimes(1)
  expect(update).not.toHaveBeenCalled()
  expect(screen.queryByRole('status')).not.toBeInTheDocument()
})

it('shows fresh receipt evidence after a progress save instead of retaining an old local row', async () => {
  let server = {
    ...app,
    status: 'ready_for_review',
    application_method: 'email',
    job_title: 'Synthetic role',
    company_name: 'Example',
  }
  apiClient.get.mockImplementation(async () => ({
    data: { count: 1, results: [server] },
  }))
  const saved = { ...server, progress_stage: 'interview', progress_revision: 1 }
  apiClient.patch.mockResolvedValue({ data: saved })
  function Harness() {
    const refresh = useApiInvalidation()
    return (
      <MemoryRouter>
        <Applications />
        <button onClick={refresh}>Refresh from server</button>
      </MemoryRouter>
    )
  }
  render(<Harness />)
  await screen.findByRole('heading', { name: 'Synthetic role, Example' })
  fireEvent.change(screen.getByLabelText('Your progress'), {
    target: { value: 'interview' },
  })
  fireEvent.click(
    screen.getByRole('button', { name: 'Save my update', hidden: true })
  )
  await waitFor(() =>
    expect(screen.getByLabelText('Your progress')).toHaveValue('interview')
  )
  server = {
    ...saved,
    status: 'sent',
    delivery_evidence: {
      kind: 'accepted',
      label: 'Email provider accepted; inbox delivery unconfirmed',
    },
  }
  fireEvent.click(screen.getByRole('button', { name: 'Refresh from server' }))
  expect(
    await screen.findByText(
      'Email provider accepted; inbox delivery unconfirmed'
    )
  ).toBeVisible()
  expect(screen.getByText('Provider accepted')).toBeVisible()
  expect(apiClient.post).not.toHaveBeenCalled()
})
