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
  const editRevision = useRef(0)
  const [errors, setErrors] = useState({})
  const [validating, setValidating] = useState(false)
  const form = useForm({
    defaultValues,
    resolver: async (values) => {
      // Public forms load validators on submit, keeping them off the first paint.
      // A failed download must never skip validation or start an API mutation.
      let validator = schema
      try {
        if (typeof schema === 'function') {
          setValidating(true)
          validator = await schema()
        }
      } catch {
        const message =
          'Could not load form validation. Check your connection and try again.'
        return {
          values: {},
          errors: {
            detail: { type: 'schema_load', message, messages: [message] },
          },
        }
      } finally {
        setValidating(false)
      }
      const parsed = validator.safeParse(values)
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
      if (
        Object.entries(updated).some(
          ([key, value]) => !Object.is(getValues(key), value)
        )
      ) {
        editRevision.current += 1
      }
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
    const revision = editRevision.current
    try {
      await form.handleSubmit(
        async (data) => {
          // Changed input (including agreement) needs a new explicit submit.
          if (editRevision.current !== revision) {
            setErrors({
              detail: [
                'Your form changed while checking. Review it and submit again.',
              ],
            })
            return
          }
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
  return {
    values,
    setValues,
    errors,
    setErrors,
    submit,
    validating,
    form,
  }
}
