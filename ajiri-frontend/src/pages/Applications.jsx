import { useState, useEffect } from 'react'
import apiClient, { mediaUrl } from '../api/client'

function Applications() {
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [sendingId, setSendingId] = useState(null)

  useEffect(() => {
    const fetchApplications = async () => {
      try {
        const response = await apiClient.get('/jobs/applications/')
        setApplications(response.data.results)
      } catch {
        setError('Failed to load applications.')
      } finally {
        setLoading(false)
      }
    }

    fetchApplications()
  }, [])

  const handleSend = async (applicationId) => {
    setSendingId(applicationId)
    try {
      const response = await apiClient.post(`/jobs/applications/${applicationId}/send/`)
      setApplications((current) =>
        current.map((app) => (app.id === applicationId ? response.data : app))
      )
    } catch {
      setError('Failed to send application.')
    } finally {
      setSendingId(null)
    }
  }

  if (loading) {
    return <p className="status-text">Loading applications…</p>
  }

  if (error) {
    return <p className="error-text">{error}</p>
  }

  if (applications.length === 0) {
    return (
      <div>
        <h1>My applications</h1>
        <p className="empty-state">No applications yet — go apply to a job.</p>
      </div>
    )
  }

  return (
    <div>
      <h1>My applications</h1>
      <div className="ledger">
        {applications.map((app) => (
          <div className="row" key={app.id}>
            <div className="row-head">
              <span className="row-title">
                {app.job_title}, {app.company_name}
              </span>
              {app.status === 'sent' && <span className="stamp">Sent</span>}
            </div>
            <p className="row-meta">
              {app.application_method === 'email' ? 'Applies by email' : 'Applies via employer link'}
            </p>

            {app.application_method === 'email' && app.status === 'ready_for_review' && (
              <div className="detail-block">
                <p className="row-meta">To: {app.application_email}</p>
                <p className="row-meta">Subject: {app.email_subject}</p>
                <p>{app.email_body}</p>
              </div>
            )}

            <p className="status-text">
              <a href={mediaUrl(app.generated_cv)} target="_blank" rel="noreferrer">CV</a>
              {'  ·  '}
              <a href={mediaUrl(app.generated_cover_letter)} target="_blank" rel="noreferrer">Cover letter</a>
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
              <p className="status-text">Sent {new Date(app.sent_at).toLocaleString()}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default Applications
