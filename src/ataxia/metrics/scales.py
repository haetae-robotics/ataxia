"""Symptom scales: mapping a metric value onto a 0-3 severity level.

Levels follow clinical rating-scale convention (0 absent - 1 mild -
2 moderate - 3 marked). Thresholds are normed against PseudoBot (see
PROPOSAL.md): the healthy profile lands at level 0 and each induced
profile at level >= 2 on its primary scales.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SymptomScale:
    name: str
    metric: str
    direction: str  # "higher" or "lower" = pathological direction
    thresholds: tuple[float, float, float]
    dsm_note: str = ""
    mechanism_note: str = ""

    def level(self, value: float) -> int:
        t0, t1, t2 = self.thresholds
        if self.direction == "higher":
            if value < t0:
                return 0
            if value < t1:
                return 1
            if value < t2:
                return 2
            return 3
        if value > t0:
            return 0
        if value > t1:
            return 1
        if value > t2:
            return 2
        return 3


SCALES: dict[str, SymptomScale] = {
    "helplessness_scale": SymptomScale(
        name="helplessness_scale",
        metric="initiation_collapse",
        direction="higher",
        thresholds=(0.10, 0.25, 0.40),
        dsm_note="proxies learned helplessness (action initiation collapse after failures)",
        mechanism_note="initiative decays as 1/(1+k*failures) over accumulated bumps",
    ),
    "perseveration_scale": SymptomScale(
        name="perseveration_scale",
        metric="failed_collect_rate",
        direction="higher",
        thresholds=(0.10, 0.25, 0.45),
        dsm_note="proxies perseveration (repetition of completed subtasks; a robotics bug-class term)",
        mechanism_note="post-collect action repetition loops the policy into walls",
    ),
    "neglect_index": SymptomScale(
        name="neglect_index",
        metric="region_detection_delta",
        direction="higher",
        thresholds=(0.25, 0.50, 0.75),
        dsm_note="maps to hemispatial neglect (one side of space systematically unattended)",
        mechanism_note="right-hemifield observations masked; right targets never enter the belief grid",
    ),
}
