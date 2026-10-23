import { useState } from 'react'
import apiClient from '../api/client'
import FormErrors from '../components/FormErrors'
import { apiErrors } from '../lib/errors'
import { useApiQuery, useApiInvalidation } from '../hooks/useApiQuery'
import { LoadingState, ErrorState, Select, Textarea, Button } from '../components/ui'

export default function EmployerReview() {
  const query = useApiQuery('/jobs/employers/review-queue/')
  const queue = query.data ?? { organisations: [], drafts: [] }
  const load = useApiInvalidation()
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  async function review(event, kind, item) {
    event.preventDefault()
    if (busy) return
    const values = Object.fromEntries(new FormData(event.currentTarget))
    setBusy(true)
    setErrors({})
    try {
      await apiClient.post(`/jobs/employers/${kind}/${item.id}/review/`, {
        approve: values.decision === 'approve',
        reason: values.reason,
        ...(kind === 'drafts' ? { revision: item.revision } : {}),
      })
      await load()
    } catch (error) {
      setErrors(apiErrors(error))
    } finally {
      setBusy(false)
    }
  }
  if (query.loading) return <LoadingState label="Loading staff review queue" />
  if (query.error) return <ErrorState onRetry={query.retry}>{query.error}</ErrorState>
  return (
    <section className="stack">
      <h1>Staff vacancy review</h1>
      <p>
        Check the official employer source, authority to advertise, application
        process, deadline and absence of applicant fees. Record evidence and a
        reason. Account email verification alone is insufficient. Do not approve
        your own organisation or listing.
      </p>
      <FormErrors errors={errors} prefix="review" />
      {['organisations', 'drafts'].map((kind) => (
        <section className="stack" key={kind}>
          <h2>{kind === 'organisations' ? 'Organisations' : 'Vacancies'}</h2>
          {queue[kind].length === 0 && <p>No items awaiting review.</p>}
          {queue[kind].map((item) => (
            <form
              className="stack"
              key={item.id}
              onSubmit={(event) => review(event, kind, item)}
            >
              <h3>{item.name || item.title}</h3>
              {kind === 'organisations' ? (
                <p>Official website: {item.website}</p>
              ) : (
                <>
                  <p>
                    Organisation ID: {item.organisation} · Revision{' '}
                    {item.revision}
                  </p>
                  <p>
                    {item.location} · Closes{' '}
                    {new Date(item.closes_at).toLocaleString()}
                  </p>
                  <p>{item.description}</p>
                  <p>{item.requirements}</p>
                  <p>Application URL: {item.application_url}</p>
                </>
              )}
              <label className="stack gap-2">
                Decision
                <Select name="decision" required defaultValue="">
                  <option value="" disabled>
                    Choose a decision
                  </option>
                  <option value="reject">Reject</option>
                  <option value="approve">
                    Approve after checking evidence
                  </option>
                </Select>
              </label>
              <label className="stack gap-2">
                Review reason and evidence
                <Textarea name="reason" required maxLength={2000} />
              </label>
              <Button disabled={busy} type="submit">
                Record review of {item.name || item.title}
              </Button>
            </form>
          ))}
        </section>
      ))}
    </section>
  )
}
