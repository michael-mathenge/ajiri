import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import apiClient from '../api/client'

function JobDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [job, setJob] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [applying, setApplying] = useState(false)

  useEffect(() => {
    const fetchJob = async () => {
      try {
        const response = await apiClient.get(`/jobs/${id}/`)
        setJob(response.data)
      } catch {
        setError('Failed to load this job.')
      } finally {
        setLoading(false)
      }
    }

    fetchJob()
  }, [id])

  const handleApply = async () => {
    setApplying(true)
    try {
      await apiClient.post(`/jobs/${id}/apply/`)
      navigate('/applications')
    } catch {
      setError('Failed to apply. Please try again.')
      setApplying(false)
    }
  }

  if (loading) {
    return <p className="status-text">Loading job…</p>
  }

  if (error) {
    return <p className="error-text">{error}</p>
  }

  return (
    <div>
      <h1>{job.title}</h1>
      <p className="row-meta">
        {job.company_name}, {job.location} — {job.job_type.replace('_', ' ')}
      </p>

      {job.is_salary_negotiable ? (
        <p className="status-text">Salary: to be discussed during the interview process</p>
      ) : (
        (job.salary_min || job.salary_max) && (
          <p className="status-text">
            Salary: KES {job.salary_min} – {job.salary_max}
          </p>
        )
      )}

      {job.match_score !== null && (
        <p className="match">{job.match_score}% match</p>
      )}

      <div className="detail-block">
        <h2>Description</h2>
        <p>{job.description}</p>
      </div>

      {job.requirements && (
        <div className="detail-block">
          <h2>Requirements</h2>
          <p>{job.requirements}</p>
        </div>
      )}

      <button onClick={handleApply} disabled={applying} className="btn btn-primary">
        {applying ? 'Applying…' : 'Apply'}
      </button>
    </div>
  )
}

export default JobDetail
