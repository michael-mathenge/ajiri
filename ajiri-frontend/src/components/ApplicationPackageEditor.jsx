import { useSchemaForm } from '../hooks/useSchemaForm'
import { packageSchema } from '../lib/formSchemas'
import { useEffect, useId, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import apiClient from '../api/client'
import { useApiInvalidation } from '../hooks/useApiQuery'
import { apiErrors } from '../lib/errors'
import DownloadButton from './DownloadButton'
import FormErrors from './FormErrors'
import ApplicationPackageReview from './ApplicationPackageReview'
import { Button } from './ui'

// Saving a revision never approves documents or sends an application.
// see docs/CONCEPTS.md#application-package-editor
export default function ApplicationPackageEditor({
  applicationId,
  readOnly = false,
}) {
  const invalidate = useApiInvalidation()
  const id = useId()
  const inFlight = useRef(false)
  const [opened, setOpened] = useState(false)
  const [data, setData] = useState(null)
  const [versions, setVersions] = useState([])
  const [page, setPage] = useState(1)
  const { values, setValues, errors, setErrors, submit } = useSchemaForm(
    packageSchema,
    {
      cv_version: '',
      letter_text: '',
      email_subject: '',
      email_body: '',
    }
  )
  const {
    cv_version: cv,
    letter_text: letter,
    email_subject: subject,
    email_body: body,
  } = values
  const setCV = (value) =>
    setValues((current) => ({ ...current, cv_version: value }))
  const setLetter = (value) =>
    setValues((current) => ({ ...current, letter_text: value }))
  const setSubject = (value) =>
    setValues((current) => ({ ...current, email_subject: value }))
  const setBody = (value) =>
    setValues((current) => ({ ...current, email_body: value }))
  const [dirty, setDirty] = useState(false)
  const [busy, setBusy] = useState(false)
  const [uncertain, setUncertain] = useState(false)
  const [notice, setNotice] = useState('')
  const base = `/jobs/applications/${applicationId}`
  useEffect(() => {
    if (!dirty) return
    const beforeUnload = (event) => {
      event.preventDefault()
      event.returnValue = ''
    }
    const leave = (event) => {
      const link = event.target.closest?.('a[href]')
      if (
        link &&
        !link.hasAttribute('download') &&
        link.target !== '_blank' &&
        !window.confirm('Leave with unsaved application edits?')
      )
        event.preventDefault()
    }
    window.addEventListener('beforeunload', beforeUnload)
    document.addEventListener('click', leave, true)
    return () => {
      window.removeEventListener('beforeunload', beforeUnload)
      document.removeEventListener('click', leave, true)
    }
  }, [dirty])
  const allowReplace = () =>
    !dirty || window.confirm('Discard unsaved edits and load this revision?')
  const applyRevision = (row) => {
    setCV(row?.cv_version || '')
    setLetter(row?.letter_text || '')
    setSubject(row?.email_subject || '')
    setBody(row?.email_body || '')
  }
  const load = async (requestedPage = 1) => {
    if (inFlight.current || !allowReplace()) return
    inFlight.current = true
    setOpened(true)
    setBusy(true)
    setErrors({})
    setNotice('')
    try {
      const [packages, cvs] = await Promise.all([
        apiClient.get(`${base}/packages/?page=${requestedPage}`),
        apiClient.get('/profiles/me/cv-versions/'),
      ])
      setData(packages.data)
      setVersions(cvs.data.versions)
      setPage(requestedPage)
      applyRevision(requestedPage === 1 ? packages.data.results[0] : null)
      setDirty(false)
      setUncertain(false)
    } catch (error) {
      setErrors(
        apiErrors(
          error,
          'Could not load application revisions. Try loading again.'
        )
      )
      setUncertain(true)
    } finally {
      inFlight.current = false
      setBusy(false)
    }
  }
  const change = (setter) => (event) => {
    setter(event.target.value)
    setDirty(true)
    setNotice('')
  }
  const generate = async () => {
    if (inFlight.current || !cv || !allowReplace()) return
    inFlight.current = true
    setBusy(true)
    setErrors({})
    setNotice('')
    try {
      const response = await apiClient.post(`${base}/package-draft/`, {
        cv_version: cv,
      })
      setLetter(response.data.letter_text)
      setData((current) => ({
        ...current,
        job_context: response.data.job_context,
        context_sha256: response.data.context_sha256,
      }))
      setDirty(true)
      setNotice(
        response.data.missing_information.length
          ? `Draft needs your review. Missing: ${response.data.missing_information.join(', ')}.`
          : 'Draft created from your selected approved CV. Check it against the job description.'
      )
    } catch (error) {
      setErrors(apiErrors(error))
    } finally {
      inFlight.current = false
      setBusy(false)
    }
  }
  const save = async () => {
    if (inFlight.current || uncertain) return
    inFlight.current = true
    setBusy(true)
    setErrors({})
    setNotice('')
    try {
      const response = await apiClient.post(`${base}/packages/`, {
        cv_version: cv,
        expected_revision: data.latest_revision,
        context_sha256: data.context_sha256,
        letter_text: letter,
        email_subject: subject,
        email_body: body,
      })
      invalidate()
      setData((current) => ({
        ...current,
        latest_revision: response.data.revision,
        results: [response.data],
        count: current.count + 1,
        next: null,
        previous: null,
      }))
      setPage(1)
      setDirty(false)
      setNotice(
        `Saved package revision ${response.data.revision}. No documents approved and no email sent.`
      )
    } catch (error) {
      setErrors(
        apiErrors(
          error,
          'Save could not be confirmed. Reload revisions before trying another save.'
        )
      )
      // Never repeat an uncertain mutation: GET saved revisions before another explicit save.
      if (
        !error.response ||
        error.response.status >= 500 ||
        error.response.status === 409
      )
        setUncertain(true)
    } finally {
      inFlight.current = false
      setBusy(false)
    }
  }
  return (
    <section className="stack" aria-label="Application document editor">
      <Button variant="outline" disabled={busy} onClick={() => load()}>
        {opened
          ? 'Reload saved revisions'
          : readOnly
            ? 'View saved package revisions'
            : 'Choose CV and edit cover letter'}
      </Button>
      {opened && (
        <>
          <FormErrors errors={errors} prefix={id} />
          {notice && <p role="status">{notice}</p>}
          {uncertain && (
            <p>
              Reload saved revisions to reconcile before saving again. Unsaved
              edits will need your confirmation to discard.
            </p>
          )}
          {data && (
            <>
              <h3>Job context for the next revision</h3>
              <p>
                {data.job_context.title} — {data.job_context.company_name}
              </p>
              <p className="job-copy">{data.job_context.description}</p>
              <p className="job-copy">{data.job_context.requirements}</p>
              {data.job_context.truncated && (
                <p>
                  Job text is shortened here. Check the original listing for
                  full instructions.
                </p>
              )}
              <p>
                Job text is reference material. Check every claim yourself;
                drafting does not establish suitability.
              </p>
              <p>
                {data.latest_revision
                  ? `Latest saved package: revision ${data.latest_revision}.`
                  : 'Legacy application: original documents have no package approval. Saving creates the first new revision.'}
              </p>
              <label htmlFor={`${id}-history`}>
                Saved cover-letter revision for this job
              </label>
              <select
                className="input"
                id={`${id}-history`}
                value=""
                disabled={busy}
                onChange={(event) => {
                  const row = data.results.find(
                    (item) => item.id === event.target.value
                  )
                  if (row && allowReplace()) {
                    applyRevision(row)
                    setDirty(true)
                    setNotice(
                      `Loaded revision ${row.revision} as a working copy. Saving creates a new revision with the job context above.`
                    )
                  }
                }}
              >
                <option value="">Choose a saved revision</option>
                {data.results.map((row) => (
                  <option key={row.id} value={row.id}>
                    Revision {row.revision}
                  </option>
                ))}
              </select>
              <div className="action-group">
                {data.previous && (
                  <Button disabled={busy} onClick={() => load(page - 1)}>
                    Newer revisions
                  </Button>
                )}
                {data.next && (
                  <Button disabled={busy} onClick={() => load(page + 1)}>
                    Older revisions
                  </Button>
                )}
              </div>
              {!data.editable ? (
                <p>This application cannot be edited in its current state.</p>
              ) : (
                <form
                  className="stack"
                  noValidate
                  onSubmit={(event) => submit(save)(event)}
                >
                  <p>
                    <Link to="/cv-builder">Build or approve a CV</Link>. Only
                    owner-approved CVs can be selected.
                  </p>
                  <label htmlFor={`${id}-cv`}>Approved CV version</label>
                  <select
                    className="input"
                    id={`${id}-cv`}
                    value={cv}
                    disabled={busy}
                    required
                    onChange={change(setCV)}
                  >
                    <option value="">Choose an approved CV</option>
                    {cv && !versions.some((row) => row.id === cv) && (
                      <option value={cv}>
                        Previously selected approved CV
                      </option>
                    )}
                    {versions.map((row) => (
                      <option key={row.id} value={row.id}>
                        CV revision {row.revision}
                      </option>
                    ))}
                  </select>
                  {cv && (
                    <DownloadButton
                      path={`/profiles/me/cv-versions/${cv}/download/`}
                      filename="Approved_CV.docx"
                    >
                      Download selected CV
                    </DownloadButton>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    disabled={busy || !cv || uncertain}
                    onClick={generate}
                  >
                    Draft letter from selected CV
                  </Button>
                  <label htmlFor={`${id}-letter`}>Working cover letter</label>
                  <textarea
                    className="input"
                    id={`${id}-letter`}
                    rows={14}
                    maxLength={10000}
                    required
                    value={letter}
                    disabled={busy}
                    onChange={change(setLetter)}
                    aria-invalid={Boolean(errors.letter_text)}
                    aria-describedby={
                      errors.letter_text ? `${id}-letter_text-error` : undefined
                    }
                  />
                  {data.job_context.application_method === 'email' && (
                    <>
                      <label htmlFor={`${id}-subject`}>
                        Email subject draft
                      </label>
                      <input
                        className="input"
                        id={`${id}-subject`}
                        maxLength={255}
                        value={subject}
                        disabled={busy}
                        onChange={change(setSubject)}
                      />
                      <label htmlFor={`${id}-body`}>Email body draft</label>
                      <textarea
                        className="input"
                        id={`${id}-body`}
                        rows={6}
                        maxLength={10000}
                        value={body}
                        disabled={busy}
                        onChange={change(setBody)}
                      />
                    </>
                  )}
                  <p>
                    {dirty ? 'Unsaved edits.' : 'No unsaved edits.'} Changing CV
                    does not rewrite your letter automatically.
                  </p>
                  <Button
                    type="submit"
                    disabled={
                      busy || uncertain || !cv || !letter.trim() || !dirty
                    }
                  >
                    {busy ? 'Working…' : 'Save new package revision'}
                  </Button>
                  <p>
                    Saving preserves a draft only. Review its saved package
                    below before approving documents. Email delivery needs
                    separate explicit permission and an enabled sending route.
                  </p>
                </form>
              )}
              {data.results.map((row) => (
                <ApplicationPackageReview
                  key={row.id}
                  applicationId={applicationId}
                  packageId={row.id}
                  revision={row.revision}
                  disabled={dirty || busy || uncertain}
                />
              ))}
            </>
          )}
        </>
      )}
    </section>
  )
}
