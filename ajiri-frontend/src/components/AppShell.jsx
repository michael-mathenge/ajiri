import { lazy, Suspense, useEffect, useState } from 'react'
import {
  Link,
  Navigate,
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
} from 'react-router-dom'
import {
  Bell,
  BriefcaseBusiness,
  LogOut,
  Menu,
  Moon,
  Sun,
  X,
} from 'lucide-react'
import apiClient from '../api/client'
import { Button, LoadingState } from './ui'
import { useToast } from '../hooks/useToast'
import { AuthContext, useAuth } from '../hooks/useAuth'

const PrivateQueryProvider = lazy(() => import('./PrivateQueryProvider'))

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => ({
    signedIn: Boolean(localStorage.getItem('access_token')),
    revision: 0,
  }))
  const setSignedIn = (signedIn) => {
    // A new keyed provider drops private reads before another account can render.
    // see docs/CONCEPTS.md#deferred-private-query-cache
    setSession((current) => ({ signedIn, revision: current.revision + 1 }))
  }
  useEffect(() => {
    const changedAccount = (event) => {
      if (event.key !== null && event.key !== 'access_token') return
      setSession((current) => ({
        signedIn: event.key !== null && Boolean(event.newValue),
        revision: current.revision + 1,
      }))
    }
    window.addEventListener('storage', changedAccount)
    return () => window.removeEventListener('storage', changedAccount)
  }, [])
  // The API still validates tokens. This state only keeps navigation in sync.
  // see docs/CONCEPTS.md#protected-routes
  return (
    <AuthContext.Provider value={{ signedIn: session.signedIn, setSignedIn }}>
      {session.signedIn ? (
        <Suspense fallback={<LoadingState label="Loading account" />}>
          <PrivateQueryProvider key={session.revision}>
            {children}
          </PrivateQueryProvider>
        </Suspense>
      ) : (
        children
      )}
    </AuthContext.Provider>
  )
}
export function ProtectedRoute() {
  const { signedIn } = useAuth()
  const location = useLocation()
  return signedIn ? (
    <Outlet />
  ) : (
    <Navigate
      to="/login"
      state={{ from: location.pathname + location.search }}
      replace
    />
  )
}
export default function AppShell() {
  const { signedIn, setSignedIn } = useAuth()
  const [menuPath, setMenuPath] = useState(null)
  const [loggingOut, setLoggingOut] = useState(false)
  const [theme, setTheme] = useState(
    () => document.documentElement.dataset.theme || 'light'
  )
  const location = useLocation()
  const navigate = useNavigate()
  const toast = useToast()
  const menuOpen = menuPath === location.pathname
  useEffect(() => {
    document.getElementById('main-content')?.focus()
  }, [location.pathname])
  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    document.documentElement.dataset.theme = next
    try {
      localStorage.setItem('ajiri-theme', next)
    } catch {
      /* Theme still works if storage is blocked. */
    }
  }
  const logout = async () => {
    setLoggingOut(true)
    try {
      await apiClient.post('/accounts/logout/')
      localStorage.removeItem('access_token')
      setSignedIn(false)
      navigate('/login')
      toast('You have been logged out')
    } catch {
      toast('Could not log out', 'Please check your connection and try again.')
    } finally {
      setLoggingOut(false)
    }
  }
  return (
    <>
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <header className="topbar">
        <div className="nav-container">
          <Link
            to="/"
            className="brand"
            aria-label="Ajiri Kenya home"
            onClick={() => setMenuPath(null)}
          >
            <span className="brand-mark">
              <BriefcaseBusiness size={21} aria-hidden="true" />
            </span>
            ajiri <span className="brand-country">KENYA</span>
          </Link>
          <nav
            id="primary-navigation"
            className={`nav-links ${menuOpen ? 'is-open' : ''}`}
            aria-label="Main navigation"
            onClick={() => setMenuPath(null)}
          >
            <NavLink to="/" end>
              <BriefcaseBusiness size={17} aria-hidden="true" />
              Find jobs
            </NavLink>
            <NavLink to="/plans">Plans</NavLink>
            {signedIn ? (
              <>
                <NavLink to="/applications">My applications</NavLink>
                <NavLink to="/profile">Profile</NavLink>
                <NavLink to="/cv-builder">CV builder</NavLink>
                <NavLink to="/employers">Post a job</NavLink>
                <NavLink to="/saved-searches">Saved searches</NavLink>
                <NavLink to="/notifications">
                  <Bell size={17} aria-hidden="true" />
                  Notifications
                </NavLink>
                <Button variant="ghost" onClick={logout} disabled={loggingOut}>
                  <LogOut size={17} aria-hidden="true" />
                  {loggingOut ? 'Logging out…' : 'Log out'}
                </Button>
              </>
            ) : (
              <>
                <NavLink to="/employer-guide">For employers</NavLink>
                <NavLink to="/login">Log in</NavLink>
                <Button asChild>
                  <Link to="/register">Create account</Link>
                </Button>
              </>
            )}
          </nav>
          <div className="nav-actions">
            <Button
              variant="ghost"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </Button>
            <Button
              variant="ghost"
              className="menu-toggle"
              aria-expanded={menuOpen}
              aria-controls="primary-navigation"
              aria-label={menuOpen ? 'Close menu' : 'Open menu'}
              onClick={() => setMenuPath(menuOpen ? null : location.pathname)}
            >
              {menuOpen ? <X size={22} /> : <Menu size={22} />}
            </Button>
          </div>
        </div>
      </header>
      <main id="main-content" tabIndex={-1} className="container">
        <Suspense fallback={<LoadingState label="Loading page" />}>
          <Outlet />
        </Suspense>
      </main>
      <footer className="footer">
        <span className="font-semibold">ajiri</span>
        <span>Your next chapter starts here.</span>
        <span>Made for Kenya · Salaries in KES</span>
        <Link to="/about">About Ajiri</Link>
        <Link to="/privacy">Privacy notice</Link>
      </footer>
    </>
  )
}
