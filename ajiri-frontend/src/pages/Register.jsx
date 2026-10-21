import { useSchemaForm } from '../hooks/useSchemaForm'
import { registerSchema } from '../lib/formSchemas'
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import apiClient from '../api/client'
import FormErrors from '../components/FormErrors'
import { apiErrors } from '../lib/errors'
import { Button, Input } from '../components/ui'

export default function Register() {
  const { values, setValues, errors, setErrors, submit } = useSchemaForm(
    registerSchema,
    {
      full_name: '',
      email: '',
      phone_number: '',
      password: '',
      privacy_consent: false,
      privacy_policy_version: 'privacy-draft-v1',
    }
  )
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const fields = [
    ['full_name', 'Full name', 'text', 'name'],
    ['email', 'Email', 'email', 'email'],
    ['phone_number', 'Phone number', 'tel', 'tel'],
    ['password', 'Password', 'password', 'new-password'],
  ]
  const handleSubmit = async () => {
    if (submitting) return
    setErrors({})
    setSubmitting(true)
    try {
      await apiClient.post('/accounts/register/', values)
      navigate('/login', { state: { registered: true } })
    } catch (error) {
      setErrors(
        apiErrors(
          error,
          'Registration failed. Please check your connection and try again.'
        )
      )
    } finally {
      setSubmitting(false)
    }
  }
  return (
    <div>
      <h1>Create your account</h1>
      <p className="lead">Start finding opportunities that fit your skills.</p>
      <form
        noValidate
        onSubmit={(event) => submit(handleSubmit)(event)}
        className="form-card"
        aria-busy={submitting}
      >
        <FormErrors
          errors={errors}
          prefix="register"
          className="form-error-summary"
        />
        {fields.map(([name, label, type, autoComplete]) => (
          <div className="field" key={name}>
            <label htmlFor={name}>{label}</label>
            <Input
              id={name}
              name={name}
              type={type}
              autoComplete={autoComplete}
              value={values[name]}
              required={name !== 'phone_number'}
              minLength={name === 'password' ? 8 : undefined}
              aria-invalid={Boolean(errors[name])}
              aria-describedby={
                errors[name] ? `register-${name}-error` : undefined
              }
              onChange={(event) =>
                setValues({ ...values, [name]: event.target.value })
              }
            />
          </div>
        ))}
        <label className="check-field">
          <input
            type="checkbox"
            name="privacy_consent"
            required
            checked={values.privacy_consent}
            aria-invalid={Boolean(errors.privacy_consent)}
            aria-describedby={
              errors.privacy_consent
                ? 'register-privacy_consent-error'
                : undefined
            }
            onChange={(event) =>
              setValues({ ...values, privacy_consent: event.target.checked })
            }
          />
          <span>
            I have read the{' '}
            <Link to="/privacy" target="_blank" rel="noopener noreferrer">
              privacy notice (draft; opens in a new tab)
            </Link>{' '}
            and agree to the account processing it describes. This does not
            enable email alerts or authorize job applications.
          </span>
        </label>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Register'}
        </Button>
      </form>
      <p className="status-text">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  )
}
