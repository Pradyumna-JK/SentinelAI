import apiClient from './apiClient'
import { getAccessToken } from './tokenStorage'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Mirrors GET /compliance/documents
export async function getDocuments() {
  const { data } = await apiClient.get('/compliance/documents')
  return data
}

// Mirrors POST /compliance/documents (multipart upload, queues background ingestion)
export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post('/compliance/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// No session picker in this UI yet — each page load starts a fresh
// conversation, so there is no prior history to fetch.
export function getChatHistory() {
  return Promise.resolve({ items: [] })
}

// Mirrors POST /compliance/chat — a Server-Sent Events stream (see
// backend/app/api/compliance.py's docstring for the event shape). Consumed
// here in full rather than rendered token-by-token, so the caller gets back
// one plain { answer, citations, insufficient_info, session_id } object and
// the rest of the UI doesn't need to know this is a streaming endpoint.
export async function askQuestion(question, sessionId) {
  const response = await fetch(`${BASE_URL}/compliance/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getAccessToken()}`,
    },
    body: JSON.stringify({ question, session_id: sessionId ?? null }),
  })

  if (!response.ok || !response.body) {
    throw new Error(`Compliance chat request failed (${response.status})`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let answer = ''
  let citations = []
  let result = { insufficient_info: false, session_id: sessionId ?? null, intent: null }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const events = buffer.split('\n\n')
    buffer = events.pop() ?? ''

    for (const rawEvent of events) {
      const eventLine = rawEvent.split('\n').find((line) => line.startsWith('event: '))
      const dataLine = rawEvent.split('\n').find((line) => line.startsWith('data: '))
      if (!eventLine || !dataLine) continue

      const eventType = eventLine.slice('event: '.length)
      const data = JSON.parse(dataLine.slice('data: '.length))

      if (eventType === 'citations') {
        citations = data.citations
      } else if (eventType === 'token') {
        answer += data.content
      } else if (eventType === 'done') {
        result = { insufficient_info: data.insufficient_info, session_id: data.session_id, intent: data.intent }
      } else if (eventType === 'error') {
        throw new Error(data.detail || 'Compliance chat stream error')
      }
    }
  }

  return { answer, citations, insufficient_info: result.insufficient_info, session_id: result.session_id }
}
