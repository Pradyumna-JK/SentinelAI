import { useEffect, useState } from 'react'

/**
 * Simulates a live WebSocket/SSE feed (docs/06_SYSTEM_WORKFLOW.md §5) by
 * gently jittering numeric fields on an interval. Swap the interval body for
 * a real WebSocket subscription once the backend exists — the return shape
 * (the live-updated data) stays the same for consumers.
 */
export function useRealtimeFeed(initialData, { intervalMs = 6000, jitter } = {}) {
  const [data, setData] = useState(initialData)

  useEffect(() => {
    setData(initialData)
  }, [initialData])

  useEffect(() => {
    if (!jitter) return undefined
    const id = setInterval(() => {
      setData((prev) => jitter(prev))
    }, intervalMs)
    return () => clearInterval(id)
  }, [intervalMs, jitter])

  return data
}
