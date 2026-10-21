import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import apiClient from '../api/client'
import { useApiQuery, useApiInvalidation } from '../hooks/useApiQuery'
import { apiErrors } from '../lib/errors'
import FormErrors from '../components/FormErrors'
import DownloadButton from '../components/DownloadButton'
import MonthYearField from '../components/MonthYearField'
import {
  Button,
  Card,
  ErrorState,
  Input,
  LoadingState,
  Textarea,
} from '../components/ui'

const sections = [
  [
    'employment',
    'Work experience',
    20,
    [
      ['title', 'Role'],
      ['organisation', 'Employer'],
      ['start', 'Start month', 'month'],
      ['end', 'End month', 'month'],
      ['current', 'I currently work here', 'checkbox'],
      ['description', 'Description', 'textarea'],
      ['achievements', 'Achievements (one per line)', 'bullets'],
    ],
  ],
  [
    'education',
    'Education',
    15,
    [
      ['qualification', 'Qualification'],
      ['institution', 'Institution'],
      ['start', 'Start month', 'month'],
      ['end', 'End month', 'month'],
      ['current', 'I am currently studying here', 'checkbox'],
      ['description', 'Description', 'textarea'],
    ],
  ],
  [
    'certifications',
    'Certifications',
    20,
    [
      ['name', 'Certification'],
      ['issuer', 'Issuer'],
      ['issued', 'Issued month', 'month'],
      ['expiry', 'Expiry month', 'month'],
      ['description', 'Description', 'textarea'],
    ],
  ],
  [
    'projects',
    'Projects',
    20,
    [
      ['name', 'Project name'],
      ['organisation', 'Organisation (optional)'],
      ['url', 'Project URL', 'url'],
      ['description', 'Description', 'textarea'],
    ],
  ],
]

// Keep row numbers and field labels: repeated blank-field messages hide what to fix.
// see docs/CONCEPTS.md#cv-builder-flow
function cvErrors(error, fallback) {
  if (error.response?.status !== 400) return apiErrors(error, fallback)
  const labels = Object.fromEntries(
    sections.map(([key, title, , fields]) => [
      key,
      {
        title,
        fields: Object.fromEntries(
          fields.map(([field, label]) => [field, label])
        ),
      },
    ])
  )
  const result = {}
  const visit = (value, path = []) => {
    if (Array.isArray(value)) {
      value.forEach((item, index) =>
        visit(item, item && typeof item === 'object' ? [...path, index] : path)
      )
    } else if (value && typeof value === 'object') {
      Object.entries(value).forEach(([key, item]) =>
        visit(item, key === 'content' ? path : [...path, key])
      )
    } else if (value != null) {
      const [section, row, field] = path
      const label =
        labels[section] && typeof row === 'number'
          ? `${labels[section].title} ${row + 1}${field ? ` — ${labels[section].fields[field] || field.replaceAll('_', ' ')}` : ''}`
          : path.join(' ').replaceAll('_', ' ') || 'detail'
      ;(result[label] ||= []).push(String(value))
    }
  }
  visit(error.response?.data)
  return Object.keys(result).length ? result : apiErrors(error, fallback)
}

function Field({
  id,
  label,
  value,
  type = 'text',
  onChange,
  maxLength = 255,
  disabled = false,
}) {
  if (type === 'month')
    return (
      <MonthYearField
        id={id}
        label={label}
        value={value || ''}
        onChange={onChange}
        disabled={disabled}
      />
    )
  const Component = type === 'textarea' || type === 'bullets' ? Textarea : Input
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <Component
        id={id}
        type={type === 'textarea' || type === 'bullets' ? undefined : type}
        maxLength={type === 'bullets' ? 5010 : maxLength}
        {...(type === 'checkbox'
          ? { checked: value || false }
          : { value: value ?? '' })}
        onChange={(e) =>
          onChange(type === 'checkbox' ? e.target.checked : e.target.value)
        }
      />
    </div>
  )
}

