import { useState } from 'react'
import apiClient from '../api/client'
import { apiErrors } from '../lib/errors'
import { useApiQuery, useApiInvalidation } from '../hooks/useApiQuery'
import { Button, ErrorState } from './ui'
import FormErrors from './FormErrors'

function SavedJobAction({ jobId, saved, title, onComplete }) {
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const refresh = useApiInvalidation()
  async function choose() {
    if (busy) return
    setBusy(true)
    setErrors({})
    setMessage('')
    try {
      const path = `/jobs/${jobId}/saved/`
      if (saved) await apiClient.delete(path)
      else await apiClient.put(path, {})
      await refresh()
      setMessage(
        saved ? 'Removed from your saved jobs.' : 'Job saved to your shortlist.'
      )
      onComplete?.()
    } catch (error) {
      setErrors(apiErrors(error))
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="stack">
      <Button
        type="button"
        variant="outline"
        disabled={busy}
        onClick={choose}
        aria-label={title ? `Remove saved job: ${title}` : undefined}
      >
        {saved ? 'Remove saved job' : 'Save job'}
      </Button>
      <FormErrors errors={errors} prefix={`saved-job-${jobId}`} />
      {message && <p role="status">{message}</p>}
      {Object.keys(errors).length > 0 && (
        <Button type="button" variant="ghost" onClick={() => refresh()}>
          Refresh saved status
        </Button>
      )}
    </div>
  )
}

// see docs/CONCEPTS.md#private-shortlist-and-follow-up
export default function SavedJobButton({ jobId }) {
  const query = useApiQuery(`/jobs/${jobId}/saved/`)
  if (query.loading) return <p role="status">Loading saved status…</p>
  if (query.error)
    return <ErrorState onRetry={query.retry}>{query.error}</ErrorState>
  return <SavedJobAction jobId={jobId} saved={query.data?.saved === true} />
}

export function RemoveSavedJobButton({ job, onComplete }) {
  return (
    <SavedJobAction
      jobId={job.id}
      saved
      title={job.title}
      onComplete={onComplete}
    />
  )
}
