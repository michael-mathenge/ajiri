import { expect, it } from 'vitest'
import { retryDeadline, waitLabel } from '../lib/retryAfter'

it('accepts delay seconds and HTTP dates without guessing missing or malformed values', () => {
  const now = Date.parse('2026-10-17T12:00:00Z')
  expect(retryDeadline({ 'retry-after': '60' }, now)).toBe(now + 60000)
  expect(retryDeadline({ 'retry-after': 'Sat, 17 Oct 2026 12:01:00 GMT' }, now)).toBe(now + 60000)
  for (const raw of [undefined, '', '-1', 'garbage', 'Infinity', 'Sat, 17 Oct 2026 11:00:00 GMT'])
    expect(retryDeadline({ 'retry-after': raw }, now)).toBe(0)
  expect(waitLabel(2270)).toBe('37 min 50 sec')
  expect(waitLabel(2)).toBe('2 sec')
})
