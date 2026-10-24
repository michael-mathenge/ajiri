import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import apiClient from '../api/client'
import FormErrors from '../components/FormErrors'
import {
  Button,
  Input,
  Select,
  LoadingState,
  ErrorState,
} from '../components/ui'
import { useApiQuery, useApiInvalidation } from '../hooks/useApiQuery'
import { useVacancyClock, availableAt } from '../hooks/useVacancyClock'
import { apiErrors } from '../lib/errors'

function Frequency({ name, children, value, error }) {
  return (
    <div className="field">
      <label htmlFor={name}>{children}</label>
      <Select
        id={name}
        name={name}
        defaultValue={value || 'off'}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `saved-search-${name}-error` : undefined}
      >
        <option value="off">Off</option>
        <option value="daily">Daily</option>
        <option value="weekly">Every seven days</option>
      </Select>
    </div>
  )
}

function Matches({ search }) {
  const [page, setPage] = useState(1)
  const query = useApiQuery(
    `/jobs/saved-searches/${search.id}/matches/?page=${page}`
  )
  const jobs = query.data?.results ?? []
  const now = useVacancyClock(jobs)
  if (query.loading)
    return <LoadingState label="Loading saved search matches" />
  if (query.error)
    return <ErrorState onRetry={query.retry}>{query.error}</ErrorState>
  const current = jobs.filter((job) => availableAt(job, now))
  return (
    <section className="stack" aria-label={`Matches for ${search.name}`}>
      <h2>Matches for {search.name}</h2>
      {current.length === 0 && (
        <p>
          No current matches yet. Only vacancies with current availability
          evidence appear here.
        </p>
      )}
      <ul>
        {current.map((job) => (
          <li key={job.id}>
            <Link to={`/jobs/${job.id}`}>
              {job.title} — {job.company_name}
            </Link>
          </li>
        ))}
      </ul>
      <nav className="flex flex-wrap gap-3" aria-label="Match pages">
        <Button
          variant="outline"
          disabled={!query.data?.previous}
          onClick={() => setPage(page - 1)}
        >
          Previous matches
        </Button>
        <span>Page {page}</span>
        <Button
          variant="outline"
          disabled={!query.data?.next}
          onClick={() => setPage(page + 1)}
        >
          Next matches
        </Button>
      </nav>
    </section>
  )
}

