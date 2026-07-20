const VARIANTS = {
  default: 'bg-navy-800 border border-border',
  elevated: 'bg-navy-800 border border-border shadow-panel',
  outlined: 'bg-transparent border border-border',
}

export default function Card({
  title,
  subtitle,
  action,
  children,
  variant = 'default',
  onClick,
  className = '',
}) {
  const interactive = Boolean(onClick)
  const Tag = interactive ? 'button' : 'div'

  return (
    <Tag
      onClick={onClick}
      className={`w-full rounded-xl p-4 text-left transition-colors ${VARIANTS[variant]} ${
        interactive ? 'hover:border-safety-orange/50 focus-ring cursor-pointer' : ''
      } ${className}`}
    >
      {(title || action) && (
        <div className="mb-3 flex items-start justify-between gap-2">
          <div>
            {title && <h3 className="text-sm font-semibold text-slate-100">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </Tag>
  )
}
