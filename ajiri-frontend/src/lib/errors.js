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
