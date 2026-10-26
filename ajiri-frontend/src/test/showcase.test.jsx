import { beforeEach, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { fireEvent, render, screen } from './test-utils'
import App from '../App'
import apiClient from '../api/client'

vi.mock('../api/client', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
vi.mock('../pages/JobList', () => ({ default: () => <h1>Signed-in jobs</h1> }))
beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
})
const visit = (path = '/') =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>
  )

it('introduces the product before login without requesting account or job data', async () => {
  visit()
  expect(
    await screen.findByRole('heading', {
      name: 'Build your CV. Prepare your next application.',
    })
  ).toBeVisible()
  expect(
    screen.getByRole('link', { name: 'Create a free account' })
  ).toHaveAttribute('href', '/register')
  expect(screen.getByText(/there may be no active jobs/)).toBeVisible()
  expect(
    screen.getByText(/Application email delivery is not generally enabled/)
  ).toBeVisible()
  expect(apiClient.get).not.toHaveBeenCalled()
  expect(apiClient.post).not.toHaveBeenCalled()
})

it('opens the independent employer review guide without sending or collecting data', async () => {
  visit()
  fireEvent.click(
    await screen.findByRole('link', { name: 'How employer review works' })
  )
  expect(
    await screen.findByRole('heading', {
      name: 'Credible vacancies, reviewed before publication.',
    })
  ).toBeVisible()
  expect(
    screen.getByText(/reviewer must be different from the submitting account/)
  ).toBeVisible()
  expect(
    screen.getByRole('link', { name: 'Open employer workspace' })
  ).toHaveAttribute('href', '/employers')
  expect(apiClient.get).not.toHaveBeenCalled()
  expect(apiClient.post).not.toHaveBeenCalled()
})

it.each(['/profile', '/applications', '/cv-builder', '/employers'])(
  'keeps %s behind login',
  async (path) => {
    visit(path)
    expect(
      await screen.findByLabelText('Email address', {}, { timeout: 5000 })
    ).toBeVisible()
    expect(apiClient.get).not.toHaveBeenCalled()
    expect(apiClient.post).not.toHaveBeenCalled()
  }
)

it('preserves signed-in jobs and a direct CV-builder navigation link', async () => {
  localStorage.setItem('access_token', 'synthetic-showcase-token')
  visit()
  expect(
    await screen.findByRole('heading', { name: 'Signed-in jobs' })
  ).toBeVisible()
  expect(screen.getByRole('link', { name: 'CV builder' })).toHaveAttribute(
    'href',
    '/cv-builder'
  )
  expect(
    screen.queryByRole('heading', {
      name: 'Build your CV. Prepare your next application.',
    })
  ).not.toBeInTheDocument()
})

it('lets a signed-in owner preview the public introduction without changing account state', async () => {
  localStorage.setItem('access_token', 'synthetic-showcase-token')
  visit('/about')
  expect(
    await screen.findByRole('heading', {
      name: 'Build your CV. Prepare your next application.',
    })
  ).toBeVisible()
  expect(localStorage.getItem('access_token')).toBe('synthetic-showcase-token')
  expect(apiClient.get).not.toHaveBeenCalled()
  expect(apiClient.post).not.toHaveBeenCalled()
})
