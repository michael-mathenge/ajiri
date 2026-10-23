import { afterEach, expect, it, vi } from 'vitest'
import { act, render, screen } from './test-utils'
import { availableAt, useVacancyClock } from '../hooks/useVacancyClock'

afterEach(() => vi.useRealTimers())
const start = Date.parse('2026-10-23T10:00:00Z')
it('removes a displayed vacancy at its closing time without refreshing the page', () => {
  vi.useFakeTimers()
  vi.setSystemTime(start)
  const job = { publication: { status: 'published', closes_at: '2026-10-23T10:00:01Z' } }
  function Display() {
    const now = useVacancyClock([job])
    return <p>{availableAt(job, now) ? 'Applications open' : 'Applications closed'}</p>
  }
  render(<Display />)
  expect(screen.getByText('Applications open')).toBeVisible()
  act(() => vi.advanceTimersByTime(1001))
  expect(screen.getByText('Applications closed')).toBeVisible()
})

it('fails closed on absent, invalid or archived availability evidence', () => {
  for (const publication of [undefined, { status: 'published' },
    { status: 'published', closes_at: 'invalid' },
    { status: 'archived', closes_at: '2099-01-01T00:00:00Z' }]) {
    expect(availableAt({ publication }, start)).toBe(false)
  }
})
