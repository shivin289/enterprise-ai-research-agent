import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import ResearchForm from '../components/ResearchForm'
import { createResearch } from '../services/api'

/**
 * Screen 1: Research Dashboard. Submits the query, then redirects to
 * /research/:id where the Research page polls status and shows progress
 * -> report per the async-processing flow in the architecture doc.
 */
export default function Dashboard() {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(query, depth) {
    setIsSubmitting(true)
    setError('')
    try {
      const { research_id } = await createResearch(query, depth)
      navigate(`/research/${research_id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start research')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="py-16 px-4">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-ink">Enterprise AI Research Agent</h1>
        <p className="text-slate-500 mt-2">
          Ask a broad question. Get a source-backed, evidence-validated research report.
        </p>
      </div>

      <ResearchForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />

      {error && <p className="text-center text-sm text-conflict mt-4">{error}</p>}

      <div className="max-w-2xl mx-auto mt-10 grid grid-cols-3 gap-4 text-center text-xs text-slate-400">
        <div>
          <p className="text-2xl mb-1">🔍</p>
          <p>Decomposes your query into focused research questions</p>
        </div>
        <div>
          <p className="text-2xl mb-1">📚</p>
          <p>Validates evidence and flags conflicting sources</p>
        </div>
        <div>
          <p className="text-2xl mb-1">✅</p>
          <p>Every recommendation is cited back to its sources</p>
        </div>
      </div>
    </div>
  )
}
