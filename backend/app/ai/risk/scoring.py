"""Pure risk-scoring math: time decay, compound aggregation, rolling
average, trend/prediction, and recommended-action rules.

Every function here is pure (no DB, no clock reads beyond what's passed
in, no I/O) and takes its tunables as parameters rather than reading
Settings directly — app/services/risk_engine_service.py is the only place
that wires configuration in. This is what "no business logic inside
inference code" looks like applied to a statistical engine instead of an
ML one: the math is mechanical and unit-testable in isolation from
persistence and configuration.

Why `level` and `severity` can legitimately disagree: `level` bands the
compound, time-decayed, rolling-averaged score — a slow-moving read of
"how risky is this zone lately". `severity` bands only the single worst
currently-live contribution — a fast-moving read of "how bad is the worst
thing we're seeing right now". A zone can be `level=Medium` (nothing much
happening most of the time) while `severity=Critical` the instant a fire
detection lands, before enough history accumulates to move the smoothed
average. That divergence is the point, not a bug: it's what lets the API
answer both "should I be worried in general" and "is something on fire
right now" from one computation.
"""

from datetime import datetime, timezone
from statistics import fmean

from app.ai.risk.types import RiskLevel, ScoredEvent, Trend

# Level bands (score, 0-100) for the compound/decayed/smoothed score.
_LEVEL_THRESHOLDS: tuple[tuple[float, RiskLevel], ...] = (
    (75.0, RiskLevel.CRITICAL),
    (50.0, RiskLevel.HIGH),
    (25.0, RiskLevel.MEDIUM),
)

_RECOMMENDED_ACTIONS: dict[tuple[RiskLevel, str | None], str] = {
    (RiskLevel.CRITICAL, "fire"): "Evacuate the zone immediately and notify emergency services.",
    (RiskLevel.CRITICAL, "smoke"): "Evacuate the zone immediately and investigate the smoke source.",
}
_LEVEL_FALLBACK_ACTIONS: dict[RiskLevel, str] = {
    RiskLevel.CRITICAL: "Escalate to a safety supervisor immediately and restrict zone access.",
    RiskLevel.HIGH: "Dispatch a supervisor to the zone and confirm compliance in person.",
    RiskLevel.MEDIUM: "Flag for the next scheduled safety walk-through.",
    RiskLevel.LOW: "No action required — continue routine monitoring.",
}


def time_decay(age_seconds: float, half_life_seconds: float) -> float:
    """Exponential decay: 1.0 at age 0, 0.5 at one half-life, etc.

    Negative age (clock skew) clamps to 0 (full weight); half_life <= 0
    is treated as "decays instantly" rather than dividing by zero.
    """
    if half_life_seconds <= 0:
        return 0.0 if age_seconds > 0 else 1.0
    age_seconds = max(0.0, age_seconds)
    return 0.5 ** (age_seconds / half_life_seconds)


def score_event(severity: float, confidence: float, detected_at: datetime, *, now: datetime, half_life_seconds: float) -> float:
    age_seconds = (now - detected_at).total_seconds()
    return severity * confidence * time_decay(age_seconds, half_life_seconds)


def aggregate_events(
    scored_events: list[ScoredEvent], *, compound_boost_factor: float = 0.25
) -> tuple[float, str | None, float]:
    """Compound aggregation: the single worst live contribution dominates,
    with a partial boost from everything else concurrently active — several
    simultaneous moderate hazards should read as riskier than any one alone
    (hence "compound"), but shouldn't simply sum without bound.

    Returns (raw_score, dominant_hazard_class, max_single_contribution) —
    the third value is what severity_band() bands, kept separate from the
    compound score itself.
    """
    if not scored_events:
        return 0.0, None, 0.0

    dominant = max(scored_events, key=lambda e: e.contribution)
    other_sum = sum(e.contribution for e in scored_events) - dominant.contribution
    raw_score = min(100.0, dominant.contribution + compound_boost_factor * other_sum)
    return raw_score, dominant.hazard_class, dominant.contribution


def rolling_average(raw_score: float, previous_smoothed: float | None, *, alpha: float) -> float:
    """EWMA smoothing: `alpha` weights the new reading against the entire
    prior smoothed history in one term, so only the last snapshot's value
    needs to be carried forward — no window of raw history required.
    `alpha=1.0` disables smoothing entirely (score == raw_score); lower
    values trade responsiveness for stability against single noisy frames.
    """
    if previous_smoothed is None:
        return raw_score
    alpha = min(1.0, max(0.0, alpha))
    return alpha * raw_score + (1 - alpha) * previous_smoothed


def level_band(score: float) -> RiskLevel:
    for threshold, band in _LEVEL_THRESHOLDS:
        if score >= threshold:
            return band
    return RiskLevel.LOW


def severity_band(max_single_contribution: float) -> RiskLevel:
    return level_band(max_single_contribution)


def predict_and_trend(
    history: list[tuple[datetime, float]], *, horizon_minutes: float, trend_deadband_per_minute: float = 0.5
) -> tuple[float | None, Trend]:
    """Least-squares linear fit over (time, score) history -> forecast
    `horizon_minutes` past the most recent point, and classify direction.

    Deliberately a simple linear regression, not ARIMA/Prophet/an LSTM: with
    the sparse, irregular sample spacing a periodic risk-snapshot scheduler
    actually produces, a more sophisticated model has no more signal to work
    with and mainly adds opacity — a safety operator can sanity-check "the
    slope over the last N snapshots" but not a black-box forecast. Needs at
    least 2 points; fewer returns (None, STABLE).
    """
    if len(history) < 2:
        return None, Trend.STABLE

    t0 = history[0][0]
    xs = [(t - t0).total_seconds() / 60.0 for t, _ in history]  # minutes since first sample
    ys = [score for _, score in history]

    x_mean, y_mean = fmean(xs), fmean(ys)
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        # All samples at the same timestamp — no time axis to regress over.
        return ys[-1], Trend.STABLE

    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator
    intercept = y_mean - slope * x_mean

    last_x = xs[-1]
    predicted = intercept + slope * (last_x + horizon_minutes)
    predicted = min(100.0, max(0.0, predicted))

    if slope > trend_deadband_per_minute:
        trend = Trend.INCREASING
    elif slope < -trend_deadband_per_minute:
        trend = Trend.DECREASING
    else:
        trend = Trend.STABLE

    return round(predicted, 1), trend


def recommend_action(level: RiskLevel, dominant_hazard_class: str | None) -> str:
    specific = _RECOMMENDED_ACTIONS.get((level, dominant_hazard_class))
    if specific:
        return specific
    return _LEVEL_FALLBACK_ACTIONS[level]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
