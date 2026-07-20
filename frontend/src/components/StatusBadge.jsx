const TONES = {
  // agent / device health
  Healthy: 'bg-safety-green/15 text-safety-green border-safety-green/30',
  active: 'bg-safety-green/15 text-safety-green border-safety-green/30',
  Degraded: 'bg-safety-yellow/15 text-safety-yellow border-safety-yellow/30',
  Offline: 'bg-safety-red/15 text-safety-red border-safety-red/30',
  offline: 'bg-safety-red/15 text-safety-red border-safety-red/30',
  inactive: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
  // incident status
  draft: 'bg-safety-yellow/15 text-safety-yellow border-safety-yellow/30',
  approved: 'bg-safety-green/15 text-safety-green border-safety-green/30',
}

export default function StatusBadge({ status, variant = 'device', className = '' }) {
  const tone = TONES[status] || 'bg-slate-500/15 text-slate-300 border-slate-500/30'
  return (
    <span
      role="status"
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${tone} ${className}`}
      data-variant={variant}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
      {status}
    </span>
  )
}
