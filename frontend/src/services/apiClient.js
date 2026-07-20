import axios from 'axios'

// Shared Axios instance. All services in this folder go through this client;
// pages never call axios directly (see docs/CODING_STANDARDS.md §2).
// The backend (backend/app/main.py) currently exposes flat routes with no
// /api/v1 prefix and no request envelope, so the default here matches that —
// override with VITE_API_BASE_URL for other environments.
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalized = {
      code: error?.code || 'NETWORK_ERROR',
      message: extractErrorMessage(error),
    }
    return Promise.reject(normalized)
  },
)

// FastAPI error bodies are `{"detail": "..."}` or, for validation errors,
// `{"detail": [{"msg": "...", "loc": [...]}, ...]}`. Falls back to the raw
// Axios/network error message when there's no response body at all.
function extractErrorMessage(error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d) => d.msg).filter(Boolean).join('; ') || 'Validation error'
  }
  return error.message || 'Something went wrong'
}

export default apiClient

// Simulates network latency for mock services so loading states are visible.
export function mockDelay(data, ms = 400) {
  return new Promise((resolve) => setTimeout(() => resolve(data), ms))
}
