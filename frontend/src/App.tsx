import { useCallback, useEffect, useState } from 'react'
import { useAppReducer } from './hooks/useAppReducer'
import { api } from './api/client'
import LevelBadge from './components/LevelBadge'
import LandingPage from './components/LandingPage'
import AssessPhase from './components/AssessPhase'
import PracticeHub from './components/PracticeHub'
import ExerciseCard from './components/ExerciseCard'
import FeedbackCard from './components/FeedbackCard'
import ChatPhase from './components/ChatPhase'

// Apply persisted theme before first paint
;(function () {
  const t = localStorage.getItem('cefr-theme')
  if (t) document.documentElement.setAttribute('data-theme', t)
})()

export default function App() {
  const [state, dispatch] = useAppReducer()
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const stored = localStorage.getItem('cefr-theme')
    if (stored === 'light' || stored === 'dark') return stored
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  function toggleTheme() {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    localStorage.setItem('cefr-theme', next)
    document.documentElement.setAttribute('data-theme', next)
  }

  const handleClassify = useCallback(async (text: string) => {
    dispatch({ type: 'SET_LOADING', payload: true })
    try {
      const result = await api.classifySession(text, state.sessionId)
      dispatch({ type: 'CLASSIFIED', payload: result })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: (e as Error).message })
    }
  }, [state.sessionId, dispatch])

  const handleExercise = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true })
    try {
      const result = await api.generateExercise(state.sessionId)
      dispatch({ type: 'EXERCISE_READY', payload: result.exercise })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: (e as Error).message })
    }
  }, [state.sessionId, dispatch])

  const handleAnswer = useCallback(async (answer: string) => {
    dispatch({ type: 'SET_LOADING', payload: true })
    try {
      const result = await api.submitFeedback(state.sessionId, answer)
      dispatch({ type: 'FEEDBACK_RECEIVED', payload: result })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: (e as Error).message })
    }
  }, [state.sessionId, dispatch])

  const handleChat = useCallback(async (msg: string) => {
    dispatch({ type: 'SET_LOADING', payload: true })
    try {
      const result = await api.chat(state.sessionId, msg)
      dispatch({ type: 'CHAT_MESSAGE', payload: { user: msg, reply: result.reply } })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: (e as Error).message })
    }
  }, [state.sessionId, dispatch])

  useEffect(() => {
    if (state.phase === 'practice' && !state.exercise && !state.loading) {
      handleExercise()
    }
  }, [state.phase]) // eslint-disable-line react-hooks/exhaustive-deps

  if (state.phase === 'landing') {
    return (
      <LandingPage
        onStart={() => dispatch({ type: 'GO_APP' })}
        theme={theme}
        toggleTheme={toggleTheme}
      />
    )
  }

  return (
    <>
      <nav className="nav">
        <div className="nav-in">
          <span className="nav__brand">CEFR Coach</span>
          <div className="nav__right">
            <LevelBadge
              level={state.level}
              confidence={state.confidence}
              samplesUsed={state.samplesUsed}
              levelReady={state.levelReady}
              compact
            />
            <button
              className="theme-btn"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              {theme === 'dark' ? '☀' : '☽'}
            </button>
          </div>
        </div>
      </nav>

      <main className="app-main">
        {state.error && (
          <div className="error-banner">
            <strong>Error:</strong> {state.error}
          </div>
        )}

        {state.phase === 'assess' && (
          <AssessPhase
            samplesUsed={state.samplesUsed}
            loading={state.loading}
            onSubmit={handleClassify}
          />
        )}

        {state.phase === 'practice' && (
          <PracticeHub
            level={state.level}
            streak={state.streak}
            totalExercises={state.totalExercises}
            loading={state.loading}
            onExercise={handleExercise}
            onChat={() => dispatch({ type: 'GO_CHAT' })}
            onAssess={() => dispatch({ type: 'GO_ASSESS' })}
          />
        )}

        {state.phase === 'exercise' && state.exercise && (
          <ExerciseCard
            exercise={state.exercise}
            loading={state.loading}
            onSubmit={handleAnswer}
          />
        )}

        {state.phase === 'feedback' && state.feedback && (
          <FeedbackCard
            feedback={state.feedback}
            levelChanged={state.levelChanged}
            level={state.level}
            streak={state.streak}
            onNext={() => dispatch({ type: 'NEXT_EXERCISE' })}
            onChat={() => dispatch({ type: 'GO_CHAT' })}
          />
        )}

        {state.phase === 'chat' && (
          <ChatPhase
            history={state.chatHistory}
            level={state.level}
            loading={state.loading}
            onSend={handleChat}
            onBack={() => dispatch({ type: 'NEXT_EXERCISE' })}
          />
        )}
      </main>
    </>
  )
}
