import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import apiClient from '../api/client'

function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    try {
      const response = await apiClient.post('/accounts/login/', {
        email: email,
        password: password,
      })

      localStorage.setItem('access_token', response.data.access)
      navigate('/')
    } catch {
      setError('Login failed. Check your email and password.')
    }
  }

  return (
    <div>
      <h1>Log in</h1>
      <form onSubmit={handleSubmit} className="form-card">
        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        {error && <p className="error-text">{error}</p>}
        <button type="submit" className="btn btn-primary">Log in</button>
      </form>
      <p className="status-text">
        No account yet? <Link to="/register">Register</Link>
      </p>
    </div>
  )
}

export default Login
