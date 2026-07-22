"""Compliance Copilot — a RAG pipeline over ingested regulations/SOPs.

ingestion.py turns an uploaded PDF's bytes into chunks (pure functions, no
DB/HTTP/vector-store calls — app/ai/compliance/worker.py orchestrates those).
vectorstore.py is the one and only path to ChromaDB, and enforces tenant
isolation on every read (see its module docstring for why a `where` filter,
not a per-tenant collection). graph.py is the LangGraph pipeline
(classify_intent -> retrieve) that app/services/compliance_chat_service.py
drives; the actual answer generation and its token streaming happen in that
service, not inside the graph — see graph.py's docstring for why.

Persistence (documents, chat sessions/messages) lives in
app/models/compliance.py; orchestration lives in
app/services/compliance_ingest_service.py and
app/services/compliance_chat_service.py; the background ingestion worker
is app/ai/compliance/worker.py.
"""
