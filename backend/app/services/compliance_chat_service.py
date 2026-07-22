"""Compliance Copilot conversation orchestration: sessions, persisted
history, and the streaming RAG chat turn itself.

`stream_chat` is the one place LangGraph (classify + retrieve) and
LangChain (chat model streaming) meet: it drives app/ai/compliance/graph.py
for the deterministic first half of the pipeline, then — only if retrieval
found something relevant — streams the actual answer token-by-token
straight from ChatGoogleGenerativeAI, yielding each token to its caller (the SSE
endpoint in app/api/compliance.py) as it arrives. Every persisted message
(user question and assistant answer alike) is written before this
generator's final `done` event, so a client that drops mid-stream still
finds a consistent, resumable history on its next `GET .../messages`.

`stream_chat` deliberately does NOT use the request-scoped `Depends(get_db)`
session the other methods share (`self._db`) — it opens its own via
`get_session_factory()` instead, same as app/ai/risk/scheduler.py and
app/ai/compliance/worker.py. Reason: this generator can stay alive for as
long as Gemini takes to stream a full answer, well past the point FastAPI
considers the route handler "done" (it returns the `StreamingResponse`
object immediately in app/api/compliance.py; the generator body hasn't
even started running yet at that point) — tying it to a session whose
lifetime is scoped to request-handler-return would risk using a closed
connection mid-stream. Opening a dedicated session sidesteps the question
entirely, and gives this method its own explicit commit points.
"""

import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from fastapi import Depends
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.compliance import prompts
from app.ai.compliance.graph import get_compliance_graph
from app.ai.compliance.memory import to_langchain_messages
from app.ai.compliance.types import ChatTurn
from app.ai.llm_content import extract_text
from app.core.config import get_settings
from app.db.session import get_db, get_session_factory
from app.models.compliance import ComplianceChatMessage, ComplianceChatSession
from app.models.enums import ChatRole, ComplianceIntent

_INSUFFICIENT_INFO_ANSWER = (
    "I don't have enough information in the ingested compliance documents to "
    "answer that. Try rephrasing, or ask an administrator to upload the "
    "relevant regulation or SOP."
)


class SessionNotFoundError(Exception):
    pass


