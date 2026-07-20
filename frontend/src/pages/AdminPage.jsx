import { useEffect, useState } from 'react'
import Table from '../components/Table'
import StatusBadge from '../components/StatusBadge'
import Button from '../components/Button'
import * as adminService from '../services/adminService'

const TABS = ['Users', 'Sites & Zones', 'Cameras & Sensors', 'Thresholds', 'Audit Log']

const USER_COLUMNS = [
  { key: 'full_name', label: 'Name' },
  { key: 'email', label: 'Email' },
  { key: 'role', label: 'Role', render: (row) => <span className="capitalize">{row.role.replace('_', ' ')}</span> },
  {
    key: 'is_active',
    label: 'Status',
    render: (row) => <StatusBadge status={row.is_active ? 'active' : 'inactive'} variant="device" />,
  },
]

const SITE_COLUMNS = [
  { key: 'name', label: 'Site' },
  { key: 'address', label: 'Address' },
  { key: 'zones', label: 'Zones' },
]

export default function AdminPage() {
  const [tab, setTab] = useState('Users')
  const [users, setUsers] = useState(null)
  const [sites, setSites] = useState(null)

  useEffect(() => {
    adminService.getUsers().then((res) => setUsers(res.items))
    adminService.getSites().then((res) => setSites(res.items))
  }, [])

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">Settings</h2>
          <p className="text-sm text-slate-500">Platform administration — users, sites, and devices.</p>
        </div>
        <Button size="sm">+ Add</Button>
      </div>

      <div className="flex gap-1 overflow-x-auto rounded-lg border border-border bg-navy-800 p-1">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`focus-ring shrink-0 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              tab === t ? 'bg-safety-orange text-navy-950' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'Users' && (
        <Table columns={USER_COLUMNS} rows={users} loading={users === null} emptyMessage="No users yet — invite your first team member" />
      )}

      {tab === 'Sites & Zones' && (
        <Table columns={SITE_COLUMNS} rows={sites} loading={sites === null} emptyMessage="No sites configured yet" />
      )}

      {tab === 'Cameras & Sensors' && (
        <div className="panel py-10 text-center text-sm text-slate-400">
          Camera and sensor registry — placeholder view.
        </div>
      )}

      {tab === 'Thresholds' && (
        <div className="panel space-y-4 p-5">
          <p className="text-sm text-slate-400">Per-site risk severity thresholds (placeholder controls).</p>
          {['Medium', 'High', 'Critical'].map((level) => (
            <div key={level} className="flex items-center gap-4">
              <span className="w-20 text-sm text-slate-300">{level}</span>
              <input type="range" min="0" max="100" defaultValue={level === 'Medium' ? 40 : level === 'High' ? 70 : 90} className="flex-1 accent-safety-orange" />
            </div>
          ))}
        </div>
      )}

      {tab === 'Audit Log' && (
        <div className="panel py-10 text-center text-sm text-slate-400">
          No audit events to display yet.
        </div>
      )}
    </div>
  )
}
