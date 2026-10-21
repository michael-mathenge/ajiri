import { useEffect, useId, useRef, useState } from 'react'
import apiClient from '../api/client'
import { useApiInvalidation } from '../hooks/useApiQuery'
import { apiErrors } from '../lib/errors'
import FormErrors from './FormErrors'
import { Button } from './ui'

const permission =
  'I authorize Ajiri to email this exact application and the two listed documents to the displayed recipient for this job. Copies are off. This permission covers this application only. I can withdraw it until sending starts; after that Ajiri may be unable to stop or recall it.'
const outcomes = {
  reserved: 'Sending or outcome pending. Check the receipt; do not send again.',
  accepted: 'Accepted by the email provider. Inbox delivery is not confirmed.',
  definite_failure:
    'The provider definitely rejected this attempt. One separately authorized retry may be available.',
  unknown:
    'Delivery outcome unknown. Sending is blocked pending operator reconciliation.',
}
const states = {
  authorized: 'Authorized; no dispatch recorded.',
  withdrawn: 'Authorization withdrawn.',
  expired:
    'Authorization expired. Review a fresh plan before authorizing again.',
  superseded: 'A newer saved package superseded this authorization.',
  dispatch_started:
    'Sending has started or may have started; cancellation cannot be guaranteed.',
}

// Separate document approval, permission and dispatch. Never auto-repeat a mutation.
// see docs/CONCEPTS.md#application-send-authorization
export default function ApplicationSendPanel({ applicationId, packageId }) {
  return (
    <SendSession
      key={`${applicationId}:${packageId}`}
      applicationId={applicationId}
      packageId={packageId}
    />
  )
}

