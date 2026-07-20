import { useToast } from '../hooks/useToast'

const VARIANT_STYLES = {
  success: 'border-safety-green/40 text-safety-green',
  error: 'border-safety-red/40 text-safety-red',
  info: 'border-safety-blue/40 text-safety-blue',
  warning: 'border-safety-yellow/40 text-safety-yellow',
}

export default function ToastContainer() {
  const { toasts, dismiss } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-full max-w-sm flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          role={t.variant === 'error' || t.variant === 'warning' ? 'alert' : 'status'}
          className={`panel pointer-events-auto flex items-start justify-between gap-3 border px-4 py-3 text-sm shadow-panel ${VARIANT_STYLES[t.variant] || VARIANT_STYLES.info}`}
        >
          <span className="text-slate-200">{t.message}</span>
          <button
            onClick={() => dismiss(t.id)}
            aria-label="Dismiss notification"
            className="focus-ring rounded text-slate-500 hover:text-slate-200"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  )
}
