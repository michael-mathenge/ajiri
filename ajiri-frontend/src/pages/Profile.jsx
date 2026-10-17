import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import apiClient from '../api/client'
import { useApiResource } from '../hooks/useApiResource'
import {
  Button,
  Card,
  ErrorState,
  Input,
  LoadingState,
  Textarea,
} from '../components/ui'
import DownloadButton from '../components/DownloadButton'
import FormErrors from '../components/FormErrors'
import { apiErrors } from '../lib/errors'
import { validateCV } from '../lib/cv'

export function ProfileEditor({ profile }) {
  const [values, setValues] = useState({
    full_name: profile.full_name || '',
    phone_number: profile.phone_number || '',
    headline: profile.headline || '',
    location: profile.location || '',
    bio: profile.bio || '',
    years_of_experience: profile.years_of_experience || 0,
    skill_names: profile.skills.map((skill) => skill.name).join(', '),
    notify_email: profile.notify_email,
    notify_in_app: profile.notify_in_app,
  })
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [file, setFile] = useState(null)
  const [fileError, setFileError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [hasCV, setHasCV] = useState(Boolean(profile.cv_file))
  const fileInput = useRef(null)
  const change = (event) =>
    setValues((current) => ({
      ...current,
      [event.target.name]:
        event.target.type === 'checkbox'
          ? event.target.checked
          : event.target.value,
    }))
  const save = async (event) => {
    event.preventDefault()
    if (saving) return
    setErrors({})
    setMessage('')
    setSaving(true)
    try {
      // JSON preserves an empty skills list, which multipart forms can otherwise omit.
      // see docs/CONCEPTS.md#profile-edit-and-upload
      await apiClient.patch('/profiles/me/', {
        ...values,
        years_of_experience: Number(values.years_of_experience),
        skill_names: [
          ...new Set(
            values.skill_names
              .split(',')
              .map((name) => name.trim())
              .filter(Boolean)
          ),
        ],
      })
      setMessage('Profile saved.')
    } catch (error) {
      setErrors(apiErrors(error))
    } finally {
      setSaving(false)
    }
  }
  const upload = async (event) => {
    event.preventDefault()
    if (uploading) return
    const error = validateCV(file)
    setFileError(error)
    if (error) return
    setUploading(true)
    setMessage('')
    const form = new FormData()
    form.append('cv_file', file)
    try {
      await apiClient.patch('/profiles/me/', form)
      setHasCV(true)
      setFile(null)
      fileInput.current.value = ''
      setMessage('CV uploaded. Your profile fields are saved separately.')
    } catch (error) {
      setFileError(Object.values(apiErrors(error)).flat().join(' '))
    } finally {
      setUploading(false)
    }
  }
  const fields = [
    ['full_name', 'Full name', 'text', 'name', 255],
    ['phone_number', 'Phone number', 'tel', 'tel', 20],
    ['headline', 'Professional headline', 'text', 'organization-title', 255],
    ['location', 'Location', 'text', 'address-level2', 255],
    ['years_of_experience', 'Years of experience', 'number', 'off'],
    ['skill_names', 'Skills (comma separated)', 'text', 'off'],
  ]
  return (
    <div className="stack">
      <p role="status" aria-live="polite">
        {message}
      </p>
      <Card>
        <h2>Your profile</h2>
        <p className="muted">Account email: {profile.email}</p>
        <form onSubmit={save} className="stack" aria-busy={saving}>
          <FormErrors errors={errors} prefix="profile" />
          <div className="profile-grid">
            {fields.map(([name, label, type, autoComplete, maxLength]) => (
              <div className="field" key={name}>
                <label htmlFor={name}>{label}</label>
                <Input
                  id={name}
                  name={name}
                  type={type}
                  autoComplete={autoComplete}
                  maxLength={maxLength}
                  min={type === 'number' ? 0 : undefined}
                  step={type === 'number' ? 1 : undefined}
                  required={type === 'number'}
                  value={values[name]}
                  onChange={change}
                  aria-invalid={Boolean(errors[name])}
                  aria-describedby={
                    errors[name] ? `profile-${name}-error` : undefined
                  }
                />
              </div>
            ))}
          </div>
          <p className="muted text-sm">
            Skills power your match scores. Leave the skills field empty to
            clear them.
          </p>
          <div className="field">
            <label htmlFor="bio">About you</label>
            <Textarea
              id="bio"
              name="bio"
              value={values.bio}
              onChange={change}
              aria-invalid={Boolean(errors.bio)}
              aria-describedby={errors.bio ? 'profile-bio-error' : undefined}
            />
          </div>
          <fieldset>
            <legend className="font-semibold">Job alerts</legend>
            <label className="check-field">
              <input
                type="checkbox"
                name="notify_email"
                checked={values.notify_email}
                onChange={change}
              />
              Email me about strong matches
            </label>
            <label className="check-field">
              <input
                type="checkbox"
                name="notify_in_app"
                checked={values.notify_in_app}
                onChange={change}
              />
              Show new match alerts in my inbox
            </label>
            <p className="muted text-sm">
              Preferences affect new alerts. Existing alerts stay in your
              history.
            </p>
          </fieldset>
          <Button type="submit" disabled={saving}>
            {saving ? 'Saving…' : 'Save profile'}
          </Button>
        </form>
      </Card>
      <Card>
        <h2>Your CV</h2>
        <p className="muted">
          Upload a PDF, DOC or DOCX, up to 5 MB. Generated documents use your
          profile fields; uploaded CV text is not extracted.
        </p>
        <form onSubmit={upload} className="stack" aria-busy={uploading}>
          <div className="field">
            <label htmlFor="cv-file">Choose CV file</label>
            <Input
              ref={fileInput}
              id="cv-file"
              type="file"
              accept=".pdf,.doc,.docx"
              aria-describedby="cv-file-help cv-file-error"
              aria-invalid={Boolean(fileError)}
              onChange={(event) => {
                const next = event.target.files?.[0] || null
                setFile(next)
                setFileError(next ? validateCV(next) : '')
              }}
            />
            <p id="cv-file-help" className="muted text-sm">
              Allowed: PDF, DOC, DOCX. Maximum: 5 MB.
            </p>
            <p
              id="cv-file-error"
              className="error-text"
              role={fileError ? 'alert' : undefined}
            >
              {fileError}
            </p>
          </div>
          <Button type="submit" disabled={uploading || Boolean(fileError)}>
            {uploading ? 'Uploading…' : 'Upload CV'}
          </Button>
        </form>
        <div className="action-group mt-6">
          {hasCV && (
            <DownloadButton path="/profiles/me/cv/" filename="Uploaded_CV">
              Download uploaded CV
            </DownloadButton>
          )}
          <Button asChild><Link to="/cv-builder">Build and review my CV</Link></Button>
        </div>
      </Card>
    </div>
  )
}
export default function Profile() {
  const { data, loading, error, retry } = useApiResource('/profiles/me/')
  if (loading) return <LoadingState label="Loading profile" />
  if (error) return <ErrorState onRetry={retry}>{error}</ErrorState>
  return (
    <div className="stack">
      <div>
        <h1>Your profile</h1>
        <p className="lead">
          Make your skills visible and choose how you hear about opportunities.
        </p>
      </div>
      <Link to="/email-verification">Check email verification</Link>
      <ProfileEditor profile={data} />
    </div>
  )
}
