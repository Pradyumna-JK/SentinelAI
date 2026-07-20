import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts'
import LoadingSkeleton from './LoadingSkeleton'

const TOOLTIP_STYLE = {
  background: '#131c2e',
  border: '1px solid #25334f',
  borderRadius: 8,
  fontSize: 12,
  color: '#e2e8f0',
}

export default function Chart({
  type = 'line',
  data,
  xKey,
  yKey,
  height = 240,
  ariaLabel,
  loading = false,
  color = '#f97316',
}) {
  if (loading) {
    return <LoadingSkeleton shape="chart" />
  }

  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-xl border border-border bg-navy-800/50 text-sm text-slate-400"
        style={{ height }}
      >
        No data available for the selected range
      </div>
    )
  }

  if (type === 'sparkline') {
    return (
      <div role="img" aria-label={ariaLabel} style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <Line type="monotone" dataKey={yKey} stroke={color} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    )
  }

  if (type === 'bar') {
    return (
      <div role="img" aria-label={ariaLabel} style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1b2740" vertical={false} />
            <XAxis dataKey={xKey} tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={{ stroke: '#25334f' }} tickLine={false} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} width={32} />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'rgba(249,115,22,0.08)' }} />
            <Bar dataKey={yKey} fill={color} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div role="img" aria-label={ariaLabel} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1b2740" vertical={false} />
          <XAxis dataKey={xKey} tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={{ stroke: '#25334f' }} tickLine={false} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} width={32} />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Line type="monotone" dataKey={yKey} stroke={color} strokeWidth={2.5} dot={{ r: 3, fill: color }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
