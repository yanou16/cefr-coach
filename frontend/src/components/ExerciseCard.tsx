import { useState } from 'react'
import type { Exercise } from '../api/client'

interface Props {
  exercise: Exercise
  loading: boolean
  onSubmit: (answer: string) => void
}

const TYPE_LABEL: Record<string, string> = {
  fill_in_the_blank: 'Fill in the blank',
  error_correction: 'Error correction',
  transformation: 'Sentence transformation',
  open_writing: 'Short writing',
  multiple_choice: 'Multiple choice',
}

export default function ExerciseCard({ exercise, loading, onSubmit }: Props) {
  const [answer, setAnswer] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!answer.trim() || loading) return
    onSubmit(answer)
  }

  const content = Array.isArray(exercise.content)
    ? exercise.content.join('\n')
    : exercise.content

  return (
    <div className="phase exercise-phase">
      <div className="ex-card">
        <div className="ex-card__meta">
          <span className="ex-tag">{TYPE_LABEL[exercise.exercise_type] ?? exercise.exercise_type}</span>
          <span className="ex-skill">{exercise.target_skill}</span>
          <span className="ex-lvl">{exercise.expected_level}</span>
        </div>

        <h3 className="ex-card__instr">{exercise.instruction}</h3>

        <div className="ex-card__content">
          {content.split('\n').map((line, i) => (
            <p key={i}>{line}</p>
          ))}
        </div>

        {exercise.rubric?.key_points?.length > 0 && (
          <details className="ex-card__rubric">
            <summary>Scoring hints</summary>
            <ul>
              {exercise.rubric.key_points.map((pt, i) => (
                <li key={i}>{pt}</li>
              ))}
            </ul>
          </details>
        )}
      </div>

      <form onSubmit={handleSubmit} className="ex-form">
        <label className="ex-form__label" htmlFor="ex-answer">Your answer</label>
        <textarea
          id="ex-answer"
          className="assess-ta"
          value={answer}
          onChange={e => setAnswer(e.target.value)}
          placeholder="Write your answer here…"
          disabled={loading}
          rows={4}
        />
        <button
          type="submit"
          className="btn-p"
          disabled={!answer.trim() || loading}
        >
          {loading ? 'Evaluating…' : 'Submit answer →'}
        </button>
      </form>
    </div>
  )
}
