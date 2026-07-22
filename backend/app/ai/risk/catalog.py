"""Hazard catalog and detection interpretation.

This is the bridge between the vision engine's raw output (app/ai/vision —
"a helmet was detected here") and the risk engine's domain concept of a
*hazard* ("this person is not wearing one"). That interpretation is
deliberately NOT inside the vision engine: app/ai/vision's own docstring
requires it stay pure ML with zero business meaning, so PPE-violation logic
lives here instead, one layer up.

PPE-violation correlation uses bbox-center containment (a PPE detection's
center point falling inside a person's bounding box), not pose estimation.
This is a real simplification with a real limitation: in a tightly packed
crowd, a helmet worn by person A whose head overlaps person B's torso box
can be misattributed to B. Pose-estimation-based keypoint matching is the
accuracy upgrade if/when that matters; bbox containment is the standard
lightweight heuristic production PPE-compliance systems start with, and is
cheap enough to run per-frame without its own model.
"""

from dataclasses import dataclass

from app.ai.risk.types import HazardEvent, NormalizedBBox, RawDetection

DIRECT_HAZARD_CLASSES = frozenset({"fire", "smoke"})
PPE_CLASSES = frozenset({"helmet", "vest", "gloves"})

# 0..100 — how bad is it, on its own, at confidence 1.0, right now (before
# time decay or aggregation). Fire and smoke are life-safety hazards, so
# they anchor the top of the scale; PPE violations are real but routine
# compliance issues, several rungs down.
HAZARD_SEVERITY: dict[str, float] = {
    "fire": 100.0,
    "smoke": 70.0,
    "ppe_violation_helmet": 55.0,
    "ppe_violation_vest": 40.0,
    "ppe_violation_gloves": 30.0,
}


@dataclass(frozen=True)
class InterpretationResult:
    hazards: list[HazardEvent]
    persons_detected: int
    persons_compliant: int  # had every one of helmet/vest/gloves matched


def _is_contained(inner_center: tuple[float, float], outer: NormalizedBBox) -> bool:
    cx, cy = inner_center
    return outer.x1 <= cx <= outer.x2 and outer.y1 <= cy <= outer.y2


def interpret_detections(detections: list[RawDetection]) -> InterpretationResult:
    """Raw vision detections for one frame -> business-meaningful hazards.

    Direct hazards (fire/smoke) pass through 1:1. PPE is inferred per
    person: a person with no contained helmet/vest/gloves center-point
    yields one `ppe_violation_<item>` hazard per missing item.
    """
    hazards: list[HazardEvent] = []

    for det in detections:
        if det.class_name in DIRECT_HAZARD_CLASSES:
            hazards.append(
                HazardEvent(
                    hazard_class=det.class_name,
                    confidence=det.confidence,
                    severity=HAZARD_SEVERITY[det.class_name],
                    bbox=det.bbox,
                )
            )

    persons = [d for d in detections if d.class_name == "person"]
    ppe_detections = [d for d in detections if d.class_name in PPE_CLASSES]

    compliant_count = 0
    for person in persons:
        matched_items: set[str] = set()
        for ppe in ppe_detections:
            if _is_contained(ppe.bbox.center, person.bbox):
                matched_items.add(ppe.class_name)

        missing = PPE_CLASSES - matched_items
        if not missing:
            compliant_count += 1
        for item in missing:
            hazard_class = f"ppe_violation_{item}"
            hazards.append(
                HazardEvent(
                    hazard_class=hazard_class,
                    # A missing item has no detection of its own to carry a
                    # confidence, so we use the person detection's — the
                    # violation is exactly as certain as "this is a person".
                    confidence=person.confidence,
                    severity=HAZARD_SEVERITY[hazard_class],
                    bbox=person.bbox,
                )
            )

    return InterpretationResult(
        hazards=hazards, persons_detected=len(persons), persons_compliant=compliant_count
    )
