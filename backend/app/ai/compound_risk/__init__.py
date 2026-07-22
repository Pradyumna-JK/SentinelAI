"""Compound Risk Intelligence Engine — the platform's centerpiece: a
LangGraph multi-agent pipeline that correlates signals no single sensor
would flag alone (gas readings, active work permits, maintenance activity,
shift changeovers, and — via the existing Risk Intelligence Engine's own
RiskEvent history — CCTV/vision detections) into one explainable finding.

Deliberately rule-based, not an LLM call: this mirrors the never-implemented
Compound Risk Engine spec in docs/11_AI_ARCHITECTURE.md §3 — a safety-
critical correlation must be fast and deterministic, with a templated
rationale, not a free-form generation that could hallucinate. graph.py's
four signal-gathering agents run in parallel and fan into one correlation
agent that applies the combination matrix; scheduler.py is what turns a
finding into a persisted, explainable event feeding the *existing*
Risk Intelligence Engine (app/ai/risk) — no parallel scoring system.
"""
