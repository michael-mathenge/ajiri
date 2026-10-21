import { beforeEach, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import apiClient from '../api/client'
import Profile, { ProfileEditor } from '../pages/Profile'
import { downloadFile } from '../lib/download'
import { validateCV, MAX_CV_BYTES } from '../lib/cv'
vi.mock('../api/client', () => ({ default: { get: vi.fn(), patch: vi.fn() } }))
const profile = {
  email: 'test@example.com',
  full_name: 'Test User',
  phone_number: '',
  skills: [{ id: 1, name: 'Python' }],
  notify_email: true,
  notify_in_app: true,
  cv_file: null,
}
beforeEach(() => {
  vi.resetAllMocks()
  apiClient.get.mockResolvedValue({ data: { enabled: false, confirmed: false, policy_version: 'job-alert-email-v1' } })
})
it('loads and saves contact, skills and independent alert preferences', async () => {
  apiClient.get.mockResolvedValue({ data: profile })
  apiClient.patch.mockResolvedValue({ data: profile })
  render(<MemoryRouter><Profile /></MemoryRouter>)
  await screen.findByLabelText('Full name')
  fireEvent.change(screen.getByLabelText('Full name'), {
    target: { value: 'Updated User' },
  })
  fireEvent.change(screen.getByLabelText('Skills (comma separated)'), {
    target: { value: 'Python, React, Python' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Save profile' }))
  await waitFor(() =>
    expect(apiClient.patch).toHaveBeenCalledWith(
      '/profiles/me/',
      expect.objectContaining({
        full_name: 'Updated User',
        skill_names: ['Python', 'React'],
        notify_in_app: true,
      })
    )
  )
  expect(apiClient.patch.mock.calls[0][1]).not.toHaveProperty('notify_email')
  expect(await screen.findByText('Profile saved.')).toBeVisible()
})
it('clears skills explicitly with an empty array', async () => {
  apiClient.patch.mockResolvedValue({ data: profile })
  render(<MemoryRouter><ProfileEditor profile={profile} /></MemoryRouter>)
  fireEvent.change(screen.getByLabelText('Skills (comma separated)'), {
    target: { value: '' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Save profile' }))
  await waitFor(() =>
    expect(apiClient.patch).toHaveBeenCalledWith(
      '/profiles/me/',
      expect.objectContaining({ skill_names: [] })
    )
  )
})
it('renders all server errors and preserves entered values', async () => {
  apiClient.patch.mockRejectedValue({
    response: {
      data: { phone_number: ['Too long.'], headline: ['Invalid headline.'] },
    },
  })
  render(<MemoryRouter><ProfileEditor profile={profile} /></MemoryRouter>)
  fireEvent.click(screen.getByRole('button', { name: 'Save profile' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Too long.')
  expect(screen.getByRole('alert')).toHaveTextContent('Invalid headline.')
  expect(screen.getByLabelText('Full name')).toHaveValue('Test User')
})
it('validates file type and the 5 MB boundary before upload', () => {
  render(<MemoryRouter><ProfileEditor profile={profile} /></MemoryRouter>)
  fireEvent.change(screen.getByLabelText('Choose CV file'), {
    target: { files: [new File(['data'], 'bad.txt')] },
  })
  expect(screen.getByRole('alert')).toHaveTextContent('Use a PDF, DOC or DOCX')
  expect(screen.getByRole('button', { name: 'Upload CV' })).toBeDisabled()
  expect(apiClient.patch).not.toHaveBeenCalled()
  expect(validateCV({ name: 'cv.pdf', size: MAX_CV_BYTES + 1 })).toMatch('5 MB')
  expect(validateCV({ name: 'cv.docx', size: MAX_CV_BYTES })).toBe('')
})
it('uploads FormData and offers an authenticated download', async () => {
  apiClient.patch.mockResolvedValue({
    data: { ...profile, cv_file: '/media/cv.pdf' },
  })
  render(<MemoryRouter><ProfileEditor profile={profile} /></MemoryRouter>)
  const file = new File(['document'], 'cv.pdf', { type: 'application/pdf' })
  fireEvent.change(screen.getByLabelText('Choose CV file'), {
    target: { files: [file] },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Upload CV' }))
  expect(
    await screen.findByText(
      'CV uploaded. Your profile fields are saved separately.'
    )
  ).toBeVisible()
  expect(apiClient.patch.mock.calls[0][1].get('cv_file')).toBe(file)
  expect(
    screen.getByRole('button', { name: 'Download uploaded CV' })
  ).toBeVisible()
})
it('shows retry after a failed profile read', async () => {
  apiClient.get.mockRejectedValue(new Error('offline'))
  render(<Profile />)
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Please check your connection'
  )
})
it('downloads through the shared client using a server-provided filename', async () => {
  apiClient.get.mockResolvedValue({
    data: new Blob(['doc']),
    headers: { 'content-disposition': 'attachment; filename="my-cv.pdf"' },
  })
  URL.createObjectURL = vi.fn(() => 'blob:test')
  URL.revokeObjectURL = vi.fn()
  let name
  const click = vi
    .spyOn(HTMLAnchorElement.prototype, 'click')
    .mockImplementation(function () {
      name = this.download
    })
  await downloadFile('/profiles/me/cv/', 'fallback')
  expect(apiClient.get).toHaveBeenCalledWith('/profiles/me/cv/', {
    responseType: 'blob',
  })
  expect(name).toBe('my-cv.pdf')
  click.mockRestore()
})
it('reports download failures without creating a broken file', async () => {
  apiClient.get.mockRejectedValue({
    response: { data: { detail: 'Document not found.' } },
  })
  await expect(downloadFile('/missing/', 'missing.docx')).rejects.toThrow(
    'Document not found.'
  )
})
