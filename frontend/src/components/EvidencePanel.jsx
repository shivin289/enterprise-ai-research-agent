import ConfidenceBadge from './ConfidenceBadge'

/**
 * The "Why this recommendation?" panel from the architecture doc's
 * explainability requirement (#12) -- shows supporting evidence count,
 * source list, and confidence for a given report section.
 */
export default function EvidencePanel({ title, sourcesCount, evidenceCount, confidence, sources = [] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="font-semibold text-slate-800">{title}</p>

      <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-600">
        <span>✓ {sourcesCount} relevant sources</span>
        <span>✓ {evidenceCount} supporting evidence items</span>
      </div>

      {sources.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2 text-xs text-accent">
          {sources.map((s, i) => (
            <span key={i} className="rounded bg-accentSoft px-2 py-0.5">{s}</span>
          ))}
        </div>
      )}

      <div className="mt-4">
        <ConfidenceBadge score={confidence} />
      </div>
    </div>
  )
}
