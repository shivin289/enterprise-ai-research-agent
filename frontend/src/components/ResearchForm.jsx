import { useState } from 'react'

/**
 * Screen 1: Research Dashboard input form.
 * Lets the user type a broad research query and pick a depth, then
 * kicks off the async pipeline via onSubmit.
 */
export default function ResearchForm({ onSubmit, isSubmitting }) {
  const [query, setQuery] = useState('')
  const [depth, setDepth] = useState('standard')

  function handleSubmit(e) {
    e.preventDefault()
    if (query.trim().length < 5) return
    onSubmit(query.trim(), depth)
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <label className="block text-sm font-medium text-slate-600 mb-2">
        What would you like to research?
      </label>
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Analyze the impact of AI on software development roles over the next 5 years."
        rows={3}
        className="w-full rounded-xl border border-slate-300 p-4 text-base shadow-sm
                   focus:border-accent focus:ring-2 focus:ring-accentSoft outline-none resize-none"
      />

      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-600">Research Depth</label>
          <select
            value={depth}
            onChange={(e) => setDepth(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm outline-none
                       focus:border-accent"
          >
            <option value="quick">Quick</option>
            <option value="standard">Standard</option>
            <option value="deep">Deep</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={isSubmitting || query.trim().length < 5}
          className="rounded-xl bg-ink px-6 py-2.5 text-sm font-semibold text-white
                     hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition"
        >
          {isSubmitting ? 'Starting research...' : 'Start Research'}
        </button>
      </div>
    </form>
  )
}
