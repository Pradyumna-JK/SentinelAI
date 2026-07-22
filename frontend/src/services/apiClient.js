import axios from 'axios'
import { clearSession, getAccessToken, getRefreshToken, storeSession } from './tokenStorage'

// Shared Axios instance. All services in this folder go through this client;
// pages never call axios directly (see docs/CODING_STANDARDS.md §2).
// The backend (backend/app/main.py) currently exposes flat routes with no
// /api/v1 prefix and no request envelope, so the default here matches that —
// override with VITE_API_BASE_URL for other environments.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attaches the bearer token to every request. Deliberately reads storage on
// every call rather than caching the header at client-creation time — the
// token changes across login/logout/refresh within the same page session.
apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// A raw (non-intercepted) client for the one call that must never trigger
// this same 401-handling logic recursively: refreshing the token itself.
const refreshClient = axios.create({ baseURL: BASE_URL, timeout: 10000 })

let refreshPromise = null

async function refreshAccessToken() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) throw new Error('No refresh token available')
  const { data } = await refreshClient.post('/auth/refresh', { refresh_token: refreshToken })
  storeSession(data)
  return data.access_token
}

const AUTH_PATHS = ['/auth/login', '/auth/refresh']

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error
    const isAuthCall = AUTH_PATHS.some((path) => config?.url?.includes(path))

    if (response?.status === 401 && !isAuthCall && !config._retried && getRefreshToken()) {
      config._retried = true
      try {
        // Multiple requests can 401 at once (e.g. a page firing several
        // calls in parallel) — share one in-flight refresh instead of
        // rotating the refresh token once per failed request.
        refreshPromise = refreshPromise || refreshAccessToken()
        const newAccessToken = await refreshPromise
        refreshPromise = null
        config.headers.Authorization = `Bearer ${newAccessToken}`
        return apiClient(config)
      } catch {
        refreshPromise = null
        clearSession()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    if (response?.status === 401 && !isAuthCall) {
      clearSession()
      window.location.href = '/login'
    }

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
