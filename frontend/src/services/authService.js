import apiClient from './apiClient'
import { clearSession, getAccessToken, getStoredEmail, getRefreshToken, storeSession } from './tokenStorage'

// Decodes a JWT's payload without verifying the signature — verification is
// the backend's job (every protected request is checked there); this is
// purely for reading claims (roles, org_id) to drive UI display.
function decodePayload(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(base64))
  } catch {
    return null
  }
}

export function isAuthenticated() {
  return Boolean(getAccessToken())
}

export function getCurrentUser() {
  const token = getAccessToken()
  if (!token) return null
  const payload = decodePayload(token)
  if (!payload) return null
  const email = getStoredEmail() || ''
  const roles = payload.roles || []
  return {
    full_name: email || 'Signed in user',
    role: roles[0] || 'Viewer',
    roles,
    permissions: payload.permissions || [],
    organization_id: payload.org_id,
  }
}

export async function login(email, password) {
  const { data } = await apiClient.post('/auth/login', { email, password })
  storeSession(data, email)
  return getCurrentUser()
}

export async function logout() {
  const refreshToken = getRefreshToken()
  try {
    if (refreshToken) {
      await apiClient.post('/auth/logout', { refresh_token: refreshToken })
    }
  } finally {
    clearSession()
  }
}
