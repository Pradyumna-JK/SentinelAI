import StatusBadge from './StatusBadge'

export default function CameraTile({ camera, detectionCount = 0, onExpand }) {
  const isActive = camera.status === 'active'

  return (
    <button
      onClick={() => onExpand?.(camera)}
      aria-label={`${camera.name}, ${camera.status}`}
      className="focus-ring group relative aspect-video w-full overflow-hidden rounded-xl border border-border bg-navy-950 text-left"
    >
      {isActive ? (
        <div className="flex h-full w-full items-center justify-center bg-[radial-gradient(circle_at_30%_20%,#1b2740,transparent_60%)]">
          <div className="absolute inset-0 opacity-20 [background-image:repeating-linear-gradient(0deg,#25334f_0px,#25334f_1px,transparent_1px,transparent_28px)]" />
          {detectionCount > 0 && (
            <span className="absolute left-2.5 top-2.5 rounded border border-safety-orange/60 bg-safety-orange/15 px-1.5 py-0.5 text-[10px] font-medium text-safety-orange">
              {detectionCount} detection{detectionCount > 1 ? 's' : ''}
            </span>
          )}
          <svg className="h-8 w-8 text-navy-600 transition-colors group-hover:text-safety-orange/70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.55-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.45.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </div>
      ) : (
        <div className="flex h-full w-full flex-col items-center justify-center gap-1 bg-navy-900 text-slate-600">
          <svg className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18.364 5.636L5.636 18.364M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <span className="text-xs">Feed unavailable</span>
        </div>
      )}
      <div className="absolute inset-x-0 bottom-0 flex items-center justify-between gap-2 bg-gradient-to-t from-navy-950/90 to-transparent px-2.5 py-2">
        <span className="truncate text-xs font-medium text-slate-100">{camera.name}</span>
        <StatusBadge status={camera.status} variant="device" />
      </div>
    </button>
  )
}
