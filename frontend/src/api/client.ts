const BASE = 'http://localhost:8001'

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const json = await r.json()
  if (!r.ok) throw new Error(json.detail ?? `HTTP ${r.status}`)
  return json as T
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`)
  const json = await r.json()
  if (!r.ok) throw new Error(json.detail ?? `HTTP ${r.status}`)
  return json as T
}

// ── Response types ─────────────────────────────────────────────────────────

export interface Smoothed {
  level: string | null
  band: string | null
  confidence: number | null
  samples_used: number
  needs_more_data: boolean
  session_id: string
}

export interface ClassifyResponse {
  level: string | null
  confidence: number | null
  processing_time_ms: number | null
  low_confidence: boolean
  advanced_plus: boolean
  error: string | null
  smoothed: Smoothed | null
}

export interface SessionState {
  session_id: string
  state: string
  level: string | null
  streak: number
  total_exercises: number
  skill_focus: string | null
  samples_used: number
  created_at: string
}

export interface Exercise {
  exercise_type: string
  instruction: string
  content: string | string[]
  expected_level: string
  target_skill: string
  rubric: { key_points: string[]; common_errors_to_watch: string[] }
  model_answer: string | string[]
  chunk_ids_used: string[]
  _model: string
}

export interface ExerciseResponse {
  session_id: string
  level: string
  exercise: Exercise
  chunks_used: number
  state: string
}

export interface FeedbackError {
  error: string
  correction: string
  explanation: string
}

export interface Feedback {
  correct: boolean
  score: number
  summary: string
  errors: FeedbackError[]
  strengths: string[]
  next_focus: string
  _model: string
}

export interface FeedbackResponse {
  session_id: string
  feedback: Feedback
  streak: number
  classified: boolean
  level: string
  level_changed: boolean
  harder: boolean
  state: string
}

export interface ChatResponse {
  session_id: string
  level: string
  reply: string
  turns: number
}

// ── API surface ────────────────────────────────────────────────────────────

export const api = {
  classifySession: (text: string, sessionId: string) =>
    post<ClassifyResponse>('/classify/session', { text, session_id: sessionId }),

  getSession: (sessionId: string) =>
    get<SessionState>(`/session/${sessionId}`),

  generateExercise: (sessionId: string, skillGap = 'general grammar') =>
    post<ExerciseResponse>('/exercise', { session_id: sessionId, skill_gap: skillGap }),

  submitFeedback: (sessionId: string, learnerAnswer: string) =>
    post<FeedbackResponse>('/feedback', { session_id: sessionId, learner_answer: learnerAnswer }),

  chat: (sessionId: string, message: string) =>
    post<ChatResponse>('/chat', { session_id: sessionId, message }),
}
