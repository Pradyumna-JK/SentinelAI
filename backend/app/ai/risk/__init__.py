"""Risk Intelligence Engine — pure hazard interpretation and scoring math.

catalog.py turns raw vision detections into business-meaningful hazards
(PPE violations via bbox correlation, fire/smoke pass-through). scoring.py
does the numbers: time decay, compound aggregation, EWMA rolling average,
linear-regression trend/prediction, rule-based recommended actions. Both
are pure functions — no DB, no HTTP. Persistence and orchestration live in
app/services/risk_ingest_service.py and app/services/risk_engine_service.py;
the periodic background recompute loop is scheduler.py.
"""
