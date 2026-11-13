import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useApiQuery } from '../hooks/useApiQuery'
import { RemoveSavedJobButton } from '../components/SavedJobButton'
import { LoadingState, ErrorState, Card, Pagination } from '../components/ui'

export default function SavedJobs() {
  const [page, setPage] = useState(1)
  const heading = useRef(null)
  const query = useApiQuery(`/jobs/saved/?page=${page}`)
  const rows = query.data?.results ?? []
  return (
    <section className="stack page-stack">
      <h1 ref={heading} tabIndex={-1}>
        Saved jobs
      </h1>
      <p>
        Your private shortlist. Saving keeps a reference, not a guarantee of
        availability or a submitted application.
      </p>
      <Link className="inline-link" to="/">
        Browse jobs
      </Link>
      {query.loading ? (
        <LoadingState label="Loading saved jobs" />
      ) : query.error ? (
        <ErrorState onRetry={query.retry}>{query.error}</ErrorState>
      ) : (
        <>
          {rows.length === 0 && (
            <p>No saved jobs yet. Open a job and choose Save job.</p>
          )}
          {rows.map(
            ({ job, saved_at: savedAt, reference_url: referenceUrl }) => (
              <Card key={job.id} className="stack">
                <h2>
                  {job.title}, {job.company_name}
                </h2>
                <p>Saved by you {new Date(savedAt).toLocaleString('en-KE')}</p>
                <p>
                  {job.can_apply
                    ? 'Current availability evidence is recorded. Check the closing date before applying.'
                    : 'Reference only: current availability is not verified. Saving does not make this role eligible for applications or alerts.'}
                </p>
                {job.can_apply && (
                  <Link className="inline-link" to={`/jobs/${job.id}`}>
                    View current job
                  </Link>
                )}
                {referenceUrl && (
                  <a
                    className="inline-link"
                    href={referenceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open saved source reference (opens in a new tab)
                  </a>
                )}
                <RemoveSavedJobButton
                  job={job}
                  onComplete={() =>
                    requestAnimationFrame(() => heading.current?.focus())
                  }
                />
              </Card>
            )
          )}
          <Pagination
            page={page}
            hasNext={Boolean(query.data?.next)}
            hasPrevious={Boolean(query.data?.previous)}
            onChange={setPage}
          />
        </>
      )}
    </section>
  )
}
