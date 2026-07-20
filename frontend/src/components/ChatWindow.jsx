import { useState } from 'react'
import Button from './Button'

export default function ChatWindow({ messages, onSend, isAnswering = false, disabled = false }) {
  const [draft, setDraft] = useState('')

  const submit = (e) => {
    e.preventDefault()
    if (!draft.trim() || disabled || isAnswering) return
    onSend?.(draft.trim())
    setDraft('')
  }

  return (
    <div className="panel flex h-[520px] flex-col">
      <div aria-live="polite" className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-xl px-3.5 py-2.5 text-sm ${
                m.role === 'user'
                  ? 'bg-safety-orange text-navy-950'
                  : 'bg-navy-700 text-slate-100'
              }`}
            >
              <p>{m.text}</p>
              {m.citations?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {m.citations.map((c, i) => (
                    <a
                      key={i}
                      href="#"
                      onClick={(e) => e.preventDefault()}
                      className="focus-ring rounded-full border border-navy-500 bg-navy-800/80 px-2 py-0.5 text-[11px] text-slate-300 hover:border-safety-orange/60 hover:text-safety-orange"
                    >
                      {c.title}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {isAnswering && (
          <div className="flex justify-start">
            <div className="flex items-center gap-1 rounded-xl bg-navy-700 px-3.5 py-2.5">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" />
            </div>
          </div>
        )}
      </div>
      <form onSubmit={submit} className="flex items-center gap-2 border-t border-border p-3">
        <label htmlFor="compliance-question" className="sr-only">
          Ask a compliance question
        </label>
        <input
          id="compliance-question"
          type="text"
          value={draft}
          disabled={disabled}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={disabled ? 'Ingest a document to start asking questions' : 'Ask a compliance question…'}
          className="focus-ring flex-1 rounded-lg border border-border bg-navy-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 disabled:opacity-50"
        />
        <Button type="submit" disabled={disabled} loading={isAnswering}>
          Ask
        </Button>
      </form>
    </div>
  )
}