function SendSession({ applicationId, packageId }) {
  const invalidate = useApiInvalidation()
  const id = useId()
  const alive = useRef(true)
  const inFlight = useRef(false)
  const pendingKey = useRef(null)
  const [preview, setPreview] = useState(null)
  const [authorization, setAuthorization] = useState(null)
  const [checked, setChecked] = useState(false)
  const [busy, setBusy] = useState(false)
  const [uncertain, setUncertain] = useState(false)
  const [errors, setErrors] = useState({})
  const base = `/jobs/applications/${applicationId}`
  useEffect(() => {
    alive.current = true
    return () => {
      alive.current = false
    }
  }, [])
  const run = async (operation) => {
    if (inFlight.current) return
    inFlight.current = true
    setBusy(true)
    setChecked(false)
    setErrors({})
    try {
      await operation()
    } catch (error) {
      if (alive.current) {
        setUncertain(true)
        setErrors(
          apiErrors(
            error,
            'The action could not be confirmed. Check authorization status before another action.'
          )
        )
      }
    } finally {
      if (alive.current) {
        inFlight.current = false
        setBusy(false)
      }
    }
  }
  const show = (row) => {
    if (!alive.current) return
    setAuthorization(row)
    setPreview({
      plan: row.plan,
      plan_sha256: row.plan_sha256,
      dispatch_enabled: row.dispatch_enabled,
      disabled_reason: row.disabled_reason,
    })
    setUncertain(false)
    pendingKey.current = null
  }
  const load = () =>
    run(async () => {
      let row
      if (pendingKey.current) {
        try {
          const { data } = await apiClient.get(`${base}/send-authorizations/`, {
            params: { request_key: pendingKey.current },
          })
          row = data
        } catch (error) {
          if (error.response?.status !== 404) throw error
          // A missing reconciliation key never causes another POST; inspect owner history.
        }
      } else if (authorization) {
        const { data } = await apiClient.get(
          `${base}/send-authorizations/${authorization.id}/`
        )
        row = data
      }
      if (!row) {
        const { data } = await apiClient.get(`${base}/send-authorizations/`)
        row = data.results.find((item) => item.plan.package_id === packageId)
      }
      if (!alive.current) return
      if (row && (row.state === 'authorized' || row.attempt)) {
        show(row)
        return
      }
      const { data } = await apiClient.get(`${base}/send-plan/`)
      if (alive.current) {
        setAuthorization(row || null)
        setPreview(data)
        setUncertain(false)
        pendingKey.current = null
      }
    })
  const authorize = () => {
    if (
      !checked ||
      uncertain ||
      !preview ||
      authorization?.state === 'authorized'
    )
      return
    run(async () => {
      const key = globalThis.crypto.randomUUID()
      pendingKey.current = key
      const plan = preview.plan
      const { data } = await apiClient.post(`${base}/send-authorizations/`, {
        request_key: key,
        package_id: plan.package_id,
        expected_revision: plan.revision,
        plan_sha256: preview.plan_sha256,
        authorization: true,
        ...(plan.retry_of ? { retry_of: plan.retry_of } : {}),
      })
      invalidate()
      show(data)
    })
  }
  const mutate = (action) => {
    if (!authorization || uncertain) return
    if (
      action === 'dispatch' &&
      (!preview?.dispatch_enabled || authorization.state !== 'authorized')
    )
      return
    run(async () => {
      const { data } = await apiClient.post(
        `${base}/send-authorizations/${authorization.id}/${action}/`,
        {}
      )
      invalidate()
      if (action === 'withdraw' && alive.current) {
        setAuthorization(data)
        setPreview(null)
        setUncertain(false)
      } else show(data)
    })
  }
  const retry = () =>
    run(async () => {
      const { data } = await apiClient.get(`${base}/send-plan/`, {
        params: { retry_of: authorization.attempt.id },
      })
      if (alive.current) {
        setPreview(data)
        setAuthorization(null)
        setUncertain(false)
      }
    })
  const plan = preview?.plan
  const mayAuthorize =
    plan && authorization?.state !== 'authorized' && !authorization?.attempt
  return (
    <section className="stack" aria-label="Application email authorization">
      <h4>Application email permission</h4>
      <p>
        Document approval does not authorize sending. Review the exact email
        plan before giving separate permission.
      </p>
      <Button variant="outline" disabled={busy} onClick={load}>
        Review email plan / check authorization status
      </Button>
      <FormErrors errors={errors} prefix={id} />
      {uncertain && (
        <p role="status">
          No automatic retry was made. Check authorization status to reconcile
          the result.
        </p>
      )}
      {plan && (
        <>
          <div className="detail-block stack">
            <p>Package revision {plan.revision}</p>
            <p>To: {plan.recipient}</p>
            <p>Reply-To: {plan.reply_to}</p>
            <p>
              From: {plan.sender_name} &lt;{plan.sender}&gt;
            </p>
            <p>Subject: {plan.subject}</p>
            <p className="job-copy">{plan.body}</p>
            <p>Attachments:</p>
            <ul>
              {plan.attachments.map((file) => (
                <li key={file.role}>
                  {file.filename} — {file.size} bytes (DOCX)
                </li>
              ))}
            </ul>
            <p>
              Copies: OFF. Permission expires 24 hours after it is recorded.
            </p>
            {plan.retry_of && (
              <p>
                This is the one explicit retry of definite-failure attempt{' '}
                {plan.retry_of}.
              </p>
            )}
          </div>
          {!preview.dispatch_enabled && (
            <p>
              {preview.disabled_reason ||
                'Real application sending is disabled.'}
            </p>
          )}
          {authorization && (
            <>
              <p role="status">
                {states[authorization.state] ||
                  'Check the current authorization state.'}
              </p>
              <p>
                Permission expires:{' '}
                <time dateTime={authorization.expires_at}>
                  {authorization.expires_at}
                </time>
              </p>
              {authorization.attempt && (
                <p role="status">
                  {outcomes[authorization.attempt.state] ||
                    'Outcome needs operator reconciliation; do not resend.'}
                </p>
              )}
            </>
          )}
          {mayAuthorize && (
            <>
              <label className="check-field" htmlFor={`${id}-authorize`}>
                <input
                  id={`${id}-authorize`}
                  type="checkbox"
                  checked={checked}
                  disabled={busy || uncertain}
                  onChange={(event) => setChecked(event.target.checked)}
                />
                {permission}
              </label>
              <Button
                disabled={!checked || busy || uncertain}
                onClick={authorize}
              >
                Record authorization (does not send)
              </Button>
            </>
          )}
          {authorization?.state === 'authorized' && (
            <div className="action-group">
              <Button
                disabled={busy || uncertain || !preview.dispatch_enabled}
                onClick={() => mutate('dispatch')}
              >
                Send this authorized application
              </Button>
              <Button
                variant="outline"
                disabled={busy || uncertain}
                onClick={() => mutate('withdraw')}
              >
                Withdraw authorization
              </Button>
            </div>
          )}
          {authorization?.attempt?.state === 'definite_failure' &&
            !authorization.plan.retry_of && (
              <Button
                variant="outline"
                disabled={busy || uncertain}
                onClick={retry}
              >
                Review one manual retry
              </Button>
            )}
        </>
      )}
    </section>
  )
}
