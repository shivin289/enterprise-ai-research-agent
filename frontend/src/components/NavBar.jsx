import { Link, useLocation, useNavigate } from 'react-router-dom'
import { logout } from '../services/api'

const LINKS = [
  { to: '/', label: 'Research' },
  { to: '/history', label: 'History' },
  { to: '/documents', label: 'Documents' },
]

export default function NavBar() {
  const location = useLocation()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <span className="font-bold text-ink text-sm">🔎 Research Agent</span>
          {LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={`text-sm ${location.pathname === link.to ? 'text-accent font-medium' : 'text-slate-500 hover:text-ink'}`}
            >
              {link.label}
            </Link>
          ))}
        </div>
        <button onClick={handleLogout} className="text-xs text-slate-400 hover:text-conflict">
          Sign out
        </button>
      </div>
    </nav>
  )
}