class ComplianceChatService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._settings = get_settings()

    # ------------------------------------------------------------- sessions

    async def create_session(self, *, organization_id: uuid.UUID, user_id: uuid.UUID) -> ComplianceChatSession:
        return await self._create_session(self._db, organization_id=organization_id, user_id=user_id)

    async def list_sessions(self, *, user_id: uuid.UUID) -> list[ComplianceChatSession]:
        result = await self._db.execute(
            select(ComplianceChatSession)
            .where(ComplianceChatSession.user_id == user_id)
            .order_by(ComplianceChatSession.updated_at.desc())
        )
        return list(result.scalars())

    async def get_session(self, session_id: uuid.UUID, *, user_id: uuid.UUID) -> ComplianceChatSession:
        return await self._get_session(self._db, session_id, user_id=user_id)

    async def get_history(self, session_id: uuid.UUID, *, user_id: uuid.UUID) -> list[ComplianceChatMessage]:
        await self.get_session(session_id, user_id=user_id)
        result = await self._db.execute(
            select(ComplianceChatMessage)
            .where(ComplianceChatMessage.session_id == session_id)
            .order_by(ComplianceChatMessage.created_at)
        )
        return list(result.scalars())

    # ------------------------------------------------------------- chat

    async def stream_chat(
        self,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        session_id: uuid.UUID | None,
        question: str,
    ) -> AsyncIterator[dict]:
        """Yields event dicts: {"type": "token", "content": str},
        {"type": "citations", "session_id": str, "citations": [...]}
        (emitted once, before the final event), or
        {"type": "done", "session_id": str, "intent": str, "insufficient_info": bool}.
        """
        session_factory = get_session_factory()

        async def _set_tenant() -> None:
            # `is_local=true` (transaction-scoped, not connection-scoped) is
            # what lets Postgres discard this automatically at commit/
            # rollback instead of leaking it onto a pooled connection's next
            # tenant — same as app/db/session.py's get_db. The cost: it must
            # be re-issued after every commit in this method, since this
            # generator commits multiple times (user message, then the
            # assistant's answer) within one session's lifetime.
            await db.execute(
                text("SELECT set_config('app.current_organization_id', :org_id, true)"),
                {"org_id": str(organization_id)},
            )

        async with session_factory() as db:
            await _set_tenant()
            try:
                if session_id is not None:
                    session = await self._get_session(db, session_id, user_id=user_id)
                else:
                    # _create_session commits internally (it's also called
                    # standalone from the public create_session() API), which
                    # ends the transaction _set_tenant() just established —
                    # re-issue it before the next tenant-scoped statement.
                    session = await self._create_session(db, organization_id=organization_id, user_id=user_id)
                    await _set_tenant()

                history_turns = await self._load_recent_history(db, session.id)

                db.add(
                    ComplianceChatMessage(
                        organization_id=organization_id,
                        session_id=session.id,
                        role=ChatRole.USER,
                        content=question,
                        intent=None,
                        citations=[],
                    )
                )
                if session.title is None:
                    session.title = question[:200]
                await db.commit()
            except Exception:
                await db.rollback()
                raise
            await _set_tenant()

            graph = get_compliance_graph()
            graph_result = await graph.ainvoke({"organization_id": str(organization_id), "question": question})
            intent = graph_result["intent"]
            retrieved = graph_result["retrieved"]

            if not retrieved:
                db.add(
                    ComplianceChatMessage(
                        organization_id=organization_id,
                        session_id=session.id,
                        role=ChatRole.ASSISTANT,
                        content=_INSUFFICIENT_INFO_ANSWER,
                        intent=intent,
                        citations=[],
                    )
                )
                await db.commit()

                yield {"type": "token", "content": _INSUFFICIENT_INFO_ANSWER}
                yield {
                    "type": "done",
                    "session_id": str(session.id),
                    "intent": intent,
                    "insufficient_info": True,
                }
                return

            # Only the fields ComplianceCitation declares — the chunk's full
            # text already lives in Chroma; duplicating it into every
            # persisted message's JSONB column would be pure bloat.
            citations = [
                {
                    "document_id": chunk.document_id,
                    "title": chunk.title,
                    "chunk_index": chunk.chunk_index,
                    "similarity": chunk.similarity,
                }
                for chunk in retrieved
            ]
            yield {"type": "citations", "session_id": str(session.id), "citations": citations}

            context = "\n\n".join(f"[{c.title} - chunk {c.chunk_index}]\n{c.text}" for c in retrieved)
            system_prompt = prompts.build_system_prompt(ComplianceIntent(intent), context)
            messages = [
                SystemMessage(content=system_prompt),
                *to_langchain_messages(history_turns),
                HumanMessage(content=question),
            ]

            llm = ChatGoogleGenerativeAI(
                model=self._settings.gemini_chat_model,
                google_api_key=self._settings.gemini_api_key.get_secret_value(),
                temperature=0.2,
                streaming=True,
            )
            full_answer = ""
            async for chunk in llm.astream(messages):
                token = extract_text(chunk.content)
                if token:
                    full_answer += token
                    yield {"type": "token", "content": token}

            db.add(
                ComplianceChatMessage(
                    organization_id=organization_id,
                    session_id=session.id,
                    role=ChatRole.ASSISTANT,
                    content=full_answer,
                    intent=intent,
                    citations=citations,
                )
            )
            session.updated_at = datetime.now(timezone.utc)
            await db.commit()

            yield {
                "type": "done",
                "session_id": str(session.id),
                "intent": intent,
                "insufficient_info": False,
            }

    # ------------------------------------------------------------- internals
    # Take `db` explicitly rather than closing over `self._db` — shared by
    # both the request-scoped public methods above (called with `self._db`)
    # and `stream_chat` (called with its own dedicated session).

    @staticmethod
    async def _create_session(
        db: AsyncSession, *, organization_id: uuid.UUID, user_id: uuid.UUID
    ) -> ComplianceChatSession:
        session = ComplianceChatSession(organization_id=organization_id, user_id=user_id)
        db.add(session)
        await db.flush()
        await db.commit()
        return session

    @staticmethod
    async def _get_session(
        db: AsyncSession, session_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> ComplianceChatSession:
        session = await db.get(ComplianceChatSession, session_id)
        if session is None or session.user_id != user_id:
            raise SessionNotFoundError()
        return session

    async def _load_recent_history(self, db: AsyncSession, session_id: uuid.UUID) -> list[ChatTurn]:
        result = await db.execute(
            select(ComplianceChatMessage)
            .where(ComplianceChatMessage.session_id == session_id)
            .order_by(ComplianceChatMessage.created_at.desc())
            .limit(self._settings.compliance_history_window)
        )
        rows = list(reversed(list(result.scalars())))
        return [ChatTurn(role=row.role.value, content=row.content) for row in rows]


def get_compliance_chat_service(db: AsyncSession = Depends(get_db)) -> ComplianceChatService:
    return ComplianceChatService(db)
