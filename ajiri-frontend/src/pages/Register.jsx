import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import apiClient from '../api/client'
import FormErrors from '../components/FormErrors'
import { apiErrors } from '../lib/errors'
import { Button, Input } from '../components/ui'

export default function Register() {
  const [values, setValues] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    password: '',
  })
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const fields = [
    ['full_name', 'Full name', 'text', 'name'],
    ['email', 'Email', 'email', 'email'],
    ['phone_number', 'Phone number', 'tel', 'tel'],
    ['password', 'Password', 'password', 'new-password'],
  ]
  const handleSubmit = async (event) => {
    event.preventDefault()
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
        onSubmit={handleSubmit}
        className="form-card"
        aria-busy={submitting}
      >
        <FormErrors errors={errors} prefix="register" />
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
