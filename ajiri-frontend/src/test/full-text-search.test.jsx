import { expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from './test-utils'
import { MemoryRouter } from 'react-router-dom'
import apiClient from '../api/client'
import JobList from '../pages/JobList'
vi.mock('../api/client', () => ({ default: { get: vi.fn() } }))
it('submits keyword search with location and preserves the entered filters', async () => {
  apiClient.get.mockImplementation((url) =>
    Promise.resolve({
      data:
        url === '/profiles/me/' ? { skills: [] } : { results: [], count: 0 },
    })
  )
  render(
    <MemoryRouter>
      <JobList />
    </MemoryRouter>
  )
  await screen.findByText('No opportunities yet')
  fireEvent.change(screen.getByLabelText('Job keywords'), {
    target: { value: 'project manager' },
  })
  fireEvent.change(screen.getByLabelText('Location'), {
    target: { value: 'Nairobi' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Search jobs' }))
  await waitFor(() =>
    expect(apiClient.get).toHaveBeenCalledWith(
      '/jobs/?page=1&q=project+manager&location=Nairobi',
      expect.any(Object)
    )
  )
  expect(screen.getByLabelText('Job keywords')).toHaveValue('project manager')
  expect(screen.getByLabelText('Location')).toHaveValue('Nairobi')
  expect(await screen.findByText('No jobs match those filters')).toBeVisible()
})
it('retains existing title-filter links without changing their request semantics', async () => {
  apiClient.get.mockResolvedValue({
    data: { results: [], count: 0, skills: [] },
  })
  render(
    <MemoryRouter initialEntries={['/?title=Developer']}>
      <JobList />
    </MemoryRouter>
  )
  await waitFor(() =>
    expect(apiClient.get).toHaveBeenCalledWith(
      '/jobs/?page=1&title=Developer',
      expect.any(Object)
    )
  )
  expect(screen.getByLabelText('Job keywords')).toHaveValue('Developer')
})

it('shows bounded keyword validation before making a search request', async () => {
  apiClient.get.mockResolvedValue({
    data: { results: [], count: 0, skills: [] },
  })
  render(
    <MemoryRouter>
      <JobList />
    </MemoryRouter>
  )
  await screen.findByText('No opportunities yet')
  apiClient.get.mockClear()
  fireEvent.change(screen.getByLabelText('Job keywords'), {
    target: { value: 'word '.repeat(13) },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Search jobs' }))
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Use at most 12 words'
  )
  expect(apiClient.get).not.toHaveBeenCalled()
})
