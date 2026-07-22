"""Pure sensor-reading simulation math — no DB, no HTTP.

Plain gaussian noise around the baseline midpoint would never produce a
demo worth watching: every reading would look the same. Instead this is a
tiny two-state model — "normal" (mean-reverting noise) and "excursion" (a
spike above baseline_max that decays back down over several ticks) — so a
demo run actually shows a legible gas-buildup-and-clear narrative, which is
exactly the signal the Compound Risk Intelligence Engine (app/ai/compound_risk)
correlates against permits/maintenance/shift activity.
"""

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationResult:
    value: float
    in_excursion: bool


def next_reading(
    *,
    previous_value: float,
    baseline_min: float,
    baseline_max: float,
    in_excursion: bool,
    excursion_start_probability: float = 0.08,
    excursion_end_probability: float = 0.35,
) -> SimulationResult:
    span = max(baseline_max - baseline_min, 1e-6)
    noise = random.gauss(0, span * 0.05)

    if in_excursion:
        # Decay back toward a point just above baseline_max, with a
        # per-tick chance to end the excursion once it's actually back
        # in range.
        decay_target = baseline_max * 0.7
        value = previous_value + (decay_target - previous_value) * 0.35 + noise
        still_excursion = value > baseline_max and random.random() > excursion_end_probability
        return SimulationResult(round(value, 2), still_excursion)

    midpoint = (baseline_min + baseline_max) / 2
    value = previous_value + (midpoint - previous_value) * 0.15 + noise

    if random.random() < excursion_start_probability:
        value = baseline_max * random.uniform(1.2, 1.6)
        return SimulationResult(round(value, 2), True)

    value = max(baseline_min * 0.7, value)
    return SimulationResult(round(value, 2), False)


def is_anomaly(value: float, baseline_min: float, baseline_max: float) -> bool:
    return value < baseline_min or value > baseline_max
