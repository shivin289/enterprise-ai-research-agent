export default function ConfidenceBadge({ score }) {
  const pct = Math.round((score || 0) * 100)
  const color = pct >= 75 ? 'bg-emerald-100 text-emerald-800' : pct >= 50 ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${color}`}>
      Confidence: {pct}%
    </span>
  )
}
