import { mockDelay } from './apiClient'
import { mockCameras, mockDetections } from '../data/mockData'

// Mirrors GET /api/v1/cctv/streams (docs/08_API_SPECIFICATION.md §4)
export function getCameraStreams() {
  return mockDelay({ streams: mockCameras })
}

// Mirrors GET /api/v1/vision/detections
export function getDetections() {
  return mockDelay({ items: mockDetections })
}
