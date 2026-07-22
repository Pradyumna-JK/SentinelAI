import { useEffect, useState } from 'react'
import ChatWindow from '../components/ChatWindow'
import Card from '../components/Card'
import Button from '../components/Button'
import Modal from '../components/Modal'
import LoadingSkeleton from '../components/LoadingSkeleton'
import * as complianceService from '../services/complianceService'
import { useToast } from '../hooks/useToast'

export default function CompliancePage() {
  const [documents, setDocuments] = useState(null)
  const [messages, setMessages] = useState([])
  const [isAnswering, setIsAnswering] = useState(false)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const { showToast } = useToast()

  const refreshDocuments = () => complianceService.getDocuments().then((res) => setDocuments(res.items))

  useEffect(() => {
    refreshDocuments()
    complianceService.getChatHistory().then((res) => setMessages(res.items))
  }, [])

  const handleSend = async (question) => {
    const userMsg = { id: `u-${Date.now()}`, role: 'user', text: question, citations: [] }
    setMessages((prev) => [...prev, userMsg])
    setIsAnswering(true)
    try {
      const res = await complianceService.askQuestion(question, sessionId)
      setSessionId(res.session_id)
      const answerText = res.insufficient_info
        ? "I don't have enough ingested documentation to answer that confidently yet."
        : res.answer
      setMessages((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, role: 'assistant', text: answerText, citations: res.citations },
      ])
    } catch (err) {
      showToast(err.message || 'Compliance chat failed', 'error')
    } finally {
      setIsAnswering(false)
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    const file = e.target.elements['doc-file'].files[0]
    if (!file) {
      showToast('Choose a PDF file first', 'error')
      return
    }
    try {
      await complianceService.uploadDocument(file)
      setUploadOpen(false)
      showToast('Document queued for ingestion — refresh in a few seconds for status', 'success')
      await refreshDocuments()
    } catch (err) {
      showToast(err.message || 'Upload failed', 'error')
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-slate-100">Compliance Copilot</h2>
        <p className="text-sm text-slate-500">Ask regulatory questions grounded in your ingested documents.</p>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ChatWindow
            messages={messages}
            onSend={handleSend}
            isAnswering={isAnswering}
            disabled={documents !== null && documents.length === 0}
          />
        </div>

        <Card
          title="Ingested Documents"
          action={
            <Button size="sm" variant="secondary" onClick={() => setUploadOpen(true)}>
              Upload
            </Button>
          }
        >
          {documents ? (
            documents.length > 0 ? (
              <ul className="space-y-2.5">
                {documents.map((doc) => (
                  <li key={doc.id} className="rounded-lg border border-border bg-navy-900/60 p-2.5">
                    <p className="text-sm text-slate-200">{doc.filename}</p>
                    <p className="text-xs text-slate-500">
                      {doc.status}
                      {doc.status === 'ready' && ` · ${doc.chunk_count} chunks`}
                      {doc.status === 'failed' && doc.error_message ? ` · ${doc.error_message}` : ''}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-400">No documents ingested yet.</p>
            )
          ) : (
            <LoadingSkeleton shape="row" count={3} />
          )}
        </Card>
      </div>

      <Modal isOpen={uploadOpen} onClose={() => setUploadOpen(false)} title="Upload Compliance Document">
        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <label htmlFor="doc-file" className="mb-1 block text-xs font-medium text-slate-400">
              PDF file
            </label>
            <input
              id="doc-file"
              type="file"
              accept="application/pdf"
              className="w-full text-sm text-slate-400 file:mr-3 file:rounded-lg file:border-0 file:bg-navy-700 file:px-3 file:py-1.5 file:text-slate-200"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setUploadOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">Upload</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
