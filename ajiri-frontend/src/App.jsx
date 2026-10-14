import { lazy } from 'react'
import { Link, Route, Routes } from 'react-router-dom'
import AppShell, { AuthProvider, ProtectedRoute } from './components/AppShell'
import { Button, EmptyState, ToastProvider } from './components/ui'
import './App.css'

// Download each screen when it is visited, keeping the first mobile load smaller.
// see docs/CONCEPTS.md#route-code-splitting
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const JobList = lazy(() => import('./pages/JobList'))
const JobDetail = lazy(() => import('./pages/JobDetail'))
const Applications = lazy(() => import('./pages/Applications'))
const Notifications = lazy(() => import('./pages/Notifications'))
const Profile = lazy(() => import('./pages/Profile'))
const Subscriptions = lazy(() => import('./pages/Subscriptions'))

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Routes>
          <Route element={<AppShell />}>
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<JobList />} />
              <Route path="/jobs/:id" element={<JobDetail />} />
              <Route path="/applications" element={<Applications />} />
              <Route path="/notifications" element={<Notifications />} />
              <Route path="/profile" element={<Profile />} />
            </Route>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
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
                  This page may have moved. Find your next opportunity from the
                  jobs page.
                </EmptyState>
              }
            />
          </Route>
        </Routes>
      </ToastProvider>
    </AuthProvider>
  )
}
