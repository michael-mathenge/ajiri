import { useEffect, useId, useRef, useState } from 'react'
import apiClient from '../api/client'
import { useApiInvalidation } from '../hooks/useApiQuery'
import { apiErrors } from '../lib/errors'
import DownloadButton from './DownloadButton'
import FormErrors from './FormErrors'
import { Button } from './ui'
import ApplicationSendPanel from './ApplicationSendPanel'

function StoredDocument({ title, paragraphs }) {
  return (
    <section className="stack" aria-label={title}>
      <h4>{title}</h4>
      {paragraphs.map((row, index) => {
        if (row.style === 'Title') return <h5 key={index}>{row.text}</h5>
        if (row.style === 'Heading 1') return <h5 key={index}>{row.text}</h5>
        if (row.style.startsWith('Heading '))
          return <h6 key={index}>{row.text}</h6>
        if (row.style.startsWith('List Bullet'))
          return (
            <ul key={index}>
              <li>{row.text}</li>
            </ul>
          )
        return (
          <p key={index} className="job-copy">
            {row.text || '\u00a0'}
          </p>
        )
      })}
    </section>
  )
}

// A working edit never carries over a checkbox or approval from a saved revision.
// see docs/CONCEPTS.md#application-package-approval
export default function ApplicationPackageReview(props) {
  // Identity or working-edit changes start a new review session with an unchecked box.
  return (
    <ReviewSession
      key={`${props.applicationId}:${props.packageId}:${Boolean(props.disabled)}`}
      {...props}
    />
  )
}

function ReviewSession({ applicationId, packageId, revision, disabled }) {
  const invalidate = useApiInvalidation()
  const id = useId()
  const generation = useRef(0)
  const inFlight = useRef(false)
  const [review, setReview] = useState(null)
  const [checked, setChecked] = useState(false)
  const [busy, setBusy] = useState(false)
  const [uncertain, setUncertain] = useState(false)
  const [errors, setErrors] = useState({})
  const base = `/jobs/applications/${applicationId}/packages/${packageId}`
  useEffect(
    () => () => {
      generation.current += 1
    },
    []
  )
  const load = async () => {
    if (inFlight.current || disabled) return
    const epoch = generation.current
    inFlight.current = true
    setBusy(true)
    setErrors({})
    setReview(null)
    setChecked(false)
    try {
      const { data } = await apiClient.get(`${base}/`)
      if (epoch === generation.current) {
        setReview(data)
        setUncertain(false)
      }
    } catch (error) {
      if (epoch === generation.current) {
        setErrors(apiErrors(error))
        setUncertain(true)
      }
    } finally {
      if (epoch === generation.current) {
        inFlight.current = false
        setBusy(false)
      }
    }
  }
  const approve = async () => {
    if (
      inFlight.current ||
      disabled ||
      uncertain ||
      !checked ||
      !review?.approvable
    )
      return
    const epoch = generation.current
    inFlight.current = true
    setBusy(true)
    setErrors({})
    try {
      const { data } = await apiClient.post(`${base}/approve/`, {
        expected_revision: review.revision,
        content_sha256: review.content_sha256,
        approval: true,
      })
      invalidate()
      if (epoch === generation.current) {
        setReview((current) => ({ ...current, approval: data.approval }))
        setChecked(false)
      }
    } catch (error) {
      if (epoch === generation.current) {
        setErrors(
          apiErrors(
            error,
            'Approval could not be confirmed. Reload this package before another attempt.'
          )
        )
        setUncertain(true)
        setChecked(false)
      }
    } finally {
      if (epoch === generation.current) {
        inFlight.current = false
        setBusy(false)
      }
    }
  }
  return (
    <section
      className="stack"
      aria-label={`Saved package revision ${revision}`}
    >
      <Button variant="outline" disabled={disabled || busy} onClick={load}>
        {busy
          ? 'Checking saved documents…'
          : `Review saved package revision ${revision}`}
      </Button>
      <FormErrors errors={errors} prefix={id} />
      {uncertain && (
        <p>
          Reload this saved package to reconcile its approval. No automatic
          retry was made.
        </p>
      )}
      {disabled && (
        <p>
          Save or discard your working edits before reviewing saved documents.
        </p>
      )}
      {review && !disabled && (
        <>
          <h3>Saved package revision {review.revision}</h3>
          <p>
            Text and paragraph order come from the saved DOCX files. Fonts and
            page breaks may differ here; download the files to check their
            layout.
          </p>
          <p>
            Saved job context: {review.job_context.title} —{' '}
            {review.job_context.company_name}
          </p>
          <p className="job-copy">{review.job_context.description}</p>
          <p className="job-copy">{review.job_context.requirements}</p>
          <StoredDocument title="Saved CV" paragraphs={review.previews.cv} />
          <StoredDocument
            title="Saved cover letter"
            paragraphs={review.previews['cover-letter']}
          />
          <div className="action-group">
            <DownloadButton
              path={`${base}/documents/cv/`}
              filename="Application_CV.docx"
            >
              Download saved package CV
            </DownloadButton>
            <DownloadButton
              path={`${base}/documents/cover-letter/`}
              filename="Application_Cover_Letter.docx"
            >
              Download saved package cover letter
            </DownloadButton>
          </div>
          {review.job_context.application_method === 'email' && (
            <div className="detail-block">
              <p>Saved recipient: {review.job_context.application_email}</p>
              <p>Saved subject: {review.email_subject || '(empty)'}</p>
              <p className="job-copy">
                {review.email_body || '(empty email draft)'}
              </p>
            </div>
          )}
          {review.approval ? (
            <p role="status">
              Document approval recorded for revision {review.revision}.
              {!review.is_latest &&
                ' A newer revision exists; this approval is historical.'}{' '}
              Document approval alone grants no sending or submission
              permission.
            </p>
          ) : review.approvable ? (
            <>
              <label className="check-field" htmlFor={`${id}-approve`}>
                <input
                  id={`${id}-approve`}
                  type="checkbox"
                  checked={checked}
                  disabled={busy || uncertain}
                  onChange={(event) => setChecked(event.target.checked)}
                />
                {review.approval_statement}
              </label>
              <Button
                disabled={!checked || busy || uncertain}
                onClick={approve}
              >
                Approve saved documents
              </Button>
            </>
          ) : (
            <p>
              This revision cannot be approved now. Reload the latest saved
              revision; historical packages stay readable.
            </p>
          )}
          <p>
            Document approval does not apply to another revision or authorize
            email delivery. Review the separate email permission controls.
          </p>
          {review.approval &&
            review.is_latest &&
            review.job_context.application_method === 'email' && (
              <ApplicationSendPanel
                applicationId={applicationId}
                packageId={packageId}
              />
            )}
        </>
      )}
    </section>
  )
}