export default function SavedSearches() {
  const [params] = useSearchParams()
  const [page, setPage] = useState(1)
  const query = useApiQuery(`/jobs/saved-searches/?page=${page}`)
  const refresh = useApiInvalidation()
  const [editing, setEditing] = useState(null)
  const [selected, setSelected] = useState(null)
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const items = query.data?.results ?? []

  async function save(event) {
    event.preventDefault()
    if (busy) return
    const form = event.currentTarget
    const values = Object.fromEntries(new FormData(form))
    setBusy(true)
    setErrors({})
    setMessage('')
    try {
      if (editing)
        await apiClient.patch(`/jobs/saved-searches/${editing.id}/`, {
          ...values,
          expected_revision: editing.revision,
        })
      else await apiClient.post('/jobs/saved-searches/', values)
      setEditing(null)
      setSelected(null)
      setPage(1)
      form.reset()
      setMessage(
        'Search saved. Saving a search does not authorize or send email.'
      )
      await refresh()
    } catch (error) {
      setErrors(apiErrors(error))
    } finally {
      setBusy(false)
    }
  }

  async function remove(item) {
    if (busy) return
    setBusy(true)
    setErrors({})
    setMessage('')
    try {
      await apiClient.delete(`/jobs/saved-searches/${item.id}/`)
      setEditing(null)
      setSelected(null)
      setPage(1)
      setMessage('Saved search removed. Its future checks are stopped.')
      await refresh()
    } catch (error) {
      setErrors(apiErrors(error))
    } finally {
      setBusy(false)
    }
  }

  if (query.loading) return <LoadingState label="Loading saved searches" />
  if (query.error)
    return <ErrorState onRetry={query.retry}>{query.error}</ErrorState>
  return (
    <section className="stack">
      <h1>Saved searches</h1>
      <p>
        Save up to ten searches for free. Choose each channel separately. In-app
        checks run with the matching sweep and may be delayed; each window keeps
        up to 50 current matches.
      </p>
      <p>
        Email sending is currently disabled. Saving a frequency does not grant
        consent. Verification and your separate{' '}
        <Link to="/profile">Profile email choice</Link> are also required. Your
        Profile in-app choice applies to new in-app results.
      </p>
      <FormErrors
        errors={errors}
        prefix="saved-search"
        fieldLabels={{
          q: 'Job keywords',
          expected_revision: 'Search revision',
          name: 'Search name',
          in_app_frequency: 'In-app frequency',
        }}
      />
      {message && <p role="status">{message}</p>}
      <form
        className="stack"
        key={editing ? `${editing.id}-${editing.revision}` : 'new'}
        onSubmit={save}
      >
        <h2>{editing ? 'Edit saved search' : 'Save a search'}</h2>
        <div className="field">
          <label htmlFor="saved-name">Search name</label>
          <Input
            id="saved-name"
            name="name"
            required
            maxLength={80}
            defaultValue={editing?.name || ''}
            aria-invalid={Boolean(errors.name)}
            aria-describedby={
              errors.name ? 'saved-search-name-error' : undefined
            }
          />
        </div>
        <div className="field">
          <label htmlFor="saved-q">Job keywords</label>
          <Input
            id="saved-q"
            name="q"
            maxLength={255}
            defaultValue={editing?.q ?? params.get('q') ?? ''}
            aria-invalid={Boolean(errors.q)}
            aria-describedby={errors.q ? 'saved-search-q-error' : undefined}
          />
        </div>
        <div className="field">
          <label htmlFor="saved-location">Location</label>
          <Input
            id="saved-location"
            name="location"
            maxLength={255}
            defaultValue={editing?.location ?? params.get('location') ?? ''}
            aria-invalid={Boolean(errors.location)}
            aria-describedby={
              errors.location ? 'saved-search-location-error' : undefined
            }
          />
        </div>
        <div className="field">
          <label htmlFor="saved-type">Job type</label>
          <Select
            id="saved-type"
            name="job_type"
            defaultValue={editing?.job_type ?? params.get('job_type') ?? ''}
            aria-invalid={Boolean(errors.job_type)}
            aria-describedby={
              errors.job_type ? 'saved-search-job_type-error' : undefined
            }
          >
            <option value="">All job types</option>
            <option value="full_time">Full time</option>
            <option value="part_time">Part time</option>
            <option value="contract">Contract</option>
            <option value="internship">Internship</option>
          </Select>
        </div>
        <Frequency
          name="in_app_frequency"
          value={editing?.in_app_frequency}
          error={errors.in_app_frequency}
        >
          In-app frequency
        </Frequency>
        <Frequency
          name="email_frequency"
          value={editing?.email_frequency}
          error={errors.email_frequency}
        >
          Email frequency (sending disabled)
        </Frequency>
        <Button disabled={busy} type="submit">
          {editing ? 'Save changes' : 'Save search'}
        </Button>
        {editing && (
          <Button
            type="button"
            variant="outline"
            onClick={() => setEditing(null)}
          >
            Cancel editing
          </Button>
        )}
      </form>
      <h2>Your searches</h2>
      {items.length === 0 && <p>No saved searches yet.</p>}
      <ul className="stack">
        {items.map((item) => (
          <li key={item.id} className="stack">
            <h3>{item.name}</h3>
            <p>
              In-app: {item.in_app_frequency}. Email preference:{' '}
              {item.email_frequency}; sending disabled.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button
                variant="outline"
                disabled={busy}
                onClick={() => {
                  setEditing(item)
                  setErrors({})
                  setMessage('')
                }}
              >
                Edit {item.name}
              </Button>
              <Button variant="outline" onClick={() => setSelected(item)}>
                Show matches for {item.name}
              </Button>
              <Button
                variant="outline"
                disabled={busy}
                onClick={() => remove(item)}
              >
                Remove {item.name}
              </Button>
            </div>
          </li>
        ))}
      </ul>
      <nav className="flex flex-wrap gap-3" aria-label="Saved search pages">
        <Button
          variant="outline"
          disabled={!query.data?.previous}
          onClick={() => setPage(page - 1)}
        >
          Previous searches
        </Button>
        <span>Page {page}</span>
        <Button
          variant="outline"
          disabled={!query.data?.next}
          onClick={() => setPage(page + 1)}
        >
          Next searches
        </Button>
      </nav>
      {selected && (
        <Matches
          key={`${selected.id}-${selected.revision}`}
          search={selected}
        />
      )}
    </section>
  )
}
