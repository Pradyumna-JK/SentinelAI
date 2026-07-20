const SHAPES = {
  card: 'h-24 w-full rounded-xl',
  row: 'h-10 w-full rounded-lg',
  chart: 'h-64 w-full rounded-xl',
  text: 'h-4 w-2/3 rounded',
}

export default function LoadingSkeleton({ shape = 'row', count = 1, className = '' }) {
  return (
    <div className="flex flex-col gap-2" aria-hidden="true">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`animate-pulse bg-navy-700/70 ${SHAPES[shape]} ${className}`}
        />
      ))}
    </div>
  )
}
