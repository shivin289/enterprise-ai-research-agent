export default function SourceCard({ source, index }) {
  return (
    <a
      href={source.url || '#'}
      target="_blank"
      rel="noreferrer"
      className="block rounded-lg border border-slate-200 p-3 hover:border-accent hover:shadow-sm transition"
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-slate-800 line-clamp-2">
          [{index}] {source.title}
        </p>
        <span className="shrink-0 text-xs text-slate-400">
          {Math.round((source.reliability_score || 0) * 100)}% reliable
        </span>
      </div>
      <p className="mt-1 text-xs text-slate-500">{source.publisher || 'Unknown publisher'}</p>
    </a>
  )
}
