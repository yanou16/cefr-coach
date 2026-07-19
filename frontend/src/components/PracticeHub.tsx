interface Props {
  level: string | null
  streak: number
  totalExercises: number
  loading: boolean
  onExercise: () => void
  onChat: () => void
  onAssess: () => void
}

const LEVEL_LABELS: Record<string, string> = {
  A1: 'Beginner', A2: 'Elementary', B1: 'Intermediate',
  B2: 'Upper-Intermediate', C1: 'Advanced', C2: 'Mastery',
}

export default function PracticeHub({ level, streak, totalExercises, loading, onExercise, onChat, onAssess }: Props) {
  return (
    <div className="phase practice-phase">
      <div className="prac-hero">
        <div className="prac-lvl-code">{level}</div>
        <div className="prac-lvl-name">{level ? LEVEL_LABELS[level] : ''}</div>
      </div>

      <div className="prac-stats">
        <div className="prac-stat">
          <span className="prac-stat__val">{totalExercises}</span>
          <span className="prac-stat__lbl">Exercises done</span>
        </div>
        <div className="prac-stat">
          <span className="prac-stat__val">{streak}</span>
          <span className="prac-stat__lbl">Current streak</span>
        </div>
      </div>

      <div className="prac-ctas">
        <button className="btn-p" onClick={onExercise} disabled={loading}>
          {loading ? 'Generating exercise…' : 'Start exercise →'}
        </button>
        <button className="btn-s" onClick={onChat}>
          Chat with tutor
        </button>
        <button className="btn-ghost" onClick={onAssess}>
          Re-assess my level
        </button>
      </div>

      <p className="prac-tip">
        Each exercise is one level above yours (<em>i+1</em>) for optimal acquisition.
        {streak >= 2 && ` After ${streak} correct answers the difficulty increases.`}
      </p>
    </div>
  )
}
