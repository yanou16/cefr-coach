import { useState } from 'react'

interface Props {
  samplesUsed: number
  loading: boolean
  onSubmit: (text: string) => void
}

const SKILL_GAPS = [
  'present perfect vs past simple',
  'countable and uncountable nouns',
  'passive voice',
  'modal verbs',
  'conditionals',
  'relative clauses',
  'phrasal verbs',
  'articles (a, an, the)',
]

export default function AssessPhase({ samplesUsed, loading, onSubmit }: Props) {
  const [text, setText] = useState('')

  const wordCount = text.trim().length === 0
    ? 0
    : text.trim().split(/\s+/).filter(Boolean).length

  const isValid = wordCount >= 20 && wordCount <= 150

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!isValid || loading) return
    onSubmit(text)
    setText('')
  }

  const tip = SKILL_GAPS[Math.floor(Date.now() / 60000) % SKILL_GAPS.length]

  return (
    <div className="phase assess-phase">
      <div className="phase__header">
        {samplesUsed === 0 ? (
          <>
            <p className="eyebrow">Step 1 of 2 — Assessment</p>
            <h2 className="phase__title">Write your first sample</h2>
            <p className="phase__sub">
              Write 20–150 words in English on any topic — your opinion, your day, a story.
              The classifier reads your vocabulary and grammar, not the subject.
            </p>
          </>
        ) : (
          <>
            <p className="eyebrow">Step 2 of 2 — One more sample</p>
            <h2 className="phase__title">Write a second sample</h2>
            <p className="phase__sub">
              One more writing sample gives the rolling window enough signal to place you accurately.
              Try a different topic for better coverage.
            </p>
          </>
        )}
      </div>

      <form onSubmit={handleSubmit} className="assess-form">
        <textarea
          className="assess-ta"
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder={
            samplesUsed === 0
              ? 'Write anything — your thoughts on technology, a recent trip, your favourite book…'
              : 'Try a different topic this time — maybe describe a challenge you faced recently…'
          }
          disabled={loading}
          aria-label="English writing sample"
        />
        <div className="assess-meta">
          <span className={wordCount > 150 ? 'assess-meta__wc--over' : ''}>
            {wordCount} / 150 words
          </span>
          <span className="assess-meta__hint">Minimum 20 words</span>
        </div>
        <button
          type="submit"
          className="btn-p"
          disabled={!isValid || loading}
        >
          {loading ? 'Analysing…' : 'Analyse my level →'}
        </button>
      </form>

      <div className="assess-tip">
        <span className="eyebrow" style={{ marginBottom: 0 }}>Tip</span>
        <p>Try writing about "<strong>{tip}</strong>" — it exercises the grammar the tutor will target.</p>
      </div>
    </div>
  )
}
