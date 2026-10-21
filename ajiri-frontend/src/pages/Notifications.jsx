import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import apiClient from '../api/client'
import { useApiQuery, useApiInvalidation } from '../hooks/useApiQuery'
import {
  Button,
  Badge,
  EmptyState,
  ErrorState,
  LoadingState,
  MatchScore,
  Pagination,
} from '../components/ui'

function Notifications() {
  const invalidate = useApiInvalidation()
  const rows = useRef({})
  const [page, setPage] = useState(1)
  const {
    data,
    loading,
    error: loadError,
    retry,
  } = useApiQuery(`/jobs/notifications/?page=${page}`)
  const [updates, setUpdates] = useState({})
  const notifications =
    data?.results.map((item) => updates[item.id] || item) || []
  const [error, setError] = useState('')
  const [pendingId, setPendingId] = useState(null)

  const handleMarkRead = async (notificationId) => {
    if (pendingId !== null) return
    setPendingId(notificationId)
    setError('')
    try {
      const response = await apiClient.post(
        `/jobs/notifications/${notificationId}/mark-read/`
      )
      invalidate()
      setUpdates((current) => ({ ...current, [notificationId]: response.data }))
      // Mark-read removes its button, so retain a useful keyboard position.
      // see docs/CONCEPTS.md#focus-after-mutations
      requestAnimationFrame(() => rows.current[notificationId]?.focus())
    } catch {
      setError('Failed to mark notification as read.')
    } finally {
      setPendingId(null)
    }
  }

  if (loading) {
    return <LoadingState label="Loading notifications" />
  }

  if (loadError) {
    return <ErrorState onRetry={retry}>{loadError}</ErrorState>
  }

  if (notifications.length === 0) {
    return (
      <div>
        <h1>Notifications</h1>
        <EmptyState
          title="You’re all caught up"
          action={
            <Button asChild>
              <Link to="/">Browse jobs</Link>
            </Button>
          }
        >
          New job-match alerts will appear here.
        </EmptyState>
      </div>
    )
  }

  return (
    <div>
      <h1>Notifications</h1>
      <p className="lead">
        Stay close to opportunities that match your skills.
      </p>
      {error && (
        <p role="alert" className="error-text">
          {error}
        </p>
      )}
      <div className="ledger">
        {notifications.map((n) => (
          <div
            className={`row${n.is_read ? '' : ' row-unread'}`}
            key={n.id}
            tabIndex={-1}
            ref={(element) => {
              rows.current[n.id] = element
            }}
          >
            <div className="row-head">
              <Link to={`/jobs/${n.job_id}`} className="row-title">
                {n.job_title}, {n.company_name}
              </Link>
              <MatchScore score={n.match_score} />
              <Badge>{n.is_read ? 'Read' : 'Unread'}</Badge>
            </div>
            <p className="row-meta">
              {new Date(n.created_at).toLocaleString()}
            </p>
            {!n.is_read && (
              <button
                onClick={() => handleMarkRead(n.id)}
                disabled={pendingId !== null}
                className="btn btn-plain"
              >
                {pendingId === n.id ? 'Marking read…' : 'Mark as read'}
              </button>
            )}
          </div>
        ))}
      </div>
      <Pagination
        page={page}
        hasNext={Boolean(data.next)}
        hasPrevious={Boolean(data.previous)}
        onChange={setPage}
      />
    </div>
  )
}

export default Notifications
