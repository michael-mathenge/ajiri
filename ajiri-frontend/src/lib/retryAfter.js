// Retry-After supports seconds or an HTTP date. Never guess a missing deadline.
// see docs/CONCEPTS.md#ui-feedback
export function retryDeadline(headers, now = Date.now()) {
  const raw = headers?.get?.('retry-after') ?? headers?.['retry-after']
  if (raw == null || String(raw).trim() === '') return 0
  const value = String(raw).trim()
  if (/^\d+(\.\d+)?$/.test(value)) {
    const deadline = now + Number(value) * 1000
    return Number.isFinite(deadline) ? deadline : 0
  }
  if (/^[+-]?\d/.test(value)) return 0
  const deadline = Date.parse(value)
  return Number.isFinite(deadline) && deadline > now ? deadline : 0
}

export function waitLabel(seconds) {
  const minutes = Math.floor(seconds / 60)
  const rest = seconds % 60
  return minutes ? `${minutes} min${rest ? ` ${rest} sec` : ''}` : `${rest} sec`
}
