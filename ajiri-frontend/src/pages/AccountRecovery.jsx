import { useSchemaForm } from '../hooks/useSchemaForm'
import { recoverySchema } from '../lib/formSchemas'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import apiClient from '../api/client'
import FormErrors from '../components/FormErrors'
import { Button, Card, Input } from '../components/ui'
import { apiErrors } from '../lib/errors'
import { retryDeadline, waitLabel } from '../lib/retryAfter'

// Fragment credentials never reach access logs/referrers. Remove from history
// immediately and keep only in component memory; never local/session storage.
function takeLink() {
  const values = new URLSearchParams(window.location.hash.slice(1))
  const result = {
    uid: values.get('uid') || '',
    token: values.get('token') || '',
  }
  return result
}

export default function AccountRecovery({ mode }) {
  const [link, setLink] = useState(takeLink)
  const {
    values,
    setValues,
    errors,
    setErrors,
    submit: validateSubmit,
  } = useSchemaForm(recoverySchema(mode), {
    email: '',
    password: '',
    password_confirm: '',
  })
  const { email, password, password_confirm: confirm } = values
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [verified, setVerified] = useState(null)
  const [requestId, setRequestId] = useState(() => crypto.randomUUID())
  const [retryAt, setRetryAt] = useState(0)
  const [now, setNow] = useState(Date.now)
  const remaining = Math.max(0, Math.ceil((retryAt - now) / 1000))
  useEffect(() => {
    if (!retryAt) return
    // Use the clock so a sleeping/background tab does not extend the wait.
    // see docs/CONCEPTS.md#ui-feedback
    const timer = setInterval(() => {
      const current = Date.now()
      setNow(current)
      if (current >= retryAt) clearInterval(timer)
    }, 1000)
    return () => clearInterval(timer)
  }, [retryAt])
  useEffect(() => {
    if (window.location.hash)
      window.history.replaceState(
        window.history.state,
        '',
        window.location.pathname + window.location.search
      )
  }, [])
  const requestReset = mode === 'request-reset'
  const reset = mode === 'reset'
  const verify = mode === 'verify'
  useEffect(() => {
    if (mode !== 'verification') return
    let active = true
    apiClient
      .get('/accounts/verification/status/')
      .then(({ data }) => {
        if (active) setVerified(data.verified)
      })
      .catch((error) => {
        if (active) setErrors(apiErrors(error))
      })
    return () => {
      active = false
    }
  }, [mode, setErrors])
  const missing =
    !done && (reset || verify) && (!link.token || (reset && !link.uid))
  const submit = async () => {
    if (busy || done || missing || Date.now() < retryAt) return
    setErrors({})
    setMessage('')
    if (reset && password !== confirm) {
      setErrors({ password_confirm: ['Passwords must match.'] })
      return
    }
    setBusy(true)
    try {
      const path = requestReset
        ? 'password-reset/request'
        : reset
          ? 'password-reset/confirm'
          : verify
            ? 'verification/confirm'
            : 'verification/request'
      const payload = requestReset
        ? { email, request_id: requestId }
        : reset
          ? { ...link, password, password_confirm: confirm }
          : verify
            ? { token: link.token }
            : { request_id: requestId }
      const { data } = await apiClient.post(`/accounts/${path}/`, payload)
      setMessage(
        data.delivery_available === false
          ? 'Email delivery is not enabled yet. No email was sent. Please try again after email service is available.'
          : data.detail
      )
      if (requestReset || mode === 'verification')
        setRequestId(crypto.randomUUID())
      if (reset || verify) {
        setDone(true)
        setLink({ uid: '', token: '' })
        setValues({ email: '', password: '', password_confirm: '' })
      }
    } catch (error) {
      const deadline =
        error.response?.status === 429
          ? retryDeadline(error.response.headers)
          : 0
      setNow(Date.now())
      setRetryAt(deadline)
      setErrors(
        deadline
          ? { detail: ['Too many requests. Please wait before trying again.'] }
          : apiErrors(
              error,
              'Delivery could not be confirmed. Check your inbox before retrying; an email may already have been accepted.'
            )
      )
      if (error.response?.status === 502) setRequestId(crypto.randomUUID())
    } finally {
      setBusy(false)
    }
  }
  const title = requestReset
    ? 'Reset your password'
    : reset
      ? 'Choose a new password'
      : verify
        ? 'Verify your email'
        : 'Email verification'
  return (
    <Card className="auth-card">
      <h1>{title}</h1>
      <p>Keep your account and application replies secure.</p>
      {missing && (
        <p role="alert">This link is incomplete. Request a new link.</p>
      )}
      {verified === true && (
        <p role="status">Your current email is verified.</p>
      )}
      {verified === false && (
        <p>
          Your current email is not verified. You can still browse jobs and
          prepare drafts.
        </p>
      )}
      {message && <p role="status">{message}</p>}
      <FormErrors errors={errors} prefix="recovery" />
      {retryAt > 0 && (
        <p aria-live="off">
          {remaining > 0
            ? `You can try again in ${waitLabel(remaining)}.`
            : 'You can now try again. No request has been sent automatically.'}
        </p>
      )}
      <form
        className="stack mt-8"
        noValidate
        onSubmit={(event) => {
          if (busy || done || missing || Date.now() < retryAt) {
            event.preventDefault()
            return
          }
          return validateSubmit(submit)(event)
        }}
        aria-busy={busy}
      >
        {requestReset && (
          <div className="field">
            <label htmlFor="recovery-email">Email address</label>
            <Input
              aria-invalid={Boolean(errors.email)}
              aria-describedby={
                errors.email ? 'recovery-email-error' : undefined
              }
              id="recovery-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => {
                setValues({ ...values, email: e.target.value })
                setRequestId(crypto.randomUUID())
              }}
              required
            />
          </div>
        )}
        {reset && !done && (
          <>
            <div className="field">
              <label htmlFor="recovery-password">New password</label>
              <Input
                aria-invalid={Boolean(errors.password)}
                aria-describedby={
                  errors.password ? 'recovery-password-error' : undefined
                }
                id="recovery-password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) =>
                  setValues({ ...values, password: e.target.value })
                }
                required
              />
            </div>
            <div className="field">
              <label htmlFor="recovery-confirm">Confirm new password</label>
              <Input
                aria-invalid={Boolean(errors.password_confirm)}
                aria-describedby={
                  errors.password_confirm
                    ? 'recovery-password_confirm-error'
                    : undefined
                }
                id="recovery-confirm"
                type="password"
                autoComplete="new-password"
                value={confirm}
                onChange={(e) =>
                  setValues({ ...values, password_confirm: e.target.value })
                }
                required
              />
            </div>
          </>
        )}
        <Button
          type="submit"
          disabled={
            busy || done || missing || verified === true || remaining > 0
          }
        >
          {busy
            ? 'Please wait…'
            : requestReset
              ? 'Request reset link'
              : reset
                ? 'Save new password'
                : verify
                  ? 'Confirm email verification'
                  : 'Request verification link'}
        </Button>
      </form>
      <p>
        <Link to="/login">Back to login</Link>
      </p>
      {(reset || verify) && !done && (
        <Link to={reset ? '/forgot-password' : '/email-verification'}>
          Request a new link
        </Link>
      )}
    </Card>
  )
}
