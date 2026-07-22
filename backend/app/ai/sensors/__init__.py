"""IoT/SCADA sensor simulation — no real hardware exists for this demo, so
simulator.py generates plausible readings (mean-reverting noise plus
occasional excursions above baseline, modeling a gas buildup-and-clear
narrative) and scheduler.py writes them on a timer, the same lifecycle
pattern as app/ai/risk/scheduler.py. Pure math lives in simulator.py; no
DB/HTTP there — scheduler.py is the only place that touches persistence.
"""
