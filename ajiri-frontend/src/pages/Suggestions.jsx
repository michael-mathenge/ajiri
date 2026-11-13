import { useState } from 'react'
import JobList from './JobList'
import RecommendationAction from '../components/RecommendationAction'
import { useApiQuery } from '../hooks/useApiQuery'
import { Button, LoadingState, ErrorState } from '../components/ui'

export default function Suggestions() {
  const [page, setPage] = useState(1)
  const query = useApiQuery(`/jobs/suggestions/dismissed/?page=${page}`)
  const rows = query.data?.results ?? []
  return (
    <div className="stack page-stack">
      <JobList suggestions />
      <section className="stack" aria-label="Dismissed suggestions">
        <h2>Dismissed suggestions</h2>
        <p>
          Dismissal affects this suggestions view. Browse jobs and your
          applications remain available. Saved searches and alerts keep their
          separate settings. Restore a role to allow it back here if it is still
          current.
        </p>
        {query.loading ? (
          <LoadingState label="Loading dismissed suggestions" />
        ) : query.error ? (
          <ErrorState onRetry={query.retry}>{query.error}</ErrorState>
        ) : (
          <>
            {rows.length === 0 && <p>No dismissed suggestions.</p>}
            <ul className="stack">
              {rows.map((row) => (
                <li className="stack" key={row.job.id}>
                  <h3>
                    {row.job.title} — {row.job.company_name}
                  </h3>
                  {!row.job.can_apply && (
                    <p>Current availability is not verified.</p>
                  )}
                  <RecommendationAction
                    job={row.job}
                    revision={row.revision}
                    restore
                  />
                </li>
              ))}
            </ul>
            <nav
              aria-label="Dismissed suggestion pages"
              className="flex flex-wrap gap-3"
            >
              <Button
                variant="outline"
                disabled={!query.data?.previous}
                onClick={() => setPage(page - 1)}
              >
                Previous dismissed suggestions
              </Button>
              <span>Page {page}</span>
              <Button
                variant="outline"
                disabled={!query.data?.next}
                onClick={() => setPage(page + 1)}
              >
                Next dismissed suggestions
              </Button>
            </nav>
          </>
        )}
      </section>
    </div>
  )
}
