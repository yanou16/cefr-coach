import { useReducer } from 'react'
import type { Exercise, Feedback, ClassifyResponse, FeedbackResponse } from '../api/client'

export type Phase = 'landing' | 'assess' | 'practice' | 'exercise' | 'feedback' | 'chat'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AppState {
  sessionId: string
  phase: Phase
  // level tracking
  level: string | null
  confidence: number | null
  samplesUsed: number
  levelReady: boolean
  // exercise flow
  exercise: Exercise | null
  feedback: Feedback | null
  levelChanged: boolean
  streak: number
  totalExercises: number
  // chat
  chatHistory: ChatMessage[]
  // ui
  loading: boolean
  error: string | null
}

type Action =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLASSIFIED'; payload: ClassifyResponse }
  | { type: 'EXERCISE_READY'; payload: Exercise }
  | { type: 'FEEDBACK_RECEIVED'; payload: FeedbackResponse }
  | { type: 'CHAT_MESSAGE'; payload: { user: string; reply: string } }
  | { type: 'GO_APP' }
  | { type: 'GO_LANDING' }
  | { type: 'GO_CHAT' }
  | { type: 'NEXT_EXERCISE' }
  | { type: 'GO_ASSESS' }

function makeSessionId() {
  return `web-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
}

const init: AppState = {
  sessionId: makeSessionId(),
  phase: 'landing',
  level: null,
  confidence: null,
  samplesUsed: 0,
  levelReady: false,
  exercise: null,
  feedback: null,
  levelChanged: false,
  streak: 0,
  totalExercises: 0,
  chatHistory: [],
  loading: false,
  error: null,
}

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload, error: null }

    case 'SET_ERROR':
      return { ...state, loading: false, error: action.payload }

    case 'CLASSIFIED': {
      const sm = action.payload.smoothed
      const levelReady = sm != null && !sm.needs_more_data
      return {
        ...state,
        loading: false,
        level: sm?.level ?? action.payload.level,
        confidence: sm?.confidence ?? action.payload.confidence,
        samplesUsed: sm?.samples_used ?? state.samplesUsed + 1,
        levelReady,
        phase: levelReady ? 'practice' : 'assess',
      }
    }

    case 'EXERCISE_READY':
      return {
        ...state,
        loading: false,
        exercise: action.payload,
        feedback: null,
        phase: 'exercise',
        totalExercises: state.totalExercises + 1,
      }

    case 'FEEDBACK_RECEIVED':
      return {
        ...state,
        loading: false,
        feedback: action.payload.feedback,
        level: action.payload.level,
        levelChanged: action.payload.level_changed,
        streak: action.payload.streak,
        phase: 'feedback',
      }

    case 'CHAT_MESSAGE':
      return {
        ...state,
        loading: false,
        chatHistory: [
          ...state.chatHistory,
          { role: 'user', content: action.payload.user },
          { role: 'assistant', content: action.payload.reply },
        ],
      }

    case 'GO_APP':
      return { ...state, phase: 'assess' }

    case 'GO_LANDING':
      return { ...init, sessionId: makeSessionId() }

    case 'GO_CHAT':
      return { ...state, phase: 'chat' }

    case 'NEXT_EXERCISE':
      return { ...state, phase: 'practice', exercise: null, feedback: null }

    case 'GO_ASSESS':
      return { ...init, sessionId: makeSessionId() }

    default:
      return state
  }
}

export function useAppReducer() {
  return useReducer(reducer, init)
}
