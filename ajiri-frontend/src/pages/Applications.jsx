import { useState } from 'react'
import { Link } from 'react-router-dom'
import apiClient, { mediaUrl } from '../api/client'
import { useApiResource } from '../hooks/useApiResource'
import {
  ApplicationStatus,
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  Pagination,
} from '../components/ui'

function Applications() {
  const [page, setPage] = useState(1)
  const {
    data,
    loading,
    error: loadError,
    retry,
  } = useApiResource(`/jobs/applications/?page=${page}`)
  const [updates, setUpdates] = useState({})
  const applications = data?.results.map((app) => updates[app.id] || app) || []
  const [error, setError] = useState('')
  const [sendingId, setSendingId] = useState(null)

  const handleSend = async (applicationId) => {
    setSendingId(applicationId)
    setError('')
    try {
      const response = await apiClient.post(
        `/jobs/applications/${applicationId}/send/`
      )
      setUpdates((current) => ({ ...current, [applicationId]: response.data }))
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          'Failed to send application. Please try again.'
      )
    } finally {
      setSendingId(null)
    }
  }

  if (loading) {
    return <LoadingState label="Loading applications" />
  }

  if (loadError) {
    return <ErrorState onRetry={retry}>{loadError}</ErrorState>
  }

  if (applications.length === 0) {
    return (
      <div>
        <h1>My applications</h1>
        <EmptyState
          title="Your next step starts with a job"
          action={
            <Button asChild>
              <Link to="/">Browse jobs</Link>
            </Button>
          }
        >
          Your applications will appear here after you prepare one.
        </EmptyState>
      </div>
    )
  }

  return (
    <div>
      <h1>My applications</h1>
      <p className="lead">Review your documents and choose your next step.</p>
      {error && (
        <p role="alert" className="error-text">
          {error}
        </p>
      )}
      <div className="ledger">
        {applications.map((app) => (
          <div className="row" key={app.id}>
            <div className="row-head">
              <span className="row-title">
                {app.job_title}, {app.company_name}
              </span>
              <ApplicationStatus status={app.status} />
            </div>
            <p className="row-meta">
              {app.application_method === 'email'
                ? 'Applies by email'
                : 'Applies via employer link'}
            </p>

            {app.application_method === 'email' &&
              app.status === 'ready_for_review' && (
                <div className="detail-block">
                  <p className="row-meta">To: {app.application_email}</p>
                  <p className="row-meta">Subject: {app.email_subject}</p>
                  <p>{app.email_body}</p>
                </div>
              )}

            <p className="status-text">
              {app.generated_cv && (
                <a
                  href={mediaUrl(app.generated_cv)}
                  target="_blank"
                  rel="noreferrer"
                >
                  CV
                </a>
              )}
              {'  ·  '}
              {app.generated_cover_letter && (
                <a
                  href={mediaUrl(app.generated_cover_letter)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Cover letter
                </a>
              )}
            </p>

            {app.status === 'ready_for_review' && (
              <button
                onClick={() => handleSend(app.id)}
                disabled={sendingId === app.id}
                className="btn btn-primary"
              >
                {sendingId === app.id ? 'Sending…' : 'Send application'}
              </button>
            )}

            {app.status === 'sent' && (
              <p className="status-text">
                Sent {new Date(app.sent_at).toLocaleString()}
              </p>
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

export default Applications
