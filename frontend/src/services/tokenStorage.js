// Zero-dependency token storage — shared by apiClient.js (attaches the
// Authorization header, handles 401 refresh) and authService.js (login/
// logout). Kept as its own module specifically so neither of those two
// needs to import the other.

const ACCESS_TOKEN_KEY = 'sentinel_access_token'
const REFRESH_TOKEN_KEY = 'sentinel_refresh_token'
const EMAIL_KEY = 'sentinel_user_email'

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function getStoredEmail() {
  return localStorage.getItem(EMAIL_KEY)
}

export function storeSession({ access_token, refresh_token }, email) {
  localStorage.setItem(ACCESS_TOKEN_KEY, access_token)
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)
  if (email) localStorage.setItem(EMAIL_KEY, email)
}

export function clearSession() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(EMAIL_KEY)
}
