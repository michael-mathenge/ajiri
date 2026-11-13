import { useState } from 'react'
import apiClient from '../api/client'
import { apiErrors } from '../lib/errors'
import { useApiInvalidation } from '../hooks/useApiQuery'
import { Button } from './ui'
import FormErrors from './FormErrors'

// see docs/CONCEPTS.md#owner-recommendation-choices
export default function RecommendationAction({
  job,
  revision,
  restore = false,
}) {
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState({})
  const [refreshRequired, setRefreshRequired] = useState(false)
  const [resolvedRevision, setResolvedRevision] = useState(null)
  const refresh = useApiInvalidation()
  async function choose() {
    if (busy || refreshRequired) return
    setBusy(true)
    setErrors({})
    try {
      await apiClient.patch(`/jobs/${job.id}/suggestion-choice/`, {
        expected_revision: resolvedRevision ?? revision,
        dismissed: !restore,
      })
      await refresh()
    } catch (error) {
      setErrors(apiErrors(error))
      setRefreshRequired(true)
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="stack">
      <Button
        type="button"
        variant="outline"
        disabled={busy || refreshRequired}
        onClick={choose}
        aria-label={`${restore ? 'Restore' : 'Dismiss'} suggestion: ${job.title}`}
      >
        {restore ? 'Restore suggestion' : 'Dismiss suggestion'}
      </Button>
      <FormErrors errors={errors} prefix={`suggestion-${job.id}`} />
      {refreshRequired && (
        <Button
          type="button"
          variant="ghost"
          disabled={busy}
          onClick={async () => {
            setBusy(true)
            try {
              // Read the owner's current revision before enabling another explicit choice.
              const response = await apiClient.get(
                `/jobs/${job.id}/suggestion-choice/`
              )
              setResolvedRevision(response.data.revision)
              await refresh()
              setErrors({})
              setRefreshRequired(false)
            } catch (error) {
              setErrors(apiErrors(error))
            } finally {
              setBusy(false)
            }
          }}
        >
          Refresh suggestions before trying again
        </Button>
      )}
    </div>
  )
}
