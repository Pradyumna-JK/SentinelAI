import { useEffect, useState } from 'react'
import Card from '../components/Card'
import Chart from '../components/Chart'
import * as analyticsService from '../services/analyticsService'

export default function AnalyticsPage() {
  const [riskTrend, setRiskTrend] = useState(null)
  const [incidentFrequency, setIncidentFrequency] = useState(null)
  const [complianceSummary, setComplianceSummary] = useState(null)
  const [range, setRange] = useState('7d')

  useEffect(() => {
    analyticsService.getRiskTrends().then((res) => setRiskTrend(res.points))
    analyticsService.getIncidentFrequency().then((res) => setIncidentFrequency(res.buckets))
    analyticsService.getComplianceSummary().then(setComplianceSummary)
  }, [range])

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">Analytics</h2>
          <p className="text-sm text-slate-500">Historical trends across risk, incidents, and compliance.</p>
        </div>
        <div className="flex gap-1 rounded-lg border border-border bg-navy-800 p-1">
          {['24h', '7d', '30d'].map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`focus-ring rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                range === r ? 'bg-safety-orange text-navy-950' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card title="Average Risk Score Trend" subtitle="All sites">
          <Chart
            type="line"
            data={riskTrend}
            xKey="timestamp"
            yKey="avg_score"
            loading={riskTrend === null}
            ariaLabel="Average risk score trend over time"
          />
        </Card>

        <Card title="Incident Frequency" subtitle="By category">
          <Chart
            type="bar"
            data={incidentFrequency}
            xKey="category"
            yKey="count"
            color="#3b82f6"
            loading={incidentFrequency === null}
            ariaLabel="Incident frequency by category"
          />
        </Card>
      </div>

      <Card title="Compliance Posture">
        {complianceSummary ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Metric label="Documents ingested" value={complianceSummary.documents_ingested} />
            <Metric label="Queries (30d)" value={complianceSummary.queries_last_30d} />
            <Metric
              label="Insufficient-info rate"
              value={`${Math.round(complianceSummary.insufficient_info_rate * 100)}%`}
            />
          </div>
        ) : (
          <p className="text-sm text-slate-500">Loading…</p>
        )}
      </Card>
    </div>
  )
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-border bg-navy-900/60 p-4">
      <p className="text-2xl font-semibold text-slate-100">{value}</p>
      <p className="mt-1 text-xs text-slate-500">{label}</p>
    </div>
  )
}
