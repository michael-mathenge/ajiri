import { useEffect, useRef, useState } from 'react'
import apiClient from '../api/client'
import { useApiInvalidation } from '../hooks/useApiQuery'
import { Button, Card } from './ui'

export default function AlertPreferences() {
  const invalidate = useApiInvalidation()
  const [state, setState] = useState(null)
  const [enabled, setEnabled] = useState(false)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const key = useRef(null)
  useEffect(() => {
    let active = true
    apiClient
      .get('/profiles/me/alert-preferences/')
      .then(({ data }) => {
        if (active) {
          setState(data)
          setEnabled(data.enabled && data.confirmed)
        }
      })
      .catch(() => {
        if (active)
          setMessage(
            'Email preferences could not load. Reload before choosing.'
          )
      })
    return () => {
      active = false
    }
  }, [])
  async function save(event) {
    event.preventDefault()
    if (busy || !state) return
    setBusy(true)
    key.current ||= crypto.randomUUID()
    try {
      const { data } = await apiClient.post('/profiles/me/alert-preferences/', {
        enabled,
        decision_id: key.current,
        policy_version: state.policy_version,
      })
      invalidate()
      setState(data)
      setEnabled(data.enabled && data.confirmed)
      key.current = null
      setMessage(
        data.enabled
          ? data.delivery_status === 'owner_pilot'
            ? 'Email choice recorded. A verified email is required; only an explicit synthetic owner pilot can send.'
            : 'Email choice recorded. Delivery is currently disabled for this account.'
          : 'Email job alerts are off.'
      )
    } catch {
      setMessage(
        'Your choice could not be confirmed. Retry this same choice or reload to check its status.'
      )
    } finally {
      setBusy(false)
    }
  }
  return (
    <Card>
      <h2>Email job alerts</h2>
      <p>
        Choose whether Ajiri may email strong job matches to your current
        account address. You can unsubscribe at any time. This is separate from
        account security emails and in-app alerts.
      </p>
      {state?.enabled && !state.confirmed && (
        <p>
          Your earlier preference has no recorded consent. Email alerts remain
          ineligible until you make a choice.
        </p>
      )}
      {state && (
        <p className="muted">
          {state.delivery_status === 'owner_pilot'
            ? 'Delivery is limited to an explicit synthetic owner pilot. Normal job emails are not active.'
            : 'Email delivery is currently disabled for this account. You can still record or withdraw your choice.'}
        </p>
      )}
      <form onSubmit={save} className="stack" aria-busy={busy}>
        <label className="check-field">
          <input
            type="checkbox"
            checked={enabled}
            disabled={!state || busy}
            onChange={(event) => {
              setEnabled(event.target.checked)
              key.current = null
            }}
          />
          I want email alerts about strong job matches
        </label>
        <Button type="submit" disabled={!state || busy}>
          {busy ? 'Saving…' : 'Save email choice'}
        </Button>
      </form>
      <p role="status">{message}</p>
    </Card>
  )
}
