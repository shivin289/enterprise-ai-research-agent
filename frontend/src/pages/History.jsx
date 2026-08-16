import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listResearch } from '../services/api'

const STATUS_COLOR = {
  completed: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-rose-100 text-rose-700',
  pending: 'bg-slate-100 text-slate-600',
  planning: 'bg-amber-100 text-amber-700',
  searching: 'bg-amber-100 text-amber-700',
  validating: 'bg-amber-100 text-amber-700',
  synthesizing: 'bg-amber-100 text-amber-700',
}

export default function History() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    listResearch()
      .then(setSessions)
      .catch(() => setError('Could not load research history.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="py-12 px-4 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-ink">Research History</h1>
        <Link to="/" className="text-sm font-medium text-accent">+ New research</Link>
      </div>

      {loading && <p className="text-sm text-slate-400">Loading...</p>}
      {error && <p className="text-sm text-conflict">{error}</p>}

      {!loading && !error && sessions.length === 0 && (
        <div className="text-center text-sm text-slate-400 border border-dashed border-slate-200 rounded-xl p-10">
          <p>No research sessions yet.</p>
          <Link to="/" className="inline-block mt-4 text-accent text-sm font-medium">
            Start your first research query →
          </Link>
        </div>
      )}

      <ul className="space-y-2">
        {sessions.map((s) => (
          <li key={s.research_id}>
            <Link
              to={`/research/${s.research_id}`}
              className="block rounded-lg border border-slate-200 p-4 hover:border-accent hover:shadow-sm transition"
            >
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-medium text-slate-800 line-clamp-2">{s.query}</p>
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${STATUS_COLOR[s.status] || 'bg-slate-100 text-slate-600'}`}>
                  {s.status}
                </span>
              </div>
              <div className="mt-2 flex items-center gap-3 text-xs text-slate-400">
                <span>{new Date(s.created_at).toLocaleString()}</span>
                {s.confidence_score != null && (
                  <span>Confidence: {Math.round(s.confidence_score * 100)}%</span>
                )}
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
