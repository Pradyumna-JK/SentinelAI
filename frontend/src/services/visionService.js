import apiClient, { mockDelay } from './apiClient'
import { mockDetections } from '../data/mockData'

// Mirrors GET /camera (backend/app/api/camera.py) — the registered camera
// list is real; live per-frame detections below are not (see that export's
// comment).
export async function getCameraStreams() {
  const { data } = await apiClient.get('/camera')
  return data
}

// Still mock: this reads from the Vision Intelligence Engine's live
// inference queue (app/ai/vision), which only has data when frames are
// actually being submitted — there's no live camera feed wired into this
// demo, so there's nothing real to fetch here yet.
export function getDetections() {
  return mockDelay({ items: mockDetections })
}
