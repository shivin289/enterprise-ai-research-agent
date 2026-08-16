import ConfidenceBadge from './ConfidenceBadge'

/**
 * Screen 3: renders the synthesized markdown report. We keep this a
 * lightweight custom renderer (headings/bullets/bold + [Source N]
 * highlighting) rather than pulling in a full markdown lib, since the
 * synthesis service always emits a predictable structure.
 */
export default function ResearchReport({ report, query }) {
  if (!report) return null

  const lines = report.report_content.split('\n')

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-ink">{query}</h1>
        <ConfidenceBadge score={report.confidence_score} />
      </div>

      <article className="prose prose-slate max-w-none">
        {lines.map((line, i) => {
          if (line.startsWith('# ')) return null // title already shown above
          if (line.startsWith('## ')) {
            return (
              <h2 key={i} className="text-lg font-semibold text-slate-800 mt-6 mb-2 border-b border-slate-200 pb-1">
                {line.replace('## ', '')}
              </h2>
            )
          }
          if (line.startsWith('- ')) {
            return (
              <p key={i} className="text-sm text-slate-700 ml-4 mb-1">
                {renderInline(line.replace(/^- /, ''))}
              </p>
            )
          }
          if (line.startsWith('  - ')) {
            return (
              <p key={i} className="text-xs text-slate-500 ml-8 mb-1 italic">
                {line.replace(/^ {2}- /, '')}
              </p>
            )
          }
          if (line.trim() === '') return null
          if (line.startsWith('**')) {
            return (
              <p key={i} className="text-sm font-semibold text-slate-800 mt-4">
                {line.replaceAll('**', '')}
              </p>
            )
          }
          return (
            <p key={i} className="text-sm text-slate-700 mb-2 leading-relaxed">
              {line}
            </p>
          )
        })}
      </article>
    </div>
  )
}

// Highlights [Source N] citation markers inline within a line of text.
function renderInline(text) {
  const parts = text.split(/(\[Source \d+\])/g)
  return parts.map((part, i) =>
    /^\[Source \d+\]$/.test(part) ? (
      <span key={i} className="mx-0.5 rounded bg-accentSoft px-1.5 py-0.5 text-xs font-medium text-accent">
        {part}
      </span>
    ) : (
      <span key={i}>{part}</span>
    ),
  )
}
