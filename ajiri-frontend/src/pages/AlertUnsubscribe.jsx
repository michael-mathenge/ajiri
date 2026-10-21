import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import apiClient from '../api/client'
import { Button, Card } from '../components/ui'

export default function AlertUnsubscribe() {
  const { hash } = useLocation()
  const token = new URLSearchParams(hash.slice(1)).get('token') || ''
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [message, setMessage] = useState('')
  async function confirm() {
    if (busy || done) return
    setBusy(true)
    try {
      await apiClient.post('/profiles/alert-unsubscribe/', { token, confirm: true })
      setDone(true); setMessage('Email job alerts are off. In-app alerts and account security emails are unchanged.')
    } catch { setMessage('This link could not be confirmed. Check the link or sign in to change your email preferences.') }
    finally { setBusy(false) }
  }
  return <Card><h1>Unsubscribe from job emails</h1>
    <p>Confirm to turn off email job alerts. Opening this page does not change your choice.</p>
    <Button onClick={confirm} disabled={!token || busy || done}>{done ? 'Unsubscribed' : busy ? 'Updating…' : 'Turn off email job alerts'}</Button>
    <p role="status">{message}</p>
  </Card>
}
