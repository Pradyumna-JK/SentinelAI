import { useEffect, useMemo, useState } from 'react'
import AlertCard from '../components/AlertCard'
import LoadingSkeleton from '../components/LoadingSkeleton'
import * as alertsService from '../services/alertsService'
import { useToast } from '../hooks/useToast'

const SEVERITIES = ['Critical', 'High', 'Medium', 'Low']

export default function AlertsPage() {
  const [alerts, setAlerts] = useState(null)
  const [severityFilter, setSeverityFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('unacknowledged')
  const { showToast } = useToast()

  const load = () => alertsService.getAlerts().then((res) => setAlerts(res.items))

  useEffect(() => {
    load()
  }, [])

  const handleAcknowledge = async (id) => {
    await alertsService.acknowledgeAlert(id, 'Priya Shah')
    await load()
    showToast('Alert acknowledged', 'success')
  }

  const filtered = useMemo(() => {
    if (!alerts) return []
    return alerts
      .filter((a) => severityFilter === 'all' || a.severity === severityFilter)
      .filter((a) => {
        if (statusFilter === 'all') return true
        if (statusFilter === 'unacknowledged') return !a.acknowledged_by
        return Boolean(a.acknowledged_by)
      })
      .sort((a, b) => severityRank(b.severity) - severityRank(a.severity))
  }, [alerts, severityFilter, statusFilter])

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-slate-100">Alert Center</h2>
        <p className="text-sm text-slate-500">Severity-ranked, real-time safety alerts across every site.</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="focus-ring rounded-lg border border-border bg-navy-800 px-3 py-2 text-sm text-slate-200"
        >
          <option value="all">All severities</option>
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="focus-ring rounded-lg border border-border bg-navy-800 px-3 py-2 text-sm text-slate-200"
        >
          <option value="unacknowledged">Unacknowledged</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="all">All</option>
        </select>
      </div>

      {alerts ? (
        filtered.length > 0 ? (
          <div className="space-y-3">
            {filtered.map((a) => (
              <AlertCard key={a.id} alert={a} onAcknowledge={handleAcknowledge} />
            ))}
          </div>
        ) : (
          <div className="panel py-10 text-center text-sm text-slate-400">
            No active alerts — all clear
          </div>
        )
      ) : (
        <LoadingSkeleton shape="card" count={4} />
      )}
    </div>
  )
}

function severityRank(sev) {
  return { Critical: 4, High: 3, Medium: 2, Low: 1 }[sev] || 0
}
