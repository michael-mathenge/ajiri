import { apiErrors } from '../lib/errors'
import FormErrors from '../components/FormErrors'
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
import { useApiQuery, useApiInvalidation } from '../hooks/useApiQuery'
import {
  Badge,
  Button,
  Card,
  ErrorState,
  LoadingState,
  MatchScore,
  Select,
} from '../components/ui'
import { useToast } from '../hooks/useToast'
import { dateLabel, jobType, salaryLabel } from '../lib/utils'
import { useVacancyClock, availableAt } from '../hooks/useVacancyClock'

export default function JobDetail() {
  const invalidate = useApiInvalidation()
  const { id } = useParams()
  const { data: job, loading, error, retry } = useApiQuery(`/jobs/${id}/`)
  const vacancyNow = useVacancyClock(job ? [job] : [])
  const {
    data: cv,
    loading: cvLoading,
    error: cvError,
    retry: retryCV,
  } = useApiQuery('/profiles/me/cv-versions/')
  const [selection, setSelection] = useState(null)
  const cvVersion = selection ?? cv?.approval_id ?? ''
  const [applying, setApplying] = useState(false)
  const [applyError, setApplyError] = useState({})
  const navigate = useNavigate()
  const toast = useToast()
  const handleApply = async () => {
    if (applying || !cvVersion) return
    setApplying(true)
    setApplyError({})
    try {
      const response = await apiClient.post(`/jobs/${id}/apply/`, {
        cv_version: cvVersion,
      })
      invalidate()
      toast(
        response.status === 201
          ? 'Your application is ready to review'
          : 'Opening your existing application',
        'Review your documents before confirming the next step.'
      )
      navigate('/applications')
    } catch (error) {
      setApplyError(
        apiErrors(
          error,
          'Preparation could not be confirmed. Check My applications before retrying; no automatic retry was made.'
        )
      )
    } finally {
      setApplying(false)
    }
  }
  if (loading) return <LoadingState label="Loading job details" />
  if (error) return <ErrorState onRetry={retry}>{error}</ErrorState>
  if (job && !availableAt(job, vacancyNow))
    return (
      <ErrorState onRetry={retry}>
        This job is closed or its current availability is not verified. Existing
        application documents remain in My applications.
      </ErrorState>
    )
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
        <p>Source: {job.source_name || 'Not supplied'}</p>
        <p>
          {job.publication?.closes_at
            ? `Applications close: ${new Date(job.publication.closes_at).toLocaleString()}`
            : 'Closing date not verified.'}
        </p>
        <p>
          {job.publication?.origin === 'employer'
            ? 'Employer submission reviewed by staff.'
            : 'Aggregated listing; check the original employer source.'}{' '}
          Review does not guarantee the employer’s conduct. Never pay to apply.
        </p>
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
            <span className="eyebrow">YOUR NEXT STEP</span>
            <h2>Interested in this role?</h2>
            <p className="muted mb-6">
              Choose an approved CV. We copy it exactly and draft a separate
              cover letter from your current profile. Review both before
              confirming.
            </p>
            <p className="salary mb-6">{salaryLabel(job)}</p>
            {cvLoading ? (
              <p role="status">Loading approved CV versions…</p>
            ) : cvError ? (
              <ErrorState onRetry={retryCV}>{cvError}</ErrorState>
            ) : cv?.versions?.length ? (
              <div className="field mb-6">
                <label htmlFor="application-cv">Approved CV version</label>
                <Select
                  id="application-cv"
                  value={cvVersion}
                  disabled={applying}
                  onChange={(event) => setSelection(event.target.value)}
                >
                  <option value="">Choose an approved version</option>
                  {cv.versions.map((version) => (
                    <option key={version.id} value={version.id}>
                      Revision {version.revision}
                      {version.revision === cv.revision
                        ? ' (current)'
                        : ' (earlier approved version)'}
                    </option>
                  ))}
                </Select>
                <p className="muted text-sm">
                  An existing application keeps its original documents, even if
                  you select another CV.
                </p>
                {cvVersion && (
                  <DownloadButton
                    path={`/profiles/me/cv-versions/${cvVersion}/download/`}
                    filename="Selected_CV.docx"
                  >
                    Review selected CV
                  </DownloadButton>
                )}
              </div>
            ) : (
              <p>
                No approved CV yet.{' '}
                <Link to="/cv-builder">Build and approve your CV</Link> to
                prepare a new application.
              </p>
            )}
            <p>
              <Link to="/applications">Open My applications</Link> to review an
              existing draft without replacing its documents.
            </p>
            <Button
              className="w-full"
              disabled={applying || cvLoading || Boolean(cvError) || !cvVersion}
              onClick={handleApply}
            >
              {applying ? 'Preparing application…' : 'Prepare application'}
              <ArrowRight size={18} aria-hidden="true" />
            </Button>
            <FormErrors errors={applyError} prefix="application" />
            <p className="trust-note">
              <ShieldCheck size={20} aria-hidden="true" />
              <span>Nothing is sent until you confirm.</span>
            </p>
          </Card>
          <Card>
            <h2>Review your documents</h2>
            <p className="muted">
              Your approved CV stays unchanged. The cover letter uses your
              current profile and needs a separate review.
            </p>
            <div className="stack">
              <Link to="/cv-builder">Edit and approve my CV</Link>
              <DownloadButton
                path={`/jobs/${job.id}/generate-cover-letter/`}
                filename="Cover_Letter.docx"
              >
                Generate cover letter
              </DownloadButton>
            </div>
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
                {job.publication?.origin === 'employer'
                  ? 'Open employer application page'
                  : 'View original listing'}
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
