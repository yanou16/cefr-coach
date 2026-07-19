import { useEffect, useRef } from 'react'

const LEVEL_NAMES: Record<string, string> = {
  A1: 'Beginner', A2: 'Elementary', B1: 'Intermediate',
  B2: 'Upper-Inter.', C1: 'Advanced', C2: 'Mastery',
}

const LEVEL_BAR: Record<string, number> = {
  A1: 8, A2: 25, B1: 42, B2: 58, C1: 75, C2: 92,
}

interface Props {
  level: string | null
  confidence: number | null
  samplesUsed: number
  levelReady: boolean
  compact?: boolean // nav variant vs hero-card variant
}

export default function LevelBadge({ level, confidence, samplesUsed, levelReady, compact }: Props) {
  const prevLevel = useRef<string | null>(null)
  const codeRef = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (level && level !== prevLevel.current && codeRef.current) {
      codeRef.current.classList.remove('lbadge-pop')
      void codeRef.current.offsetWidth // reflow to restart animation
      codeRef.current.classList.add('lbadge-pop')
      prevLevel.current = level
    }
  }, [level])

  if (compact) {
    // ── Nav pill variant ───────────────────────────────────────────────────
    if (!levelReady) {
      return (
        <div className="lbadge-pill lbadge-pill--pending" title={`${samplesUsed}/2 samples`}>
          <span className="lbadge-pill__dot" />
          Assessing… {samplesUsed}/2
        </div>
      )
    }
    return (
      <div className="lbadge-pill" title={`Confidence: ${Math.round((confidence ?? 0) * 100)}%`}>
        <span ref={codeRef} className="lbadge-pill__code">{level}</span>
        <span className="lbadge-pill__name">{LEVEL_NAMES[level!]}</span>
        <span className="lbadge-pill__conf">{Math.round((confidence ?? 0) * 100)}%</span>
      </div>
    )
  }

  // ── Full card variant ────────────────────────────────────────────────────
  const barPct = level ? LEVEL_BAR[level] ?? 0 : 0
  const confPct = Math.round((confidence ?? 0) * 100)

  return (
    <div className="lcard">
      <p className="lcard__label">Your current level</p>
      {!levelReady ? (
        <div className="lcard__assessing">
          <div className="lcard__dots">
            {[0, 1, 2].map(i => (
              <span key={i} className="lcard__dot" style={{ animationDelay: `${i * 0.2}s` }} />
            ))}
          </div>
          <p className="lcard__sub">Analysing sample {samplesUsed + 1} of 2…</p>
          <p className="lcard__hint">Write at least 20 words per sample.</p>
        </div>
      ) : (
        <>
          <div className="lcard__badge">
            <span ref={codeRef} className="lcard__code">{level}</span>
            <span className="lcard__name">{LEVEL_NAMES[level!]}</span>
          </div>
          <div className="lcard__bar-track">
            <div className="lcard__bar-fill" style={{ width: `${barPct}%` }} />
          </div>
          <p className="lcard__conf">Confidence — {confPct}%</p>
        </>
      )}
    </div>
  )
}
