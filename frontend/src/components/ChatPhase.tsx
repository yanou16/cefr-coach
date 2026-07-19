import { useState, useRef, useEffect } from 'react'
import type { ChatMessage } from '../hooks/useAppReducer'

interface Props {
  history: ChatMessage[]
  level: string | null
  loading: boolean
  onSend: (text: string) => void
  onBack: () => void
}

export default function ChatPhase({ history, level, loading, onSend, onBack }: Props) {
  const [msg, setMsg] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history])

  function handleSend(e: React.FormEvent) {
    e.preventDefault()
    if (!msg.trim() || loading) return
    onSend(msg)
    setMsg('')
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend(e as unknown as React.FormEvent)
    }
  }

  return (
    <div className="phase chat-phase">
      <div className="chat-header">
        <button className="chat-back" onClick={onBack} aria-label="Back to exercises">←</button>
        <div className="chat-header__info">
          <strong>CEFR Coach</strong>
          {level && <span className="chat-header__lvl">Tuned to {level}</span>}
        </div>
      </div>

      <div className="chat-log">
        {history.length === 0 && (
          <div className="chat-empty">
            <p>Ask your tutor anything — grammar questions, explanations, more examples.</p>
            <p className="chat-empty__hint">Replies are calibrated to your {level ?? 'current'} level.</p>
          </div>
        )}
        {history.map((m, i) => (
          <div key={i} className={`chat-msg chat-msg--${m.role}`}>
            <span className="chat-msg__role">{m.role === 'user' ? 'You' : 'Tutor'}</span>
            <p className="chat-msg__text">{m.content}</p>
          </div>
        ))}
        {loading && (
          <div className="chat-msg chat-msg--assistant">
            <span className="chat-msg__role">Tutor</span>
            <p className="chat-msg__text chat-typing">
              <span /><span /><span />
            </p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="chat-form">
        <textarea
          className="chat-input"
          value={msg}
          onChange={e => setMsg(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask anything… (Enter to send, Shift+Enter for new line)"
          disabled={loading}
          rows={2}
        />
        <button
          type="submit"
          className="btn-p chat-send"
          disabled={!msg.trim() || loading}
          aria-label="Send"
        >
          ↑
        </button>
      </form>
    </div>
  )
}
