import { useEffect, useState } from 'react'
import Table from '../components/Table'
import StatusBadge from '../components/StatusBadge'
import Modal from '../components/Modal'
import Button from '../components/Button'
import Timeline from '../components/Timeline'
import * as incidentsService from '../services/incidentsService'
import { useToast } from '../hooks/useToast'

const COLUMNS = [
  { key: 'title', label: 'Incident' },
  { key: 'zone_name', label: 'Zone' },
  { key: 'severity', label: 'Severity' },
  { key: 'status', label: 'Status', render: (row) => <StatusBadge status={row.status} variant="incident" /> },
  {
    key: 'created_at',
    label: 'Reported',
    render: (row) => new Date(row.created_at).toLocaleDateString(),
  },
]

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState(null)
  const [selected, setSelected] = useState(null)
  const { showToast } = useToast()

  const load = () => incidentsService.getIncidents().then((res) => setIncidents(res.items))

  useEffect(() => {
    load()
  }, [])

  const handleApprove = async (id) => {
    await incidentsService.approveIncident(id)
    await load()
    setSelected(null)
    showToast('Incident report approved', 'success')
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-slate-100">Incident Reports</h2>
        <p className="text-sm text-slate-500">Auto-drafted, evidence-linked reports awaiting review.</p>
      </div>

      <Table
        columns={COLUMNS}
        rows={incidents}
        loading={incidents === null}
        onRowClick={setSelected}
        emptyMessage="No incidents recorded"
      />

      <Modal isOpen={Boolean(selected)} onClose={() => setSelected(null)} title={selected?.title} size="lg">
        {selected && (
          <div className="space-y-5">
            <div className="flex items-center gap-2">
              <StatusBadge status={selected.status} variant="incident" />
              <span className="text-sm text-slate-400">{selected.zone_name}</span>
            </div>
            <p className="text-sm text-slate-300">
              This is placeholder incident detail text. In production, the Incident Report Generator
              drafts this from linked evidence (detections, sensor readings, the triggering risk
              score, and — where applicable — the Emergency Response Agent's recommendation). See
              docs/11_AI_ARCHITECTURE.md §6.
            </p>
            <div>
              <h4 className="mb-2 text-sm font-semibold text-slate-100">Evidence Timeline</h4>
              <Timeline
                events={[
                  { id: 'e1', label: 'Detection recorded', timestamp: selected.created_at, type: 'evidence' },
                  { id: 'e2', label: 'Compound risk score computed', timestamp: selected.created_at, type: 'evidence' },
                  { id: 'e3', label: 'Incident report drafted', timestamp: selected.created_at, type: 'evidence' },
                ]}
              />
            </div>
            <div className="flex justify-end gap-2 border-t border-border pt-4">
              <Button variant="secondary" disabled={selected.status === 'approved'}>
                Export PDF
              </Button>
              <Button
                onClick={() => handleApprove(selected.id)}
                disabled={selected.status === 'approved'}
              >
                {selected.status === 'approved' ? 'Approved' : 'Approve'}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