export function CVPreview({ preview }) {
  return (
    <article className="cv-preview" aria-label="Saved CV preview">
      <h2>{preview.name || 'Name needed before approval'}</h2>
      {preview.headline && <p>{preview.headline}</p>}
      {preview.contact && <p>{preview.contact}</p>}
      {preview.sections.map((section) => (
        <section key={section.title}>
          <h3>{section.title}</h3>
          {section.entries.map((entry, i) => (
            <div key={i}>
              {entry.heading && <h4>{entry.heading}</h4>}
              {entry.paragraphs.map((text, j) => (
                <p key={j}>{text}</p>
              ))}
              {entry.bullets.length > 0 && (
                <ul>
                  {entry.bullets.map((text, j) => (
                    <li key={j}>{text}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </section>
      ))}
    </article>
  )
}

export function CVEditor({ initial }) {
  const invalidate = useApiInvalidation()
  const [saved, setSaved] = useState(initial)
  const [values, setValues] = useState(initial.content)
  const [skills, setSkills] = useState(initial.content.skills.join(', '))
  const [bullets, setBullets] = useState({})
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState('')
  const [review, setReview] = useState(false)
  const [approved, setApproved] = useState(false)
  const [conflict, setConflict] = useState(false)
  const errorSummary = useRef(null)
  const previewHeading = useRef(null)
  useEffect(() => {
    // Bring feedback into view after submitting a long form, including keyboard use.
    const target = Object.keys(errors).length
      ? errorSummary.current
      : review
        ? previewHeading.current
        : null
    target?.focus()
    target?.scrollIntoView?.({ block: 'start', behavior: 'auto' })
  }, [errors, review, saved.revision])
  const content = {
    ...values,
    skills: skills
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean),
    employment: values.employment.map((row) => ({
      ...row,
      achievements:
        bullets[row.id] === undefined
          ? row.achievements
          : bullets[row.id]
              .split('\n')
              .map((s) => s.trim())
              .filter(Boolean),
    })),
  }
  const dirty = JSON.stringify(content) !== JSON.stringify(saved.content)
  useEffect(() => {
    const warn = (event) => {
      if (dirty) {
        event.preventDefault()
        event.returnValue = ''
      }
    }
    const leave = (event) => {
      const anchor = event.target.closest?.('a[href]')
      if (
        !dirty ||
        !anchor ||
        anchor.target === '_blank' ||
        anchor.hasAttribute('download')
      )
        return
      const next = new URL(anchor.href, window.location.href)
      if (
        next.href !== window.location.href &&
        !window.confirm('You have unsaved CV changes. Leave without saving?')
      ) {
        event.preventDefault()
        event.stopPropagation()
      }
    }
    window.addEventListener('beforeunload', warn)
    document.addEventListener('click', leave, true)
    return () => {
      window.removeEventListener('beforeunload', warn)
      document.removeEventListener('click', leave, true)
    }
  }, [dirty])
  const change = (key, value) => {
    setValues((current) => ({ ...current, [key]: value }))
    setReview(false)
    setApproved(false)
    setMessage('')
  }
  const changeRow = (section, index, key, value) =>
    change(
      section,
      values[section].map((row, i) =>
        i === index
          ? {
              ...row,
              [key]: value,
              ...(key === 'current' && value ? { end: '' } : {}),
            }
          : row
      )
    )
  const save = async (event) => {
    event.preventDefault()
    if (busy || conflict) return
    setBusy(true)
    setErrors({})
    setMessage('')
    setApproved(false)
    try {
      const { data } = dirty
        ? await apiClient.patch('/profiles/me/cv-draft/', {
            expected_revision: saved.revision,
            content,
          })
        : { data: saved }
      invalidate()
      setSaved(data)
      setValues(data.content)
      setSkills(data.content.skills.join(', '))
      setBullets({})
      setReview(true)
      setMessage(
        `Revision ${data.revision} saved. Review the preview before approving.`
      )
    } catch (error) {
      setErrors(
        cvErrors(
          error,
          'Save could not be confirmed. Your edits are still here; reload only when ready.'
        )
      )
      if (error.response?.status === 409) setConflict(true)
    } finally {
      setBusy(false)
    }
  }
  const approve = async () => {
    if (busy || dirty || !approved || conflict) return
    setBusy(true)
    setErrors({})
    setMessage('')
    try {
      // Bind consent to the saved content, never an unsaved editor or newer tab.
      // see docs/CONCEPTS.md#cv-builder-flow
      const { data } = await apiClient.post('/profiles/me/cv-draft/approve/', {
        expected_revision: saved.revision,
        content_sha256: saved.content_sha256,
        approval: true,
      })
      invalidate()
      setSaved((current) => ({
        ...current,
        approval_id: data.approval_id,
        versions: [
          { id: data.approval_id, revision: data.revision },
          ...current.versions.filter((v) => v.id !== data.approval_id),
        ],
      }))
      setMessage(
        `Revision ${saved.revision} approved. Your CV is ready to download.`
      )
    } catch (error) {
      setErrors(
        apiErrors(
          error,
          'Approval could not be confirmed. No automatic retry was made.'
        )
      )
      if (error.response?.status === 409) setConflict(true)
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="stack">
      <p role="status">
        {message ||
          (dirty
            ? 'Unsaved changes. Save and preview before approval.'
            : `Saved revision ${saved.revision}.`)}
      </p>
      <p className="muted">
        This personal CV is separate from job application drafts. Editing it
        does not change your account or saved applications.
      </p>
      {Object.keys(errors).length > 0 && (
        <div ref={errorSummary} tabIndex={-1} aria-label="CV save errors">
          <FormErrors
            errors={errors}
            prefix="cv"
            className="form-error-summary"
          />
        </div>
      )}
      {conflict && (
        <p role="alert">
          Another change was saved. Your edits remain on this page. Copy
          anything you need before reloading to compare with the current
          version.
        </p>
      )}
      <form onSubmit={save} className="stack" aria-busy={busy}>
        <fieldset disabled={busy} className="stack">
          <Card>
            <h2>Contact details</h2>
            <div className="profile-grid">
              {[
                ['name', 'Full name'],
                ['email', 'Contact email', 'email'],
                ['phone', 'Phone', 'tel'],
                ['location', 'Location'],
              ].map(([key, label, type]) => (
                <Field
                  key={key}
                  id={`cv-${key}`}
                  label={label}
                  type={type}
                  value={values.contact[key]}
                  maxLength={key === 'phone' ? 20 : key === 'email' ? 254 : 255}
                  onChange={(value) =>
                    change('contact', { ...values.contact, [key]: value })
                  }
                />
              ))}
            </div>
          </Card>
          <Card className="stack">
            <h2>Summary and skills</h2>
            <Field
              id="cv-headline"
              label="Professional headline"
              value={values.headline}
              onChange={(value) => change('headline', value)}
            />
            <Field
              id="cv-summary"
              label="Summary (optional)"
              type="textarea"
              maxLength={3000}
              value={values.summary}
              onChange={(value) => change('summary', value)}
            />
            <Field
              id="cv-skills"
              label="Skills (comma separated)"
              maxLength={5100}
              value={skills}
              onChange={(value) => {
                setSkills(value)
                setReview(false)
                setApproved(false)
                setMessage('')
              }}
            />
          </Card>
          {sections.map(([section, title, limit, fields]) => (
            <Card className="stack" key={section}>
              <h2>
                {title} <span className="muted text-sm">Optional</span>
              </h2>
              {values[section].map((row, index) => (
                <fieldset className="cv-entry stack" key={row.id}>
                  <legend>
                    {title} {index + 1}
                  </legend>
                  <div className="profile-grid">
                    {fields.map(([key, label, type]) => (
                      <Field
                        key={key}
                        id={`cv-${row.id}-${key}`}
                        label={`${label} (${title.toLowerCase()} ${index + 1})`}
                        type={type}
                        maxLength={
                          key === 'description'
                            ? 2000
                            : key === 'url'
                              ? 2048
                              : 255
                        }
                        disabled={key === 'end' && Boolean(row.current)}
                        value={
                          type === 'bullets'
                            ? (bullets[row.id] ??
                              row.achievements?.join('\n') ??
                              '')
                            : row[key]
                        }
                        onChange={(value) =>
                          type === 'bullets'
                            ? (setBullets((current) => ({
                                ...current,
                                [row.id]: value,
                              })),
                              setReview(false),
                              setApproved(false),
                              setMessage(''))
                            : changeRow(section, index, key, value)
                        }
                      />
                    ))}
                  </div>
                  <Button
                    variant="outline"
                    onClick={() =>
                      change(
                        section,
                        values[section].filter((_, i) => i !== index)
                      )
                    }
                  >
                    Remove {title.toLowerCase()} {index + 1}
                  </Button>
                </fieldset>
              ))}
              <Button
                variant="outline"
                disabled={values[section].length >= limit}
                onClick={() =>
                  change(section, [
                    ...values[section],
                    {
                      id: crypto.randomUUID(),
                      ...Object.fromEntries(
                        fields.map(([key, , type]) => [
                          key,
                          type === 'checkbox'
                            ? false
                            : type === 'bullets'
                              ? []
                              : '',
                        ])
                      ),
                    },
                  ])
                }
              >
                Add {title.toLowerCase()}
              </Button>
            </Card>
          ))}
        </fieldset>
        <Button type="submit" disabled={busy || conflict}>
          {busy ? 'Please wait…' : 'Save and preview CV'}
        </Button>
      </form>
      {review && !dirty && (
        <Card className="stack">
          <h2 ref={previewHeading} tabIndex={-1}>
            Review revision {saved.revision}
          </h2>
          <p>
            Check every detail. The DOCX uses this content and section order;
            page breaks may differ. No information is invented.
          </p>
          <CVPreview preview={saved.preview} />
          {!saved.approval_id && (
            <>
              <label className="check-field">
                <input
                  type="checkbox"
                  checked={approved}
                  disabled={busy || conflict}
                  onChange={(e) => setApproved(e.target.checked)}
                />
                I have reviewed this CV and approve this version.
              </label>
              <Button
                onClick={approve}
                disabled={!approved || busy || conflict}
              >
                Approve this CV version
              </Button>
            </>
          )}
        </Card>
      )}
      {!dirty && saved.approval_id && (
        <DownloadButton
          path={`/profiles/me/cv-versions/${saved.approval_id}/download/`}
          filename="Ajiri_CV.docx"
        >
          Download approved CV (revision {saved.revision})
        </DownloadButton>
      )}
      {saved.versions.filter((version) => version.revision !== saved.revision)
        .length > 0 && (
        <Card>
          <h2>Earlier approved versions</h2>
          <p>
            These are earlier snapshots, not your current draft. Showing up to
            20 recent versions.
          </p>
          {saved.versions
            .filter((version) => version.revision !== saved.revision)
            .map((version) => (
              <DownloadButton
                key={version.id}
                path={`/profiles/me/cv-versions/${version.id}/download/`}
                filename={`Ajiri_CV_revision_${version.revision}.docx`}
              >
                Download earlier revision {version.revision}
              </DownloadButton>
            ))}
        </Card>
      )}
    </div>
  )
}

export default function CVBuilder() {
  const invalidate = useApiInvalidation()
  const { data, loading, error, retry } = useApiQuery('/profiles/me/cv-draft/')
  const [started, setStarted] = useState(null)
  const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState({})
  const start = async () => {
    if (busy) return
    setBusy(true)
    setErrors({})
    try {
      const response = await apiClient.post('/profiles/me/cv-draft/', {})
      setStarted(response.data)
      invalidate()
    } catch (error) {
      setErrors(apiErrors(error))
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="stack">
      <h1>Build your CV</h1>
      <p className="lead">Your information, your review, your approved CV.</p>
      {loading ? (
        <LoadingState label="Loading CV" />
      ) : error ? (
        <ErrorState onRetry={retry}>{error}</ErrorState>
      ) : started || data.content ? (
        <CVEditor initial={started || data} />
      ) : (
        <Card className="stack">
          <p>
            Start with a copy of your profile. Add your own details, review the
            draft and approve it before downloading. You can save incomplete
            drafts and return later.
          </p>
          <FormErrors errors={errors} />
          <Button onClick={start} disabled={busy}>
            {busy ? 'Starting…' : 'Start my CV'}
          </Button>
        </Card>
      )}
      <Link to="/profile">Back to profile</Link>
    </div>
  )
}
