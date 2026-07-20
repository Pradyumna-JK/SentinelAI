import Button from './Button'

const SEVERITY_STYLES = {
  Critical: { dot: 'bg-safety-red', text: 'text-safety-red', border: 'border-l-safety-red' },
  High: { dot: 'bg-safety-orange', text: 'text-safety-orange', border: 'border-l-safety-orange' },
  Medium: { dot: 'bg-safety-yellow', text: 'text-safety-yellow', border: 'border-l-safety-yellow' },
  Low: { dot: 'bg-safety-green', text: 'text-safety-green', border: 'border-l-safety-green' },
}

function timeAgo(iso) {
  const diffMs = Date.now() - new Date(iso).getTime()
  const mins = Math.max(1, Math.round(diffMs / 60000))
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.round(mins / 60)
  return `${hrs}h ago`
}

export default function AlertCard({ alert, onAcknowledge, compact = false }) {
  const styles = SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.Low
  const acknowledged = Boolean(alert.acknowledged_by)

  return (
    <div className={`panel border-l-4 p-4 ${styles.border} ${compact ? 'text-sm' : ''}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${styles.dot}`} aria-hidden="true" />
            <span className={`text-xs font-semibold uppercase tracking-wide ${styles.text}`}>
              {alert.severity} alert
            </span>
            <span className="text-xs text-slate-500">· {alert.zone_name}</span>
          </div>
          <p className="mt-1.5 text-sm text-slate-200">{alert.rationale}</p>
          <p className="mt-1 text-xs text-slate-500">{timeAgo(alert.created_at)}</p>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between gap-2">
        {acknowledged ? (
          <span className="text-xs text-slate-500">Acknowledged by {alert.acknowledged_by}</span>
        ) : (
          <span className="text-xs text-safety-yellow">Unacknowledged</span>
        )}
        {!acknowledged && onAcknowledge && (
          <Button size="sm" variant="secondary" onClick={() => onAcknowledge(alert.id)}>
            Acknowledge
          </Button>
        )}
      </div>
    </div>
  )
}
