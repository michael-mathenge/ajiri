import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, Check, Eye, EyeOff, ShieldCheck } from 'lucide-react'
import apiClient from '../api/client'
import { useAuth } from '../hooks/useAuth'
import { Button, Card, Input } from '../components/ui'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [visible, setVisible] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { setSignedIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const handleSubmit = async (event) => {
    event.preventDefault()
    if (submitting) return
    setError('')
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
      setError(
        error.response?.status === 401
          ? 'The email or password is incorrect. Please try again.'
          : 'We could not log you in. Check your connection and try again.'
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
        <p className="muted">Your next opportunity could be waiting.</p>
        <form
          onSubmit={handleSubmit}
          className="stack mt-8"
          aria-busy={submitting}
        >
          <div className="field">
            <label htmlFor="email">Email address</label>
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="username"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <div className="password-field">
              <Input
                id="password"
                name="password"
                type={visible ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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
          {error && (
            <p role="alert" className="error-text">
              {error}
            </p>
          )}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Logging in…' : 'Log in'}
            <ArrowRight size={18} aria-hidden="true" />
          </Button>
        </form>
        <p className="auth-switch">
          New to Ajiri? <Link to="/register">Create an account</Link>
        </p>
      </Card>
    </div>
  )
}
