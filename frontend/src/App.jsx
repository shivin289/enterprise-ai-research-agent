import { Navigate, Route, Routes } from 'react-router-dom'
import NavBar from './components/NavBar'
import Dashboard from './pages/Dashboard'
import Research from './pages/Research'
import History from './pages/History'
import Documents from './pages/Documents'
import Login from './pages/Login'
import { isAuthenticated } from './services/api'

function RequireAuth({ children }) {
  if (!isAuthenticated()) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        path="/*"
        element={
          <RequireAuth>
            <div className="min-h-screen">
              <NavBar />
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/research/:researchId" element={<Research />} />
                <Route path="/history" element={<History />} />
                <Route path="/documents" element={<Documents />} />
              </Routes>
            </div>
          </RequireAuth>
        }
      />
    </Routes>
  )
}
