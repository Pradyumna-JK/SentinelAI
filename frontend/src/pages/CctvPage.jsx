import { useEffect, useMemo, useState } from 'react'
import CameraTile from '../components/CameraTile'
import Timeline from '../components/Timeline'
import Modal from '../components/Modal'
import LoadingSkeleton from '../components/LoadingSkeleton'
import * as visionService from '../services/visionService'
import { mockZones } from '../data/mockData'

export default function CctvPage() {
  const [cameras, setCameras] = useState(null)
  const [detections, setDetections] = useState([])
  const [zoneFilter, setZoneFilter] = useState('all')
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    visionService.getCameraStreams().then((res) => setCameras(res.streams))
    visionService.getDetections().then((res) => setDetections(res.items))
  }, [])

  const detectionCountByCamera = useMemo(() => {
    const map = {}
    detections.forEach((d) => {
      map[d.camera_id] = (map[d.camera_id] || 0) + 1
    })
    return map
  }, [detections])

  const filteredCameras = (cameras || []).filter(
    (c) => zoneFilter === 'all' || c.zone_id === zoneFilter,
  )

  const expandedEvents = expanded
    ? detections
        .filter((d) => d.camera_id === expanded.camera_id)
        .map((d) => ({ id: d.id, label: `${d.class_label.replace('_', ' ')} (${Math.round(d.confidence * 100)}%)`, timestamp: d.created_at, type: 'detection' }))
    : []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">Camera Monitoring</h2>
          <p className="text-sm text-slate-500">Live feeds with AI detection overlays.</p>
        </div>
        <select
          value={zoneFilter}
          onChange={(e) => setZoneFilter(e.target.value)}
          className="focus-ring rounded-lg border border-border bg-navy-800 px-3 py-2 text-sm text-slate-200"
        >
          <option value="all">All zones</option>
          {mockZones.map((z) => (
            <option key={z.zone_id} value={z.zone_id}>
              {z.zone_name}
            </option>
          ))}
        </select>
      </div>

      {cameras ? (
        filteredCameras.length > 0 ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredCameras.map((cam) => (
              <CameraTile
                key={cam.camera_id}
                camera={cam}
                detectionCount={detectionCountByCamera[cam.camera_id] || 0}
                onExpand={setExpanded}
              />
            ))}
          </div>
        ) : (
          <div className="panel py-10 text-center text-sm text-slate-400">
            No cameras registered for this zone
          </div>
        )
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <LoadingSkeleton key={i} shape="card" className="!h-40" />
          ))}
        </div>
      )}

      <Modal isOpen={Boolean(expanded)} onClose={() => setExpanded(null)} title={expanded?.name} size="lg">
        {expanded && (
          <div className="space-y-4">
            <div className="aspect-video w-full rounded-lg bg-navy-950" />
            <div>
              <h4 className="mb-2 text-sm font-semibold text-slate-100">Recent Detections</h4>
              <Timeline events={expandedEvents} />
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
