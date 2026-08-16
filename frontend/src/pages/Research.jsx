import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import ResearchProgress from '../components/ResearchProgress'
import ResearchReport from '../components/ResearchReport'
import EvidencePanel from '../components/EvidencePanel'
import SourceCard from '../components/SourceCard'
import { getResearchStatus, getResearchDetail, getSources } from '../services/api'

const POLL_INTERVAL_MS = 2000

/**
 * Screen 2 -> Screen 3: polls /research/:id/status until the pipeline
 * finishes, then fetches the full detail + sources and renders the
 * report with an evidence/citations panel alongside it.
 */
export default function Research() {
  const { researchId } = useParams()
  const [status, setStatus] = useState('pending')
  const [progressStep, setProgressStep] = useState('queued')
  const [errorMessage, setErrorMessage] = useState(null)
  const [detail, setDetail] = useState(null)
  const [sources, setSources] = useState([])
  const pollRef = useRef(null)

  useEffect(() => {
    let cancelled = false

    async function poll() {
      try {
        const s = await getResearchStatus(researchId)
        if (cancelled) return
        setStatus(s.status)
        setProgressStep(s.progress_step)
        setErrorMessage(s.error_message)

        if (s.status === 'completed' || s.status === 'failed') {
          clearInterval(pollRef.current)
          if (s.status === 'completed') {
            const [d, src] = await Promise.all([getResearchDetail(researchId), getSources(researchId)])
            if (!cancelled) {
              setDetail(d)
              setSources(src)
            }
          }
        }
      } catch (err) {
        clearInterval(pollRef.current)
        setErrorMessage('Lost connection while checking research status.')
        setStatus('failed')
      }
    }

    poll()
    pollRef.current = setInterval(poll, POLL_INTERVAL_MS)
    return () => {
      cancelled = true
      clearInterval(pollRef.current)
    }
  }, [researchId])

  if (status !== 'completed') {
    return (
      <div className="py-20 px-4">
        <ResearchProgress status={status} progressStep={progressStep} errorMessage={errorMessage} />
      </div>
    )
  }

  return (
    <div className="py-12 px-4">
      <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-8 max-w-6xl mx-auto">
        <ResearchReport report={detail?.report} query={detail?.query} />

        <aside className="space-y-4">
          <EvidencePanel
            title="Why this report?"
            sourcesCount={sources.length}
            evidenceCount={detail?.questions?.length || 0}
            confidence={detail?.report?.confidence_score}
          />

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm font-semibold text-slate-800 mb-3">Sources</p>
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {sources.map((s, i) => (
                <SourceCard key={s.id} source={s} index={i} />
              ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}
