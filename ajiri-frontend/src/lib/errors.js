const messages = (value) => {
  if (Array.isArray(value)) return value.flatMap(messages)
  if (value && typeof value === 'object')
    return Object.values(value).flatMap(messages)
  return value == null ? [] : [String(value)]
}

// DRF can return field arrays, nested errors, or a single detail string.
// see docs/CONCEPTS.md#drf-field-errors
export function apiErrors(
  error,
  fallback = 'Please check your connection and try again.'
) {
  if (error.response?.status === 429)
    return { detail: [rateLimitMessage(error)] }
  const data = error.response?.data
  if (!data || typeof data !== 'object' || Array.isArray(data))
    return { detail: [fallback] }
  const result = Object.fromEntries(
    Object.entries(data).map(([field, value]) => [field, messages(value)])
  )
  return Object.values(result).some((value) => value.length)
    ? result
    : { detail: [fallback] }
}

// No automatic retry of mutations; let the user choose after the wait.
// see docs/CONCEPTS.md#endpoint-throttling
export function rateLimitMessage(error) {
  const raw = error.response?.headers?.['retry-after']
  const seconds = Number(raw)
  return Number.isFinite(seconds) && seconds > 0
    ? `Too many requests. Please wait ${Math.ceil(seconds)} seconds and try again.`
    : 'Too many requests. Please wait a moment and try again.'
}
