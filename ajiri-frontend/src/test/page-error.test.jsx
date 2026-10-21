import { afterEach, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from './test-utils'
import PageErrorBoundary from '../components/PageErrorBoundary'

afterEach(() => vi.restoreAllMocks())

it('shows an explicit safe recovery without exception details or automatic reload', () => {
  vi.spyOn(console, 'error').mockImplementation(() => {})
  const reload = vi.fn()
  function BrokenPage() {
    throw new Error('synthetic-private-exception-content')
  }
  render(
    <PageErrorBoundary onReload={reload}>
      <BrokenPage />
    </PageErrorBoundary>
  )
  expect(
    screen.getByRole('heading', { name: 'This page could not load' })
  ).toBeInTheDocument()
  expect(
    screen.queryByText(/synthetic-private-exception/)
  ).not.toBeInTheDocument()
  expect(reload).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: 'Reload application' }))
  expect(reload).toHaveBeenCalledOnce()
})

it('leaves a healthy page unchanged', () => {
  render(
    <PageErrorBoundary>
      <h1>Healthy page</h1>
    </PageErrorBoundary>
  )
  expect(
    screen.getByRole('heading', { name: 'Healthy page' })
  ).toBeInTheDocument()
  expect(
    screen.queryByRole('button', { name: 'Reload application' })
  ).not.toBeInTheDocument()
})
