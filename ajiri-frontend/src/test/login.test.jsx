import { beforeEach, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from './test-utils'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import apiClient from '../api/client'
import Login from '../pages/Login'
import { AuthContext } from '../hooks/useAuth'

vi.mock('../api/client', () => ({ default: { post: vi.fn() } }))
beforeEach(() => {
  vi.resetAllMocks()
  localStorage.clear()
})
const fill = () => {
  fireEvent.change(screen.getByLabelText('Email address'), {
    target: { value: 'test@example.com' },
  })
  fireEvent.change(screen.getByLabelText('Password', { exact: true }), {
    target: { value: 'test-password' },
  })
}
const renderLogin = (from) => {
  const setSignedIn = vi.fn()
  render(
    <AuthContext.Provider value={{ signedIn: false, setSignedIn }}>
      <MemoryRouter initialEntries={[{ pathname: '/login', state: { from } }]}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<h1>Jobs destination</h1>} />
          <Route path="/jobs/42" element={<h1>Requested job</h1>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  )
  return setSignedIn
}
it('stores access, updates navigation and returns to the requested route', async () => {
  apiClient.post.mockResolvedValue({ data: { access: 'test-access' } })
  const setSignedIn = renderLogin('/jobs/42')
  fill()
  fireEvent.click(screen.getByRole('button', { name: 'Log in', exact: true }))
  expect(await screen.findByText('Requested job')).toBeVisible()
  expect(localStorage.getItem('access_token')).toBe('test-access')
  expect(setSignedIn).toHaveBeenCalledWith(true)
})
it('rejects external return destinations', async () => {
  apiClient.post.mockResolvedValue({ data: { access: 'test-access' } })
  renderLogin('//untrusted.example')
  fill()
  fireEvent.click(screen.getByRole('button', { name: 'Log in', exact: true }))
  expect(await screen.findByText('Jobs destination')).toBeVisible()
})
it('shows invalid credentials without storing a token', async () => {
  apiClient.post.mockRejectedValue({ response: { status: 401 } })
  renderLogin('/')
  fill()
  fireEvent.click(screen.getByRole('button', { name: 'Log in', exact: true }))
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'email or password is incorrect'
  )
  expect(localStorage.getItem('access_token')).toBeNull()
})
it('disables repeated login while the first request is pending', async () => {
  apiClient.post.mockReturnValue(new Promise(() => {}))
  renderLogin('/')
  fill()
  fireEvent.click(screen.getByRole('button', { name: 'Log in', exact: true }))
  expect(
    await screen.findByRole('button', { name: 'Logging in…' })
  ).toBeDisabled()
  expect(apiClient.post).toHaveBeenCalledTimes(1)
})
it('shows a useful connection error', async () => {
  apiClient.post.mockRejectedValue(new Error('offline'))
  renderLogin('/')
  fill()
  fireEvent.click(screen.getByRole('button', { name: 'Log in', exact: true }))
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Check your connection'
  )
})

it('announces successful registration on arrival at login', () => {
  render(
    <AuthContext.Provider value={{ signedIn: false, setSignedIn: vi.fn() }}>
      <MemoryRouter
        initialEntries={[{ pathname: '/login', state: { registered: true } }]}
      >
        <Login />
      </MemoryRouter>
    </AuthContext.Provider>
  )
  expect(screen.getByRole('status')).toHaveTextContent(
    'Account created. Log in to continue.'
  )
})
