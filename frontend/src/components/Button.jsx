const VARIANTS = {
  primary: 'bg-safety-orange text-navy-950 hover:bg-orange-400 disabled:bg-orange-900/50',
  secondary: 'bg-transparent text-slate-200 border border-border hover:bg-navy-700 disabled:opacity-50',
  danger: 'bg-safety-red text-white hover:bg-red-500 disabled:bg-red-900/50',
  ghost: 'bg-transparent text-slate-300 hover:bg-navy-700 disabled:opacity-40',
}

const SIZES = {
  sm: 'text-xs px-2.5 py-1.5 gap-1.5',
  md: 'text-sm px-4 py-2 gap-2',
  lg: 'text-base px-5 py-2.5 gap-2',
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  type = 'button',
  onClick,
  className = '',
  ...rest
}) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      aria-disabled={disabled || undefined}
      onClick={onClick}
      className={`inline-flex items-center justify-center rounded-lg font-medium transition-colors
        focus-ring disabled:cursor-not-allowed ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...rest}
    >
      {loading && (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  )
}
