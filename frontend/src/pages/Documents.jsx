import { useEffect, useState } from 'react'
import { uploadDocument, listDocuments } from '../services/api'

/**
 * Lets a user upload an internal document (e.g. company_ai_strategy.pdf)
 * that gets chunked + embedded into pgvector. Re-running a research
 * query afterward will pull relevant chunks in alongside web sources --
 * this is what backs the "incorporate new business info without
 * touching source code" demo beat (#26 in the architecture doc).
 */
export default function Documents() {
  const [docs, setDocs] = useState([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    refresh()
  }, [])

  function refresh() {
    listDocuments().then(setDocs).catch(() => {})
  }

  async function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      await uploadDocument(file)
      refresh()
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  return (
    <div className="py-12 px-4 max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-ink mb-2">Internal Documents</h1>
      <p className="text-sm text-slate-500 mb-6">
        Upload internal context (.txt, .md, .pdf) to be indexed and pulled into future research sessions.
      </p>

      <label className="flex items-center justify-center rounded-xl border-2 border-dashed border-slate-300 p-8 cursor-pointer hover:border-accent transition">
        <input type="file" accept=".txt,.md,.pdf" onChange={handleFileChange} className="hidden" disabled={uploading} />
        <span className="text-sm text-slate-500">
          {uploading ? 'Uploading and indexing...' : 'Click to upload a document'}
        </span>
      </label>

      {error && <p className="text-sm text-conflict mt-3">{error}</p>}

      <ul className="mt-6 space-y-2">
        {docs.map((d) => (
          <li key={d.id} className="flex items-center justify-between rounded-lg border border-slate-200 p-3">
            <span className="text-sm text-slate-800">{d.filename}</span>
            <span className="text-xs text-slate-400">v{d.version} · {new Date(d.created_at).toLocaleDateString()}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
