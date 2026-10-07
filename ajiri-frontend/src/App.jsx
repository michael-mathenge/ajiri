import { Routes, Route, Link } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import JobList from './pages/JobList'
import JobDetail from './pages/JobDetail'
import Applications from './pages/Applications'
import Notifications from './pages/Notifications'
import './App.css'

function App() {
  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-mark">&#9679;</span> Ajiri
        </Link>
        <nav className="nav-links">
          <Link to="/">Jobs</Link>
          <Link to="/applications">My applications</Link>
          <Link to="/notifications">Notifications</Link>
          <Link to="/login">Log in</Link>
          <Link to="/register">Register</Link>
        </nav>
      </header>

      <main className="container">
        <Routes>
          <Route path="/" element={<JobList />} />
          <Route path="/jobs/:id" element={<JobDetail />} />
          <Route path="/applications" element={<Applications />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Routes>
      </main>
    </>
  )
}

export default App
