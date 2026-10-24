import { useState } from 'react'
import apiClient from '../api/client'
import { apiErrors } from '../lib/errors'
import FormErrors from './FormErrors'
import { Button, Select, Textarea } from './ui'

const stages = {
  not_reported: 'No update reported',
  applied: 'Applied (your report)',
  interview: 'Interview (your report)',
  offer: 'Offer (your report)',
  closed: 'Closed (your report)',
}

export default function ApplicationProgress({ application, onUpdate }) {
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState({})
  const [saved, setSaved] = useState(false)
  const prefix = `progress-${application.id}`

  async function save(event) {
    event.preventDefault()
    if (busy) return
    const form = event.currentTarget
    const values = Object.fromEntries(new FormData(form))
    setBusy(true)
    setErrors({})
    setSaved(false)
    try {
      const { data } = await apiClient.patch(
        `/jobs/applications/${application.id}/progress/`,
        { ...values, expected_revision: application.progress_revision ?? 0 }
      )
      onUpdate(data)
      setSaved(true)
    } catch (error) {
      setErrors(apiErrors(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="stack" aria-label="Your application progress">
      <h3>Your progress update</h3>
      <p>
        These are your own notes, not confirmation from an employer. Saving an
        update does not submit an application, send email or change approved
        documents.
      </p>
      <p>{stages[application.progress_stage] || stages.not_reported}</p>
      {application.progress_reported_at && (
        <p className="muted">
          Updated by you{' '}
          {new Date(application.progress_reported_at).toLocaleString('en-KE')}
        </p>
      )}
      <FormErrors
        errors={errors}
        prefix={prefix}
        fieldLabels={{
          stage: 'Your progress',
          note: 'Private note',
          expected_revision: 'Update revision',
        }}
      />
      {saved && (
        <p role="status">Your update is saved. No application was sent.</p>
      )}
      <form
        className="stack"
        key={application.progress_revision ?? 0}
        onSubmit={save}
      >
        <div className="field">
          <label htmlFor={`${prefix}-stage`}>Your progress</label>
          <Select
            id={`${prefix}-stage`}
            name="stage"
            disabled={busy}
            defaultValue={application.progress_stage || 'not_reported'}
            aria-invalid={Boolean(errors.stage)}
            aria-describedby={
              errors.stage ? `${prefix}-stage-error` : undefined
            }
          >
            {Object.entries(stages).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </div>
        <div className="field">
          <label htmlFor={`${prefix}-note`}>Private note (optional)</label>
          <Textarea
            id={`${prefix}-note`}
            name="note"
            disabled={busy}
            maxLength={1000}
            defaultValue={application.progress_note || ''}
            aria-invalid={Boolean(errors.note)}
            aria-describedby={errors.note ? `${prefix}-note-error` : undefined}
          />
        </div>
        <Button type="submit" disabled={busy}>
          {busy ? 'Saving update…' : 'Save my update'}
        </Button>
      </form>
    </section>
  )
}
