import { beforeEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import apiClient from '../api/client'
import Register from '../pages/Register'
import Applications, { ApplicationRow } from '../pages/Applications'
import Notifications from '../pages/Notifications'

vi.mock('../api/client', () => ({
  default: { get: vi.fn(), post: vi.fn() },
  mediaUrl: (url) => url,
}))
beforeEach(() => vi.resetAllMocks())
const renderPage = (page) => render(<MemoryRouter>{page}</MemoryRouter>)
const fillRegister = () => {
  fireEvent.change(screen.getByLabelText('Full name'), {
    target: { value: 'Test User' },
  })
  fireEvent.change(screen.getByLabelText('Email'), {
    target: { value: 'test@example.com' },
  })
  fireEvent.change(screen.getByLabelText('Password'), {
    target: { value: 'test-password' },
  })
}
const app = {
  id: 1,
  job: 1,
  job_title: 'Developer',
  company_name: 'Example',
  status: 'ready_for_review',
  application_method: 'email',
  application_email: 'jobs@example.com',
  email_subject: 'Application',
  email_body: 'Dear team',
  generated_cv: '/media/cv.docx',
  generated_cover_letter: '/media/letter.docx',
  employer_url: 'https://example.com/job',
}

describe('Register', () => {
  it('shows all field errors and complete messages', async () => {
    apiClient.post.mockRejectedValue({
      response: {
        data: {
          email: ['Already registered.', 'Try another email.'],
          password: ['Too short.', 'Too common.', 'Entirely numeric.'],
          detail: 'Please correct your entries.',
        },
      },
    })
    renderPage(<Register />)
    fillRegister()
    fireEvent.click(screen.getByRole('button', { name: 'Register' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Already registered. Try another email.'
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Too short.')
    expect(screen.getByRole('alert')).toHaveTextContent('Too common.')
    expect(screen.getByRole('alert')).toHaveTextContent('Entirely numeric.')
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Please correct your entries.'
    )
    expect(screen.getByLabelText('Email')).toHaveAttribute(
      'aria-invalid',
      'true'
    )
    expect(screen.getByRole('alert')).toHaveClass('form-error-summary')
    expect(screen.getByLabelText('Password')).toHaveAttribute('aria-describedby', 'register-password-error')
    expect(document.getElementById('register-password-error')).toHaveTextContent('Too short. Too common. Entirely numeric.')
  })
  it('explains rate limits without retrying registration', async () => {
    apiClient.post.mockRejectedValue({ response: { status: 429, headers: { 'retry-after': '60' }, data: {} } })
    renderPage(<Register />)
    fillRegister()
    fireEvent.click(screen.getByRole('button', { name: 'Register' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('wait 60 seconds')
    expect(apiClient.post).toHaveBeenCalledTimes(1)
  })
  it('navigates to login after successful registration', async () => {
    apiClient.post.mockResolvedValue({ data: {} })
    render(
      <MemoryRouter initialEntries={['/register']}>
        <Routes>
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<h1>Login destination</h1>} />
        </Routes>
      </MemoryRouter>
    )
    fillRegister()
    fireEvent.click(screen.getByRole('button', { name: 'Register' }))
    expect(await screen.findByText('Login destination')).toBeVisible()
  })
})

describe('Applications', () => {
  it('keeps managed email sending unavailable and preserves original downloads', async () => {
    apiClient.get.mockResolvedValue({ data: { results: [app], count: 1 } })
    renderPage(<Applications />)
    await screen.findByText('Developer, Example')
    fireEvent.click(screen.getByText('Review application'))
    expect(screen.getByText(/Managed application sending is awaiting activation/)).toBeVisible()
    expect(screen.queryByRole('button', { name: 'Send application' })).not.toBeInTheDocument()
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Download CV' })).toBeVisible()
    expect(apiClient.post).not.toHaveBeenCalled()
  })
  it('requires opening the employer link and confirming submission', async () => {
    const onUpdate = vi.fn()
    apiClient.post.mockResolvedValue({ data: { ...app, status: 'sent' } })
    renderPage(
      <ApplicationRow
        application={{ ...app, application_method: 'external_link' }}
        onUpdate={onUpdate}
      />
    )
    fireEvent.click(screen.getByText('Review application'))
    expect(screen.getByRole('checkbox')).toBeDisabled()
    const link = screen.getByRole('link', { name: /Open employer listing/ })
    expect(link).toHaveAttribute('href', 'https://example.com/job')
    fireEvent.click(link)
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(
      screen.getByRole('button', { name: 'Confirm external submission' })
    )
    await waitFor(() => expect(onUpdate).toHaveBeenCalled())
  })
  it('dismisses only after confirmation', async () => {
    const onUpdate = vi.fn()
    apiClient.post.mockResolvedValue({ data: { ...app, status: 'dismissed' } })
    renderPage(<ApplicationRow application={app} onUpdate={onUpdate} />)
    fireEvent.click(screen.getByRole('button', { name: 'Dismiss application' }))
    expect(apiClient.post).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Confirm dismissal' }))
    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith(
        '/jobs/applications/1/dismiss/'
      )
    )
  })
  it('keeps a rejected send visible with the server error', async () => {
    apiClient.post.mockRejectedValue({
      response: {
        data: { detail: 'Cannot send an application with status sent.' },
      },
    })
    renderPage(<ApplicationRow application={{ ...app, application_method: 'external_link' }} onUpdate={vi.fn()} />)
    fireEvent.click(screen.getByText('Review application'))
    fireEvent.click(screen.getByRole('link', { name: /Open employer listing/ }))
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByRole('button', { name: 'Confirm external submission' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot send')
    expect(screen.getByText('Developer, Example')).toBeVisible()
  })
})

describe('Notifications', () => {
  it('marks an unread notification read', async () => {
    const notification = {
      id: 1,
      job_id: 1,
      job_title: 'Developer',
      company_name: 'Example',
      match_score: 100,
      is_read: false,
    }
    apiClient.get.mockResolvedValue({
      data: { results: [notification], count: 1 },
    })
    apiClient.post.mockResolvedValue({
      data: { ...notification, is_read: true },
    })
    renderPage(<Notifications />)
    expect(await screen.findByText('Unread')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Mark as read' }))
    expect(await screen.findByText('Read')).toBeVisible()
    await waitFor(() =>
      expect(
        screen.getByText('Developer, Example').closest('.row')
      ).toHaveFocus()
    )
    expect(
      screen.queryByRole('button', { name: 'Mark as read' })
    ).not.toBeInTheDocument()
  })
  it('shows an empty state', async () => {
    apiClient.get.mockResolvedValue({ data: { results: [], count: 0 } })
    renderPage(<Notifications />)
    expect(await screen.findByText('You’re all caught up')).toBeVisible()
  })
})

it('restores a dismissed application only after an explicit click', async () => {
  const onUpdate = vi.fn()
  const restored = { ...app, status: 'ready_for_review' }
  apiClient.post.mockResolvedValue({ data: restored })
  renderPage(<ApplicationRow application={{ ...app, status: 'dismissed' }} onUpdate={onUpdate} />)
  expect(apiClient.post).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: 'Restore for review' }))
  await waitFor(() => expect(onUpdate).toHaveBeenCalledWith(restored))
  expect(apiClient.post).toHaveBeenCalledExactlyOnceWith('/jobs/applications/1/restore/')
})
