import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import apiClient from '../api/client'

function Notifications() {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const response = await apiClient.get('/jobs/notifications/')
        setNotifications(response.data.results)
      } catch {
        setError('Failed to load notifications.')
      } finally {
        setLoading(false)
      }
    }

    fetchNotifications()
  }, [])

  const handleMarkRead = async (notificationId) => {
    try {
      const response = await apiClient.post(`/jobs/notifications/${notificationId}/mark-read/`)
      setNotifications((current) =>
        current.map((n) => (n.id === notificationId ? response.data : n))
      )
    } catch {
      setError('Failed to mark notification as read.')
    }
  }

  if (loading) {
    return <p className="status-text">Loading notifications…</p>
  }

  if (error) {
    return <p className="error-text">{error}</p>
  }

  if (notifications.length === 0) {
    return (
      <div>
        <h1>Notifications</h1>
        <p className="empty-state">No notifications yet.</p>
      </div>
    )
  }

  return (
    <div>
      <h1>Notifications</h1>
      <div className="ledger">
        {notifications.map((n) => (
          <div className={`row${n.is_read ? '' : ' row-unread'}`} key={n.id}>
            <div className="row-head">
              <Link to={`/jobs/${n.job_id}`} className="row-title">
                {n.job_title}, {n.company_name}
              </Link>
              <span className="match">{n.match_score}% match</span>
            </div>
            <p className="row-meta">{new Date(n.created_at).toLocaleString()}</p>
            {!n.is_read && (
              <button onClick={() => handleMarkRead(n.id)} className="btn btn-plain">
                Mark as read
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default Notifications
