import { beforeEach, expect, it, vi } from 'vitest'
import { render, screen } from './test-utils'
import { MemoryRouter } from 'react-router-dom'
import JobList from '../pages/JobList'
import apiClient from '../api/client'

vi.mock('../api/client', () => ({ default: { get: vi.fn() } }))
const jobs = {
  count: 1,
  results: [
    {
      id: 1,
      title: 'Developer',
      company_name: 'Example',
      match_score: 0,
      publication: { status: 'published', closes_at: '2099-01-01T00:00:00Z' },
    },
  ],
}
beforeEach(() => vi.resetAllMocks())
function page(profile) {
  apiClient.get.mockImplementation((url) =>
    url === '/profiles/me/' ? profile : Promise.resolve({ data: jobs })
  )
  render(
    <MemoryRouter>
      <JobList />
    </MemoryRouter>
  )
}
it('replaces the score with a profile link when skills are empty', async () => {
  page(Promise.resolve({ data: { skills: [] } }))
  expect(
    await screen.findByRole('link', { name: 'Add skills to see matches' })
  ).toHaveAttribute('href', '/profile')
  expect(screen.queryByText('0% skill match')).not.toBeInTheDocument()
})
it('preserves a genuine zero score when the profile has skills', async () => {
  page(Promise.resolve({ data: { skills: [{ name: 'Python' }] } }))
  expect(await screen.findByText('0% skill match')).toBeVisible()
  expect(
    screen.queryByText('Add skills to see matches')
  ).not.toBeInTheDocument()
})
it('keeps jobs available without guessing when the profile request fails', async () => {
  apiClient.get.mockImplementation((url) =>
    url === '/profiles/me/'
      ? Promise.reject(new Error('Unavailable'))
      : Promise.resolve({ data: jobs })
  )
  render(
    <MemoryRouter>
      <JobList />
    </MemoryRouter>
  )
  expect(await screen.findByText('Developer')).toBeVisible()
  expect(screen.queryByText('0% skill match')).not.toBeInTheDocument()
  expect(
    screen.queryByText('Add skills to see matches')
  ).not.toBeInTheDocument()
})
it('includes the visible View job words in each accessible link name', async () => {
  page(Promise.resolve({ data: { skills: [] } }))
  const link = await screen.findByRole('link', {
    name: 'View job: Developer at Example',
  })
  expect(link).toHaveTextContent('View job')
  expect(link).toHaveAttribute('href', '/jobs/1')
})
