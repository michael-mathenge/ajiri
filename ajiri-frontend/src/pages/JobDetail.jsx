import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  CalendarDays,
  MapPin,
  ShieldCheck,
} from 'lucide-react'
import apiClient from '../api/client'
import DownloadButton from '../components/DownloadButton'
import { useApiResource } from '../hooks/useApiResource'
import {
  Badge,
  Button,
  Card,
  ErrorState,
  LoadingState,
  MatchScore,
} from '../components/ui'
import { useToast } from '../hooks/useToast'
import { dateLabel, jobType, salaryLabel } from '../lib/utils'

export default function JobDetail() {
  const { id } = useParams()
  const { data: job, loading, error, retry } = useApiResource(`/jobs/${id}/`)
  const [applying, setApplying] = useState(false)
  const [applyError, setApplyError] = useState('')
  const navigate = useNavigate()
  const toast = useToast()
  const handleApply = async () => {
    if (applying) return
    setApplying(true)
    setApplyError('')
    try {
      const response = await apiClient.post(`/jobs/${id}/apply/`)
      toast(
        response.status === 201
          ? 'Your application is ready to review'
          : 'Opening your existing application',
        'Review your documents before confirming the next step.'
      )
      navigate('/applications')
    } catch (error) {
      setApplyError(
        error.response?.data?.detail ||
          'Could not prepare your application. Please try again.'
      )
    } finally {
      setApplying(false)
    }
  }
  if (loading) return <LoadingState label="Loading job details" />
  if (error) return <ErrorState onRetry={retry}>{error}</ErrorState>
  return (
    <div className="stack page-stack">
      <Link to="/" className="inline-link">
        <ArrowLeft size={16} aria-hidden="true" />
        All opportunities
      </Link>
      <Card className="detail-heading">
        <div className="job-card-top">
          <span className="company-avatar" aria-hidden="true">
            {job.company_name.slice(0, 2).toUpperCase()}
          </span>
          <MatchScore score={job.match_score} />
        </div>
        <p className="company-name">{job.company_name}</p>
        <h1>{job.title}</h1>
        <div className="job-tags">
          <span className="icon-text muted">
            <MapPin size={17} aria-hidden="true" />
            {job.location || 'Location not listed'}
          </span>
          <Badge className="capitalize">{jobType(job.job_type)}</Badge>
          <span className="icon-text muted">
            <CalendarDays size={17} aria-hidden="true" />
            Posted {dateLabel(job.posted_at)}
          </span>
        </div>
      </Card>
      <div className="detail-layout">
        <div className="stack">
          <Card>
            <h2>About the role</h2>
            <p className="job-copy">{job.description}</p>
          </Card>
          {job.requirements && (
            <Card>
              <h2>What you’ll bring</h2>
              <p className="job-copy">{job.requirements}</p>
            </Card>
          )}
          {job.skills_required?.length > 0 && (
            <Card>
              <h2>Skills for this role</h2>
              <div className="job-tags mt-4">
                {job.skills_required.map((skill) => (
                  <Badge key={skill.id}>{skill.name}</Badge>
                ))}
              </div>
            </Card>
          )}
        </div>
        <aside className="stack apply-sidebar" aria-label="Application">
          <Card>
            <h2>Generate documents</h2>
            <p className="muted">
              Use your current profile to create a DOCX for this role.
            </p>
            <div className="stack">
              <DownloadButton
                path="/profiles/me/generate-cv/"
                filename="Ajiri_CV.docx"
              >
                Generate CV
              </DownloadButton>
              <DownloadButton
                path={`/jobs/${job.id}/generate-cover-letter/`}
                filename="Cover_Letter.docx"
              >
                Generate cover letter
              </DownloadButton>
            </div>
          </Card>
          <Card>
            <span className="eyebrow">YOUR NEXT STEP</span>
            <h2>Interested in this role?</h2>
            <p className="muted mb-6">
              Prepare your CV and cover letter, then review your application.
            </p>
            <p className="salary mb-6">{salaryLabel(job)}</p>
            <Button
              className="w-full"
              disabled={applying}
              onClick={handleApply}
            >
              {applying ? 'Preparing application…' : 'Prepare application'}
              <ArrowRight size={18} aria-hidden="true" />
            </Button>
            {applyError && (
              <p role="alert" className="error-text mt-4">
                {applyError}
              </p>
            )}
            <p className="trust-note">
              <ShieldCheck size={20} aria-hidden="true" />
              <span>Nothing is sent until you confirm.</span>
            </p>
          </Card>
          <Card>
            <p className="icon-text font-semibold">
              <Building2 size={18} aria-hidden="true" />
              Listing source
            </p>
            <p className="muted">{job.source_name || 'External job feed'}</p>
            {/^https?:\/\//i.test(job.source_url || '') && (
              <a
                href={job.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-link"
              >
                View original listing
                <span className="sr-only"> (opens in a new tab)</span>
                <ArrowRight size={16} aria-hidden="true" />
              </a>
            )}
          </Card>
        </aside>
      </div>
    </div>
  )
}
