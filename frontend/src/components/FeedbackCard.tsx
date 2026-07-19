import type { Feedback } from '../api/client'

interface Props {
  feedback: Feedback
  levelChanged: boolean
  level: string | null
  streak: number
  onNext: () => void
  onChat: () => void
}

export default function FeedbackCard({ feedback, levelChanged, level, streak, onNext, onChat }: Props) {
  const score = Math.min(100, Math.max(0, feedback.score))
  const color = score >= 70 ? 'var(--accent)' : score >= 40 ? '#e8c840' : '#e06060'

  return (
    <div className="phase feedback-phase">
      {levelChanged && level && (
        <div className="fb-level-change">
          Level updated → <strong>{level}</strong>
        </div>
      )}

      <div className="fb-score">
        <svg viewBox="0 0 100 100" className="fb-score__ring">
          <circle cx="50" cy="50" r="42" />
          <circle
            cx="50" cy="50" r="42"
            style={{
              strokeDashoffset: `${264 - (264 * score) / 100}`,
              stroke: color,
            }}
          />
        </svg>
        <div className="fb-score__num">
          <span>{score}</span>
          <small>/100</small>
        </div>
      </div>

      <p className="fb-summary">{feedback.summary}</p>

      {streak >= 3 && (
        <div className="fb-streak">
          {streak}-exercise streak — difficulty increasing!
        </div>
      )}

      {feedback.strengths.length > 0 && (
        <div className="fb-section">
          <h4 className="fb-section__title fb-section__title--good">Strengths</h4>
          <ul className="fb-list fb-list--good">
            {feedback.strengths.map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </div>
      )}

      {feedback.errors.length > 0 && (
        <div className="fb-section">
          <h4 className="fb-section__title fb-section__title--err">Errors to fix</h4>
          <ul className="fb-list fb-list--err">
            {feedback.errors.map((e, i) => (
              <li key={i}>
                <span className="fb-err__label">{e.error}</span>
                <span className="fb-err__corr">→ {e.correction}</span>
                <span className="fb-err__exp">{e.explanation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="fb-next-focus">
        Next focus: <strong>{feedback.next_focus}</strong>
      </div>

      <div className="fb-actions">
        <button className="btn-p" onClick={onNext}>Next exercise →</button>
        <button className="btn-s" onClick={onChat}>Ask tutor</button>
      </div>
    </div>
  )
}
