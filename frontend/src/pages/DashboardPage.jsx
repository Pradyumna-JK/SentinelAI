import { useCallback, useEffect, useState } from 'react'
import RiskMeter from '../components/RiskMeter'
import AlertCard from '../components/AlertCard'
import StatusBadge from '../components/StatusBadge'
import LoadingSkeleton from '../components/LoadingSkeleton'
import Modal from '../components/Modal'
import Button from '../components/Button'
import * as dashboardService from '../services/dashboardService'
import * as alertsService from '../services/alertsService'
import * as riskService from '../services/riskService'
import { useToast } from '../hooks/useToast'

const REFRESH_INTERVAL_MS = 15000

// GET /risk carries the score/level/rationale, but not the site name or
// active-alert count — those only come back on GET /dashboard's zones.
// Merge by zone_id so risk cards keep showing everything they did before.
function mergeZoneRisk(riskScores, dashboardZones) {
  const zoneMetaById = Object.fromEntries((dashboardZones || []).map((z) => [z.zone_id, z]))
  return (riskScores || []).map((r) => {
    const meta = zoneMetaById[r.zone_id]
    return {
      zone_id: r.zone_id,
      zone_name: r.zone_name,
      site_name: meta?.site_name,
      risk_score: r.score,
      risk_level: r.level,
      active_alerts: meta?.active_alerts ?? 0,
      rationale: r.rationale,
      confidence: r.confidence,
    }
  })
}

export default function DashboardPage() {
  const [zones, setZones] = useState(null)
  const [agents, setAgents] = useState(null)
  const [alerts, setAlerts] = useState(null)
  const [selectedZone, setSelectedZone] = useState(null)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)
  const { showToast } = useToast()

  const loadDashboard = useCallback(async () => {
    setRefreshing(true)
    try {
      const [dashboard, risk, alertsRes] = await Promise.all([
        dashboardService.getDashboard(),
        riskService.getRiskScores(),
        alertsService.getAlerts(),
      ])
      setZones(mergeZoneRisk(risk.scores, dashboard.zones))
      setAgents(dashboard.agents)
      setAlerts(alertsRes.items)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data')
    } finally {
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadDashboard()
    const interval = setInterval(loadDashboard, REFRESH_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [loadDashboard])

  const handleAcknowledge = async (id) => {
    await alertsService.acknowledgeAlert(id, 'Priya Shah')
    const res = await alertsService.getAlerts()
    setAlerts(res.items)
    showToast('Alert acknowledged', 'success')
  }

  const unacknowledged = (alerts || [])
    .filter((a) => !a.acknowledged_by)
    .sort((a, b) => severityRank(b.severity) - severityRank(a.severity))

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-100">Live Risk Overview</h2>
        <p className="text-sm text-slate-500">Real-time compound risk across all monitored zones.</p>
      </div>

      {error && (
        <div className="panel flex items-center justify-between gap-4 border-l-4 border-l-safety-red p-4">
          <p className="text-sm text-safety-red">{error}</p>
          <Button size="sm" variant="secondary" onClick={loadDashboard} loading={refreshing}>
            Retry
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {zones
              ? zones.map((z) => (
                  <RiskMeter
                    key={z.zone_id}
                    score={z.risk_score}
                    level={z.risk_level}
                    zoneName={z.zone_name}
                    siteName={z.site_name}
                    activeAlerts={z.active_alerts}
                    onClick={() => setSelectedZone(z)}
                  />
                ))
              : Array.from({ length: 4 }).map((_, i) => <LoadingSkeleton key={i} shape="card" />)}
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-100">Active Alerts</h3>
          {alerts ? (
            unacknowledged.length > 0 ? (
              unacknowledged.slice(0, 3).map((a) => (
                <AlertCard key={a.id} alert={a} onAcknowledge={handleAcknowledge} compact />
              ))
            ) : (
              <div className="panel py-8 text-center text-sm text-slate-400">
                No active alerts — all clear
              </div>
            )
          ) : (
            <LoadingSkeleton shape="card" count={2} />
          )}
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-semibold text-slate-100">Agent Health</h3>
        <div className="panel grid grid-cols-2 gap-3 p-4 sm:grid-cols-3 lg:grid-cols-6">
          {agents
            ? agents.map((a) => (
                <div key={a.name} className="flex flex-col items-start gap-1.5">
                  <span className="text-xs text-slate-400">{a.name}</span>
                  <StatusBadge status={a.status} variant="agent" />
                </div>
              ))
            : Array.from({ length: 6 }).map((_, i) => <LoadingSkeleton key={i} shape="text" />)}
        </div>
      </div>

      <Modal isOpen={Boolean(selectedZone)} onClose={() => setSelectedZone(null)} title="Risk Rationale">
        {selectedZone && (
          <div className="space-y-2 text-sm text-slate-300">
            <p>
              <span className="font-medium text-slate-100">{selectedZone.zone_name}</span> is currently
              rated <span className="font-medium">{selectedZone.risk_level}</span> risk
              (score {selectedZone.risk_score}/100).
            </p>
            <p className="text-slate-400">{selectedZone.rationale}</p>
          </div>
        )}
      </Modal>
    </div>
  )
}

function severityRank(sev) {
  return { Critical: 4, High: 3, Medium: 2, Low: 1 }[sev] || 0
}
