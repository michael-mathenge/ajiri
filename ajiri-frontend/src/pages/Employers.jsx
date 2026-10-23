import { useState } from 'react'
import apiClient from '../api/client'
import FormErrors from '../components/FormErrors'
import { apiErrors } from '../lib/errors'
import { useApiQuery, useApiInvalidation } from '../hooks/useApiQuery'
import {
  LoadingState,
  ErrorState,
  Input,
  Select,
  Textarea,
  Button,
} from '../components/ui'

// Employer review is independent of account email verification.
// see docs/CONCEPTS.md#job-freshness-evidence
export default function Employers() {
  const [orgPage, setOrgPage] = useState(1)
  const [draftPage, setDraftPage] = useState(1)
  const orgQuery = useApiQuery(`/jobs/employers/organisations/?page=${orgPage}`)
  const draftQuery = useApiQuery(`/jobs/employers/drafts/?page=${draftPage}`)
  const load = useApiInvalidation()
  const organisations = orgQuery.data?.results ?? orgQuery.data ?? []
  const drafts = draftQuery.data?.results ?? draftQuery.data ?? []
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  function failure(error) {
    setErrors(apiErrors(error))
  }
  async function submit(event, kind) {
    event.preventDefault()
    if (busy) return
    const form = event.currentTarget
    const values = Object.fromEntries(new FormData(form))
    if (kind === 'drafts') {
      values.organisation = Number(values.organisation)
      // The picker is local time; transport an explicit timezone-aware instant.
      values.closes_at = new Date(values.closes_at).toISOString()
    }
    setBusy(true)
    setErrors({})
    setMessage('')
    try {
      await apiClient.post(`/jobs/employers/${kind}/`, values)
      form.reset()
      if (kind === 'organisations') setOrgPage(1)
      else setDraftPage(1)
      setMessage('Submitted for staff review. This job is not published yet.')
      await load()
    } catch (error) {
      failure(error)
    } finally {
      setBusy(false)
    }
  }
  async function withdraw(id) {
    setBusy(true)
    setErrors({})
    try {
      await apiClient.post(`/jobs/employers/drafts/${id}/withdraw/`, {})
      await load()
    } catch (error) {
      failure(error)
    } finally {
      setBusy(false)
    }
  }
  if (orgQuery.loading || draftQuery.loading)
    return <LoadingState label="Loading employer workspace" />
  if (orgQuery.error || draftQuery.error)
    return (
      <ErrorState
        onRetry={() => {
          orgQuery.retry()
          draftQuery.retry()
        }}
      >
        {orgQuery.error || draftQuery.error}
      </ErrorState>
    )
  return (
    <section className="stack">
      <h1>Post a job</h1>
      <Button variant="outline" onClick={() => load()}>
        Refresh review status
      </Button>
      <p>
        Verify your account email, then submit your organisation and vacancy for
        staff review. A closing date is required. Review is not a guarantee of
        an employer’s conduct.
      </p>
      <p>
        Job seekers never pay Ajiri to apply. Do not request application,
        registration or processing fees.
      </p>
      <FormErrors errors={errors} prefix="employer" />
      {message && <p role="status">{message}</p>}
      <form
        className="stack"
        onSubmit={(event) => submit(event, 'organisations')}
      >
        <h2>Your organisation</h2>
        <label className="stack gap-2">
          Organisation name
          <Input name="name" required maxLength={255} />
        </label>
        <label className="stack gap-2">
          Official website
          <Input name="website" type="url" required />
        </label>
        <Button disabled={busy} type="submit">
          Submit organisation for review
        </Button>
      </form>
      <ul>
        {organisations.map((org) => (
          <li key={org.id}>
            {org.name}: {org.status}
          </li>
        ))}
      </ul>
      {organisations.length > 0 && (
        <nav aria-label="Organisation pages" className="flex gap-2">
          <Button
            variant="outline"
            disabled={!orgQuery.data?.previous}
            onClick={() => setOrgPage(orgPage - 1)}
          >
            Previous organisations
          </Button>
          <span>Page {orgPage}</span>
          <Button
            variant="outline"
            disabled={!orgQuery.data?.next}
            onClick={() => setOrgPage(orgPage + 1)}
          >
            Next organisations
          </Button>
        </nav>
      )}
      {organisations.length > 0 && (
        <form className="stack" onSubmit={(event) => submit(event, 'drafts')}>
          <h2>New vacancy</h2>
          <label className="stack gap-2">
            Organisation
            <Select name="organisation" required>
              {organisations.map((org) => (
                <option value={org.id} key={org.id}>
                  {org.name}
                </option>
              ))}
            </Select>
          </label>
          <label className="stack gap-2">
            Job title
            <Input name="title" required maxLength={255} />
          </label>
          <label className="stack gap-2">
            Location (include country)
            <Input name="location" required maxLength={255} />
          </label>
          <label className="stack gap-2">
            Description
            <Textarea name="description" required maxLength={12000} />
          </label>
          <label className="stack gap-2">
            Requirements
            <Textarea name="requirements" maxLength={6000} />
          </label>
          <label className="stack gap-2">
            Job type
            <Select name="job_type">
              <option value="full_time">Full-time</option>
              <option value="part_time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
            </Select>
          </label>
          <label className="stack gap-2">
            Official application URL
            <Input name="application_url" type="url" required />
          </label>
          <label className="stack gap-2">
            Closing date and time (your local time)
            <Input name="closes_at" type="datetime-local" required />
          </label>
          <Button type="submit" disabled={busy}>
            Submit vacancy for review
          </Button>
        </form>
      )}
      <h2>Your submissions</h2>
      {drafts.length === 0 && <p>No vacancies submitted.</p>}
      <ul>
        {drafts.map((draft) => (
          <li key={draft.id}>
            <h3>{draft.title}</h3>
            <p>
              {draft.status} · Closes{' '}
              {new Date(draft.closes_at).toLocaleString()}
            </p>
            {['pending', 'published'].includes(draft.status) && (
              <Button disabled={busy} onClick={() => withdraw(draft.id)}>
                Withdraw {draft.title}
              </Button>
            )}
          </li>
        ))}
      </ul>
      <nav aria-label="Submission pages" className="flex gap-2">
        <Button
          variant="outline"
          disabled={!draftQuery.data?.previous}
          onClick={() => setDraftPage(draftPage - 1)}
        >
          Previous submissions
        </Button>
        <span>Page {draftPage}</span>
        <Button
          variant="outline"
          disabled={!draftQuery.data?.next}
          onClick={() => setDraftPage(draftPage + 1)}
        >
          Next submissions
        </Button>
      </nav>
    </section>
  )
}
