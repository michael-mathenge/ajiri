import { useCallback, useRef, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'

// Keep editor values in RHF memory. Schema failures never make a request;
// server validation remains authoritative and preserves its existing message IDs.
// see docs/CONCEPTS.md#schema-forms
export function schemaMessages(issues) {
  const result = {}
  for (const issue of issues) {
    const path = issue.path.join('.') || 'detail'
    ;(result[path] ||= []).push(issue.message)
  }
  return result
}
export function useSchemaForm(schema, defaultValues) {
  const inFlight = useRef(false)
  const [errors, setErrors] = useState({})
  const form = useForm({
    defaultValues,
    resolver: async (values) => {
      const parsed = schema.safeParse(values)
      if (parsed.success) return { values: parsed.data, errors: {} }
      const messages = schemaMessages(parsed.error.issues)
      return {
        values: {},
        errors: Object.fromEntries(
          Object.entries(messages).map(([key, value]) => [
            key,
            { type: 'schema', message: value.join(' '), messages: value },
          ])
        ),
      }
    },
  })
  const values = useWatch({ control: form.control })
  const { getValues, setValue } = form
  const setValues = useCallback(
    (next) => {
      const updated = typeof next === 'function' ? next(getValues()) : next
      for (const [key, value] of Object.entries(updated)) {
        setValue(key, value, { shouldDirty: true })
      }
    },
    [getValues, setValue]
  )
  const submit = (action) => async (event) => {
    event?.preventDefault()
    if (inFlight.current) return
    inFlight.current = true
    try {
      await form.handleSubmit(
        async (data) => {
          setErrors({})
          await action(data)
        },
        (invalid) => {
          setErrors(
            Object.fromEntries(
              Object.entries(invalid).map(([key, error]) => [
                key,
                error.messages || [error.message],
              ])
            )
          )
        }
      )(event)
    } finally {
      inFlight.current = false
    }
  }
  return { values, setValues, errors, setErrors, submit, form }
}
