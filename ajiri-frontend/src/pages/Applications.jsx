import Dialog from '../components/Dialog'
import { rateLimitMessage } from '../lib/errors'
import { useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import apiClient from '../api/client'
import DownloadButton from '../components/DownloadButton'
import ApplicationPackageEditor from '../components/ApplicationPackageEditor'
import ApplicationProgress from '../components/ApplicationProgress'
import { useApiQuery, useApiInvalidation } from '../hooks/useApiQuery'
import {
  ApplicationStatus,
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  Pagination,
} from '../components/ui'

export function ApplicationRow({ application: app, onUpdate }) {
  const invalidate = useApiInvalidation()
  const heading = useRef(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [reviewed, setReviewed] = useState(false)
  const [opened, setOpened] = useState(false)
  const [dismissOpen, setDismissOpen] = useState(false)
  const email = app.application_method === 'email'
  const receiptBadge =
    {
      accepted: 'Provider accepted',
      unknown: 'Outcome uncertain',
      reserved: 'Awaiting reconciliation',
      definite_failure: 'Attempt failed',
      user_report: 'Reported submitted',
      unverified_record: 'Unverified email record',
    }[app.delivery_evidence?.kind] ||
    (email ? 'Check email receipt' : 'Reported submitted')
  const ready = app.status === 'ready_for_review'
  const dismissible = ['draft', 'ready_for_review'].includes(app.status)
  const employerUrl = /^https?:\/\//i.test(app.employer_url || '')
    ? app.employer_url
    : null
  // The server enforces state transitions too; approval here makes intent explicit.
  // see docs/CONCEPTS.md#explicit-application-confirmation
  const act = async (action) => {
    if (busy) return
    setBusy(true)
    setError('')
    try {
      const { data } = await apiClient.post(
        `/jobs/applications/${app.id}/${action}/`
      )
      invalidate()
      onUpdate(data)
      setDismissOpen(false)
      // Sending or dismissing removes the focused action; return to its application.
      // see docs/CONCEPTS.md#focus-after-mutations
      requestAnimationFrame(() => heading.current?.focus())
    } catch (error) {
      setError(
        (error.response?.status === 429
          ? rateLimitMessage(error)
          : error.response?.data?.detail) ||
          'Could not update this application. Please try again.'
      )
    } finally {
      setBusy(false)
    }
  }
  return (
    <Card className="application-card">
      <div className="row-head">
        <h2 tabIndex={-1} ref={heading}>
          {app.job_title}, {app.company_name}
        </h2>
        {app.status === 'sent' ? (
          <Badge>{receiptBadge}</Badge>
        ) : (
          <ApplicationStatus status={app.status} />
        )}
      </div>
      <p className="muted">
        {email ? 'Apply by email' : 'Apply on the employer’s website'}
      </p>
      <details className="review-details">
        <summary>Review application</summary>
        <div className="stack mt-4">
          <ApplicationPackageEditor
            applicationId={app.id}
            readOnly={!dismissible}
          />
          <p>
            Original application documents (saving a new package does not
            replace these):
          </p>
          <div className="action-group">
            {app.generated_cv && (
              <DownloadButton
                path={`/jobs/applications/${app.id}/documents/cv/`}
                filename="Application_CV.docx"
              >
                Download CV
              </DownloadButton>
            )}
            {app.generated_cover_letter && (
              <DownloadButton
                path={`/jobs/applications/${app.id}/documents/cover-letter/`}
                filename="Application_Cover_Letter.docx"
              >
                Download cover letter
              </DownloadButton>
            )}
          </div>
          {email && (
            <div className="detail-block">
              <p>
                <strong>To:</strong> {app.application_email}
              </p>
              <p>
                <strong>Subject:</strong> {app.email_subject}
              </p>
              <p className="job-copy">
                {app.email_body || 'No email draft is available.'}
              </p>
            </div>
          )}
          {ready && email && (
            <p>
              Document approval alone never sends an email. Review the separate
              email permission controls in the approved package.
            </p>
          )}
          {ready && !email && (
            <>
              {!email && (
                <>
                  <p>
                    Ajiri does not submit this application for you. Open the
                    employer’s listing, follow its instructions and submit your
                    application there.
                  </p>
                  {employerUrl ? (
                    <a
                      className="btn btn-outline"
                      href={employerUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => setOpened(true)}
                    >
                      Open employer listing
                      <span className="sr-only"> (opens in a new tab)</span>
                    </a>
                  ) : (
                    <p role="alert" className="error-text">
                      The employer link is unavailable. Open the job listing for
                      source details.
                    </p>
                  )}
                </>
              )}
              <label className="check-field">
                <input
                  type="checkbox"
                  checked={reviewed}
                  disabled={busy || (!email && !opened)}
                  onChange={(event) => setReviewed(event.target.checked)}
                />
                {email
                  ? 'I reviewed the documents and email, and approve sending.'
                  : 'I submitted my application on the employer’s website.'}
              </label>
              <Button
                disabled={busy || !reviewed || (!email && !employerUrl)}
                onClick={() => act('send')}
              >
                {busy
                  ? 'Updating…'
                  : email
                    ? 'Send application'
                    : 'Confirm external submission'}
              </Button>
            </>
          )}
        </div>
      </details>
      {app.status === 'sent' && (
        <p className="status-text">
          {app.delivery_evidence?.label ||
            (email
              ? 'Email record; check delivery receipt'
              : 'External submission reported by you')}
          {app.sent_at
            ? ` ${new Date(app.sent_at).toLocaleString('en-KE')}`
            : ''}
        </p>
      )}
      {app.status !== 'sent' &&
        app.delivery_evidence &&
        ['accepted', 'unknown', 'reserved', 'definite_failure'].includes(
          app.delivery_evidence.kind
        ) && <p className="status-text">{app.delivery_evidence.label}</p>}
      <details className="review-details">
        <summary>Track my progress</summary>
        <div className="mt-4">
          <ApplicationProgress application={app} onUpdate={onUpdate} />
        </div>
      </details>
      {app.status === 'dismissed' && (
        <div className="stack">
          <p className="status-text">
            Dismissed. Restore the saved documents to review them again.
            Restoring does not send an application or renew sending permission.
          </p>
          <Button disabled={busy} onClick={() => act('restore')}>
            {busy ? 'Restoring…' : 'Restore for review'}
          </Button>
        </div>
      )}
      {dismissible && (
        <Dialog
          open={dismissOpen}
          onOpenChange={setDismissOpen}
          trigger={<Button variant="ghost">Dismiss application</Button>}
          title="Dismiss this application?"
          description="This keeps it in your history and prevents sending. It does not delete your documents."
        >
          <div className="action-group">
            <Button
              variant="outline"
              disabled={busy}
              onClick={() => setDismissOpen(false)}
            >
              Keep application
            </Button>
            <Button disabled={busy} onClick={() => act('dismiss')}>
              {busy ? 'Dismissing…' : 'Confirm dismissal'}
            </Button>
          </div>
          {error && (
            <p role="alert" className="error-text">
              {error}
            </p>
          )}
        </Dialog>
      )}
      {error && !dismissOpen && (
        <p role="alert" className="error-text">
          {error}
        </p>
      )}
    </Card>
  )
}

export default function Applications() {
  const [page, setPage] = useState(1)
  const client = useQueryClient()
  const url = `/jobs/applications/?page=${page}`
  const { data, loading, error, retry } = useApiQuery(url)
  if (loading) return <LoadingState label="Loading applications" />
  if (error) return <ErrorState onRetry={retry}>{error}</ErrorState>
  return (
    <div className="stack">
      <div>
        <h1>My applications</h1>
        <p className="lead">
          Review each draft before you send or confirm a submission.
        </p>
      </div>
      {!data.results.length ? (
        <EmptyState
          title="Your next step starts with a job"
          action={
            <Button asChild>
              <Link to="/">Browse jobs</Link>
            </Button>
          }
        >
          Prepared applications will appear here.
        </EmptyState>
      ) : (
        <>
          {data.results.map((item) => (
            <ApplicationRow
              key={item.id}
              application={item}
              onUpdate={(updated) =>
                client.setQueryData(['api', url], (current) =>
                  current
                    ? {
                        ...current,
                        results: current.results.map((row) =>
                          row.id === updated.id ? updated : row
                        ),
                      }
                    : current
                )
              }
            />
          ))}
          <Pagination
            page={page}
            hasNext={Boolean(data.next)}
            hasPrevious={Boolean(data.previous)}
            onChange={setPage}
          />
        </>
      )}
    </div>
  )
}
