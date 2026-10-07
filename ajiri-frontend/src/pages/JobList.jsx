import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import apiClient from '../api/client'

function JobList() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await apiClient.get('/jobs/')
        setJobs(response.data.results)
      } catch {
        setError('Failed to load jobs.')
      } finally {
        setLoading(false)
      }
    }

    fetchJobs()
  }, [])

  if (loading) {
    return <p className="status-text">Loading jobs…</p>
  }

  if (error) {
    return <p className="error-text">{error}</p>
  }

  return (
    <div>
      <h1>Job listings</h1>
      {jobs.length === 0 && <p className="empty-state">No jobs found.</p>}
      <div className="ledger">
        {jobs.map((job) => (
          <div className="row" key={job.id}>
            <div className="row-head">
              <Link to={`/jobs/${job.id}`} className="row-title">
                {job.title}
              </Link>
              {job.match_score !== null && (
                <span className="match">{job.match_score}% match</span>
              )}
            </div>
            <p className="row-meta">
              {job.company_name}, {job.location}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default JobList
