/**
 * Screen 2: Research progress. Maps the backend's `progress_step`
 * (queued -> creating_research_questions -> searching_sources ->
 * validating_evidence -> generating_report -> done) onto a checklist
 * so the pipeline "feels alive" while the background task runs.
 */
const STEP_ORDER = [
  { key: 'queued', label: 'Understanding request' },
  { key: 'creating_research_questions', label: 'Creating research questions' },
  { key: 'searching_sources', label: 'Searching sources' },
  { key: 'validating_evidence', label: 'Validating evidence' },
  { key: 'generating_report', label: 'Generating report' },
  { key: 'done', label: 'Final verification' },
]

export default function ResearchProgress({ status, progressStep, errorMessage }) {
  const currentIndex = STEP_ORDER.findIndex((s) => s.key === progressStep)

  if (status === 'failed') {
    return (
      <div className="max-w-xl mx-auto rounded-xl border border-conflict/30 bg-conflict/5 p-6">
        <p className="font-semibold text-conflict">Research failed</p>
        <p className="text-sm text-slate-600 mt-1">{errorMessage || 'An unexpected error occurred.'}</p>
      </div>
    )
  }

  return (
    <div className="max-w-xl mx-auto">
      <p className="text-center text-lg font-medium text-slate-700 mb-6">Researching...</p>
      <ul className="space-y-3">
        {STEP_ORDER.map((step, i) => {
          const isDone = currentIndex > i || status === 'completed'
          const isActive = currentIndex === i && status !== 'completed'
          return (
            <li key={step.key} className="flex items-center gap-3">
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold
                  ${isDone ? 'bg-accent text-white' : isActive ? 'border-2 border-accent text-accent' : 'border border-slate-300 text-slate-300'}`}
              >
                {isDone ? '✓' : isActive ? '●' : '○'}
              </span>
              <span className={isDone || isActive ? 'text-slate-800' : 'text-slate-400'}>
                {step.label}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
