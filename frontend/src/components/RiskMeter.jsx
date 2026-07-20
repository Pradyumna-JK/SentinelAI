const LEVEL_STYLES = {
  Low: { ring: 'stroke-safety-green', text: 'text-safety-green', chip: 'bg-safety-green/15 text-safety-green' },
  Medium: { ring: 'stroke-safety-yellow', text: 'text-safety-yellow', chip: 'bg-safety-yellow/15 text-safety-yellow' },
  High: { ring: 'stroke-safety-orange', text: 'text-safety-orange', chip: 'bg-safety-orange/15 text-safety-orange' },
  Critical: { ring: 'stroke-safety-red', text: 'text-safety-red', chip: 'bg-safety-red/15 text-safety-red' },
}

export default function RiskMeter({ score, level, zoneName, siteName, activeAlerts = 0, onClick }) {
  const styles = LEVEL_STYLES[level] || LEVEL_STYLES.Low
  const circumference = 2 * Math.PI * 26
  const offset = circumference - (Math.min(Math.max(score, 0), 100) / 100) * circumference
  const interactive = Boolean(onClick)
  const Tag = interactive ? 'button' : 'div'

  return (
    <Tag
      onClick={onClick}
      aria-label={`${zoneName}, risk level ${level}, score ${score}`}
      className={`panel flex w-full items-center gap-4 p-4 text-left transition-colors ${
        interactive ? 'hover:border-safety-orange/50 focus-ring cursor-pointer' : ''
      }`}
    >
      <svg viewBox="0 0 64 64" className="h-16 w-16 shrink-0 -rotate-90">
        <circle cx="32" cy="32" r="26" strokeWidth="6" className="fill-none stroke-navy-700" />
        <circle
          cx="32"
          cy="32"
          r="26"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={`fill-none transition-all duration-700 ${styles.ring}`}
        />
      </svg>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-slate-100">{zoneName}</p>
        {siteName && <p className="truncate text-xs text-slate-500">{siteName}</p>}
        <div className="mt-1.5 flex items-center gap-2">
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles.chip}`}>{level}</span>
          <span className={`text-sm font-semibold tabular-nums ${styles.text}`}>{score}</span>
          {activeAlerts > 0 && (
            <span className="text-xs text-slate-500">
              {activeAlerts} alert{activeAlerts > 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>
    </Tag>
  )
}
