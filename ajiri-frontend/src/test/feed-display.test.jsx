import { beforeEach, expect, it, vi } from 'vitest'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { render, screen } from './test-utils'
import JobList from '../pages/JobList'
import JobDetail from '../pages/JobDetail'
import { availableAt, displayableAt } from '../hooks/useVacancyClock'
import apiClient from '../api/client'

vi.mock('../api/client', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
const notice = "Not verified: check the employer's page before applying"
const job = {
  id: 1,
  title: 'Unverified developer',
  company_name: 'Synthetic',
  description: 'Synthetic role',
  source_name: 'Feed',
  posted_at: null,
  publication: { status: 'archived' },
  display_only: true,
  display_notice: notice,
  can_apply: false,
  original_source_url: 'https://example.invalid/original',
  source_url: 'https://example.invalid/application',
}
beforeEach(() => {
  vi.resetAllMocks()
  apiClient.get.mockImplementation((url) =>
    Promise.resolve({
      data:
        url === '/profiles/me/'
          ? { skills: [] }
          : url === '/profiles/me/cv-versions/'
            ? { versions: [{ id: 'cv', revision: 1 }] }
            : url.startsWith('/jobs/?')
              ? { count: 1, results: [job] }
              : job,
    })
  )
})

it('displays labelled feed cards with source and explicit missing date', async () => {
  render(
    <MemoryRouter>
      <JobList />
    </MemoryRouter>
  )
  expect(await screen.findByText(notice)).toBeVisible()
  expect(screen.getByText('Posted date not supplied')).toBeVisible()
  expect(
    screen.getByRole('link', { name: 'View original listing' })
  ).toHaveAttribute('href', job.original_source_url)
  expect(
    screen.queryByRole('button', { name: /apply|send|prepare/i })
  ).not.toBeInTheDocument()
})

it('displays details without application or document actions', async () => {
  render(
    <MemoryRouter initialEntries={['/jobs/1']}>
      <Routes>
        <Route path="/jobs/:id" element={<JobDetail />} />
      </Routes>
    </MemoryRouter>
  )
  expect(await screen.findByText(notice)).toBeVisible()
  expect(screen.getByText('Posted date not supplied')).toBeVisible()
  expect(
    screen.getByRole('link', { name: /View original listing/ })
  ).toHaveAttribute('href', job.original_source_url)
  expect(screen.queryByText('Prepare application')).not.toBeInTheDocument()
  expect(screen.queryByText('Generate cover letter')).not.toBeInTheDocument()
  expect(screen.queryByLabelText('Approved CV version')).not.toBeInTheDocument()
  expect(screen.queryByText('Review selected CV')).not.toBeInTheDocument()
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('does not reinterpret display-only rows as available vacancies', () => {
  expect(availableAt(job, Date.now())).toBe(false)
  expect(displayableAt(job, Date.now())).toBe(true)
  expect(displayableAt({ ...job, can_apply: true }, Date.now())).toBe(false)
  expect(
    displayableAt(
      { ...job, publication: { closes_at: '2020-01-01T00:00:00Z' } },
      Date.now()
    )
  ).toBe(false)
  const eligible = {
    publication: { status: 'published', closes_at: '2099-01-01T00:00:00Z' },
  }
  expect(displayableAt(eligible, Date.now())).toBe(true)
  expect(displayableAt(eligible, Date.parse('2099-01-01T00:00:00Z'))).toBe(
    false
  )
})
