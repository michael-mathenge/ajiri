import { beforeEach, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import JobDetail from '../pages/JobDetail'
import apiClient from '../api/client'
import { ToastProvider } from '../components/ui'
vi.mock('../api/client', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
vi.mock('../lib/download', () => ({ downloadFile: vi.fn() }))
const job = { id: 1, title: 'Developer', company_name: 'Test', description: 'Test role' }
const cv = { revision: 2, approval_id: 'current-id', versions: [{ id: 'current-id', revision: 2 }, { id: 'old-id', revision: 1 }] }
beforeEach(() => vi.resetAllMocks())
function page(data = cv) {
  apiClient.get.mockImplementation(url => Promise.resolve({ data: url === '/profiles/me/cv-versions/' ? data : job }))
  render(<MemoryRouter initialEntries={['/jobs/1']}><ToastProvider><Routes>
    <Route path="/jobs/:id" element={<JobDetail />} />
    <Route path="/applications" element={<h1>Application review</h1>} />
  </Routes></ToastProvider></MemoryRouter>)
}
it('requires a CV when none is approved and offers the builder without posting', async () => {
  page({ content: null })
  expect(await screen.findByRole('link', { name: 'Build and approve your CV' })).toHaveAttribute('href', '/cv-builder')
  expect(screen.getByRole('button', { name: 'Prepare application' })).toBeDisabled()
  expect(apiClient.post).not.toHaveBeenCalled()
})
it('uses an explicitly selected earlier approved version and moves to separate review', async () => {
  apiClient.post.mockResolvedValue({ status: 201 })
  page()
  const selection = await screen.findByLabelText('Approved CV version')
  expect(selection).toHaveValue('current-id')
  fireEvent.change(selection, { target: { value: 'old-id' } })
  fireEvent.click(screen.getByRole('button', { name: 'Prepare application' }))
  expect(await screen.findByRole('heading', { name: 'Application review' })).toBeVisible()
  expect(apiClient.post).toHaveBeenCalledWith('/jobs/1/apply/', { cv_version: 'old-id' })
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})
it('does not silently select an earlier version for an unapproved current draft', async () => {
  page({ ...cv, approval_id: null })
  expect(await screen.findByLabelText('Approved CV version')).toHaveValue('')
  expect(screen.getByRole('button', { name: 'Prepare application' })).toBeDisabled()
})
it('retains uncertainty guidance without automatically retrying preparation', async () => {
  apiClient.post.mockRejectedValue({})
  page()
  await screen.findByLabelText('Approved CV version')
  fireEvent.click(screen.getByRole('button', { name: 'Prepare application' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Check My applications')
  await waitFor(() => expect(apiClient.post).toHaveBeenCalledTimes(1))
  expect(screen.getByRole('link', { name: 'Open My applications' })).toHaveAttribute('href', '/applications')
})
