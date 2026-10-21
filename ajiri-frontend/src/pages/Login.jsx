import { useSchemaForm } from '../hooks/useSchemaForm'
import { loginSchema } from '../lib/formSchemas'
import FormErrors from '../components/FormErrors'
import { apiErrors, rateLimitMessage } from '../lib/errors'
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, Check, Eye, EyeOff, ShieldCheck } from 'lucide-react'
import apiClient from '../api/client'
import { useAuth } from '../hooks/useAuth'
import { Button, Card, Input } from '../components/ui'

export default function Login() {
  const { values, setValues, errors, setErrors, submit } = useSchemaForm(
    loginSchema,
    { email: '', password: '' }
  )
  const { email, password } = values
  const [visible, setVisible] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const { setSignedIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const handleSubmit = async () => {
    if (submitting) return
    setErrors({})
    setSubmitting(true)
    try {
      const { data } = await apiClient.post('/accounts/login/', {
        email,
        password,
      })
      localStorage.setItem('access_token', data.access)
      setSignedIn(true)
      const from = location.state?.from
      navigate(
        typeof from === 'string' &&
          from.startsWith('/') &&
          !from.startsWith('//') &&
          !from.startsWith('/login')
          ? from
          : '/',
        { replace: true }
      )
    } catch (error) {
      setErrors(
        error.response?.status === 401
          ? {
              detail: ['The email or password is incorrect. Please try again.'],
            }
          : error.response?.status === 429
            ? { detail: [rateLimitMessage(error)] }
            : apiErrors(
                error,
                'We could not log you in. Check your connection and try again.'
              )
      )
    } finally {
      setSubmitting(false)
    }
  }
  return (
    <div className="auth-layout">
      <section className="auth-intro">
        <span className="eyebrow">A LITTLE CLOSER TO YOUR NEXT CHAPTER</span>
        <h1>
          Good skills.
          <br />
          Better opportunities.
        </h1>
        <p className="lead">
          Find work that fits you. Ajiri connects your skills with opportunities
          across Kenya.
        </p>
        <ul className="benefit-list">
          {[
            'See how your skills match each role',
            'Review your CV and cover letter before sending',
            'Keep your applications in one place',
          ].map((text) => (
            <li key={text}>
              <Check size={20} aria-hidden="true" />
              {text}
            </li>
          ))}
        </ul>
        <div className="trust-note">
          <ShieldCheck size={22} aria-hidden="true" />
          <span>
            You’re in control. Applications are sent only after you confirm.
          </span>
        </div>
      </section>
      <Card className="auth-card">
        <span className="eyebrow">WELCOME BACK</span>
        <h2>Log in to Ajiri</h2>
        {location.state?.registered && (
          <p role="status">Account created. Log in to continue.</p>
        )}
        <p className="muted">Your next opportunity could be waiting.</p>
        <form
          noValidate
          onSubmit={(event) => submit(handleSubmit)(event)}
          className="stack mt-8"
          aria-busy={submitting}
        >
          <div className="field">
            <label htmlFor="email">Email address</label>
            <Input
              aria-invalid={Boolean(errors.email)}
              aria-describedby={errors.email ? 'login-email-error' : undefined}
              id="email"
              name="email"
              type="email"
              autoComplete="username"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setValues({ ...values, email: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <div className="password-field">
              <Input
                aria-invalid={Boolean(errors.password)}
                aria-describedby={
                  errors.password ? 'login-password-error' : undefined
                }
                id="password"
                name="password"
                type={visible ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(e) =>
                  setValues({ ...values, password: e.target.value })
                }
                required
              />
              <Button
                variant="ghost"
                aria-label={visible ? 'Hide password' : 'Show password'}
                aria-pressed={visible}
                onClick={() => setVisible(!visible)}
              >
                {visible ? <EyeOff size={19} /> : <Eye size={19} />}
              </Button>
            </div>
          </div>
          <FormErrors errors={errors} prefix="login" />
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Logging in…' : 'Log in'}
            <ArrowRight size={18} aria-hidden="true" />
          </Button>
        </form>
        <p className="auth-switch">
          <Link to="/forgot-password">Forgot your password?</Link>
        </p>
        <p className="auth-switch">
          New to Ajiri? <Link to="/register">Create an account</Link>
        </p>
      </Card>
    </div>
  )
}
