import { lazy } from 'react'
import { Link, Route, Routes } from 'react-router-dom'
import AppShell, { AuthProvider, ProtectedRoute } from './components/AppShell'
import { Button, EmptyState, ToastProvider } from './components/ui'
import './App.css'
import PageErrorBoundary from './components/PageErrorBoundary'
import { useAuth } from './hooks/useAuth'

// Download each screen when it is visited, keeping the first mobile load smaller.
// see docs/CONCEPTS.md#route-code-splitting
const Showcase = lazy(() => import('./pages/Showcase'))
const EmployerGuide = lazy(() => import('./pages/EmployerGuide'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const JobList = lazy(() => import('./pages/JobList'))
const JobDetail = lazy(() => import('./pages/JobDetail'))
const Applications = lazy(() => import('./pages/Applications'))
const Notifications = lazy(() => import('./pages/Notifications'))
const Profile = lazy(() => import('./pages/Profile'))
const Employers = lazy(() => import('./pages/Employers'))
const SavedSearches = lazy(() => import('./pages/SavedSearches'))
const EmployerReview = lazy(() => import('./pages/EmployerReview'))
const CVBuilder = lazy(() => import('./pages/CVBuilder'))
const Subscriptions = lazy(() => import('./pages/Subscriptions'))
const AccountRecovery = lazy(() => import('./pages/AccountRecovery'))
const Privacy = lazy(() => import('./pages/Privacy'))
const AlertUnsubscribe = lazy(() => import('./pages/AlertUnsubscribe'))

function Home() {
  const { signedIn } = useAuth()
  return signedIn ? <JobList /> : <Showcase />
}

export default function App() {
  return (
    <PageErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/" element={<Home />} />
              <Route path="/employer-guide" element={<EmployerGuide />} />
              <Route path="/about" element={<Showcase />} />
              <Route element={<ProtectedRoute />}>
                <Route path="/jobs/:id" element={<JobDetail />} />
                <Route path="/applications" element={<Applications />} />
                <Route path="/notifications" element={<Notifications />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/employers" element={<Employers />} />
                <Route path="/saved-searches" element={<SavedSearches />} />
                <Route path="/employers/review" element={<EmployerReview />} />
                <Route path="/cv-builder" element={<CVBuilder />} />
                <Route
                  path="/email-verification"
                  element={
                    <AccountRecovery key="verification" mode="verification" />
                  }
                />
              </Route>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/privacy" element={<Privacy />} />
              <Route path="/unsubscribe" element={<AlertUnsubscribe />} />
              <Route
                path="/forgot-password"
                element={<AccountRecovery key="request" mode="request-reset" />}
              />
              <Route
                path="/reset-password"
                element={<AccountRecovery key="reset" mode="reset" />}
              />
              <Route
                path="/verify-email"
                element={<AccountRecovery key="verify" mode="verify" />}
              />
              <Route path="/plans" element={<Subscriptions />} />
              <Route
                path="*"
                element={
                  <EmptyState
                    title="Page not found"
                    action={
                      <Button asChild>
                        <Link to="/">Browse jobs</Link>
                      </Button>
                    }
                  >
                    This page may have moved. Find your next opportunity from
                    the jobs page.
                  </EmptyState>
                }
              />
            </Route>
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </PageErrorBoundary>
  )
}
