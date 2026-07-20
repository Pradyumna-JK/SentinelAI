import { mockDelay } from './apiClient'
import { mockComplianceDocuments, mockChatMessages } from '../data/mockData'

// Mirrors GET /api/v1/compliance/documents (docs/08_API_SPECIFICATION.md §9)
export function getDocuments() {
  return mockDelay({ items: mockComplianceDocuments })
}

// Mirrors GET /api/v1/compliance (initial chat history — placeholder only)
export function getChatHistory() {
  return mockDelay({ items: mockChatMessages })
}

// Mirrors POST /api/v1/compliance/query
export function askQuestion(question) {
  const insufficient = /predict|guarantee|future/i.test(question)
  if (insufficient) {
    return mockDelay(
      { answer: null, citations: [], insufficient_info: true },
      900,
    )
  }
  return mockDelay(
    {
      answer:
        'Based on the ingested SOPs and OSHA references, PPE must be worn at all times within marked hazard zones, and hearing protection is required above 85 dBA TWA.',
      citations: [{ document_id: 'doc2', title: 'OSHA 1910.132', chunk_index: 2 }],
      insufficient_info: false,
    },
    900,
  )
}
