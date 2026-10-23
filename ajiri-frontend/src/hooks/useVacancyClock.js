import { useEffect, useState } from 'react'

export function availableAt(job, now) {
  const evidence = job?.publication
  if (!evidence) return false // Missing evidence is unknown, never an active vacancy.
  const end = Date.parse(evidence.available_until || evidence.closes_at || evidence.confirmed_until || '')
  return evidence.status === 'published' && Number.isFinite(end) && end > now
}

// Hide a closing vacancy without polling or downloading another job list.
// The server still rechecks the deadline before any application action.
export function useVacancyClock(jobs) {
  const [now, setNow] = useState(() => Date.now())
  const deadlines = jobs.map((job) => job?.publication?.available_until || job?.publication?.closes_at || job?.publication?.confirmed_until || '').join('|')
  useEffect(() => {
    const values = deadlines.split('|').map(Date.parse).filter((value) => Number.isFinite(value) && value > now)
    const refresh = () => setNow(Date.now())
    const timer = values.length ? setTimeout(refresh, Math.min(2147483647, Math.max(1, Math.min(...values) - Date.now() + 1))) : null
    window.addEventListener('focus', refresh)
    return () => { if (timer !== null) clearTimeout(timer); window.removeEventListener('focus', refresh) }
  }, [deadlines, now])
  return now
}
