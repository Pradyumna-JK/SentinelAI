const TYPE_DOT = {
  detection: 'bg-safety-orange',
  evidence: 'bg-safety-blue',
  default: 'bg-slate-500',
}

export default function Timeline({ events = [], orientation = 'vertical' }) {
  if (events.length === 0) {
    return <p className="text-sm text-slate-500">No events yet.</p>
  }

  return (
    <ol className={`flex ${orientation === 'vertical' ? 'flex-col gap-4' : 'flex-row gap-6 overflow-x-auto'}`}>
      {events.map((event) => (
        <li key={event.id} className="flex items-start gap-3">
          <span
            className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${TYPE_DOT[event.type] || TYPE_DOT.default}`}
            aria-hidden="true"
          />
          <div className="min-w-0">
            <p className="text-sm text-slate-200">{event.label}</p>
            <time dateTime={event.timestamp} className="text-xs text-slate-500">
              {new Date(event.timestamp).toLocaleString()}
            </time>
          </div>
        </li>
      ))}
    </ol>
  )
}
