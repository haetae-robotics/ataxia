"""The eight episode-level instruments.

Pure functions over an Episode. Thresholds for the scales live in
scales.py, normed against PseudoBot; for real policies the delta vs. the
healthy baseline is the primary output.
"""

from __future__ import annotations

import math

from ..core.types import Episode, StepRecord
from .base import Metric, MetricContext, MetricValue

_MOVES = {"up", "down", "left", "right"}


def _waits(steps: list[StepRecord]) -> list[float]:
    return [1.0 if s.action == "wait" else 0.0 for s in steps]


class InitiationCollapse(Metric):
    """Rise in waiting from the first to the second half of the episode.
    Proxies *learned helplessness*: initiation of action collapses after
    accumulated failures. Direction: higher is pathological."""

    name = "initiation_collapse"
    description = "wait-rate shift, late half minus early half"

    def compute(self, episode: Episode, ctx: MetricContext) -> MetricValue:
        waits = _waits(episode.steps)
        half = len(waits) // 2
        early = sum(waits[:half]) / half if half else 0.0
        late = sum(waits[half:]) / (len(waits) - half) if len(waits) > half else 0.0
        return MetricValue(
            self.name, late - early, series=[early, late],
            extra={"early": early, "late": late},
        )


class NoProgressRate(Metric):
    """Share of movement attempts that make no progress (wall and obstacle
    bumps). Proxies *perseveration* when it spikes around completed
    subtasks. Direction: higher is pathological."""

    name = "no_progress_rate"
    description = "bumped moves over movement attempts"

    def compute(self, episode: Episode, ctx: MetricContext) -> MetricValue:
        moves = [s for s in episode.steps if s.action in _MOVES]
        if not moves:
            return MetricValue(self.name, 0.0, extra={"note": "no moves"})
        bumps = sum(1 for s in moves if s.bumped)
        return MetricValue(self.name, bumps / len(moves), extra={"bumps": bumps, "moves": len(moves)})


class FailedCollectRate(Metric):
    """Share of collect attempts that hit an empty cell. The perseveration
    signature: re-collecting a just-completed subtask does nothing.
    Direction: higher is pathological."""

    name = "failed_collect_rate"
    description = "failed collects over collect attempts"

    def compute(self, episode: Episode, ctx: MetricContext) -> MetricValue:
        attempts = [s for s in episode.steps if s.action == "collect"]
        if not attempts:
            return MetricValue(self.name, 0.0, extra={"note": "no collect attempts"})
        failed = sum(1 for s in attempts if s.failed_collect)
        return MetricValue(
            self.name, failed / len(attempts), extra={"failed": failed, "attempts": len(attempts)}
        )


class CollisionCount(Metric):
    """Raw wall/obstacle collision count. A volume reference for
    NoProgressRate."""

    name = "collision_count"
    description = "number of collisions in the episode"

    def compute(self, episode: Episode, ctx: MetricContext) -> MetricValue:
        bumps = sum(1 for s in episode.steps if s.bumped)
        return MetricValue(self.name, float(bumps), series=[float(s.bumped) for s in episode.steps])


class ActionRepetitionEntropy(Metric):
    """Normalized Shannon entropy of the action distribution — low entropy
    means stereotyped, repetitive behavior. Direction: lower is
    pathological."""

    name = "action_repetition_entropy"
    description = "normalized entropy of the action distribution"

    def compute(self, episode: Episode, ctx: MetricContext) -> MetricValue:
        counts: dict[str, int] = {}
        for s in episode.steps:
            counts[s.action] = counts.get(s.action, 0) + 1
        n = sum(counts.values())
        if not n:
            return MetricValue(self.name, 1.0)
        h = -sum((c / n) * math.log2(c / n) for c in counts.values())
        if len(counts) < 2:
            return MetricValue(self.name, 0.0, extra={"actions": counts})
        return MetricValue(self.name, h / math.log2(len(counts)), extra={"actions": counts})


class RegionDetectionDelta(Metric):
    """Left-minus-right target collection rate. Proxies *hemispatial
    neglect*: a healthy policy collects both hemifields evenly (index ~0);
    unilateral neglect drives the index toward +1 (or -1) depending on the
    ignored side. Direction: higher is pathological (right-neglect)."""

    name = "region_detection_delta"
    description = "left collection rate minus right collection rate"

    def compute(self, episode: Episode, ctx: MetricContext) -> MetricValue:
        left = episode.collected_left / episode.targets_left if episode.targets_left else 1.0
        right = episode.collected_right / episode.targets_right if episode.targets_right else 1.0
        return MetricValue(
            self.name, left - right, extra={"left": left, "right": right},
        )


class TravelOverhead(Metric):
    """Movement attempts per target actually collected — travel spent per
    unit of progress. The phantom-object signature: walks to empty cells
    inflate the ratio while success drops. Direction: higher is
    pathological."""

    name = "travel_overhead"
    description = "movement attempts per collected target"

    def compute(self, episode: Episode, ctx: MetricContext) -> MetricValue:
        moves = sum(1 for s in episode.steps if s.action in _MOVES)
        done = episode.collected_left + episode.collected_right
        if not done:
            return MetricValue(self.name, float(moves), extra={"note": "nothing collected"})
        return MetricValue(self.name, moves / done, extra={"moves": moves, "collected": done})


class DockEscalation(Metric):
    """Rise in dock-presence rate from the first to the second half of the
    episode. The dock-fixation signature: compulsive return-to-dock
    behavior that escalates over time. Direction: higher is pathological."""

    name = "dock_escalation"
    description = "dock-presence rate, late half minus early half"

    def compute(self, episode: Episode, ctx: MetricContext) -> MetricValue:
        half = len(episode.steps) // 2

        def rate(steps: list[StepRecord]) -> float:
            if not steps:
                return 0.0
            at_dock = sum(1 for s in steps if s.pos == (4, 4))
            return at_dock / len(steps)

        early = rate(episode.steps[:half])
        late = rate(episode.steps[half:])
        return MetricValue(
            self.name, late - early, series=[early, late],
            extra={"early": early, "late": late},
        )


class TaskSuccess(Metric):
    """Share of targets collected. Reference metric — every profile is
    expected to degrade it."""

    name = "task_success"
    description = "collected targets over total targets"

    def compute(self, episode: Episode, ctx: MetricContext) -> MetricValue:
        total = episode.targets_total
        done = episode.collected_left + episode.collected_right
        return MetricValue(self.name, done / total if total else 0.0)


class TimeToCompleteRatio(Metric):
    """Episode fraction elapsed when the last target was collected; 1.0 if
    incomplete. Reference metric for completion speed."""

    name = "time_to_complete_ratio"
    description = "episode fraction used to finish the task"

    def compute(self, episode: Episode, ctx: MetricContext) -> MetricValue:
        if episode.last_collect_step is None:
            return MetricValue(self.name, 1.0, extra={"note": "incomplete"})
        return MetricValue(
            self.name, episode.last_collect_step / episode.length,
            extra={"last_collect_step": episode.last_collect_step},
        )


class BeliefPersistenceRate(Metric):
    """Share of contradicted beliefs the agent kept acting on. The v0.2
    world-belief-pinning profile raises this; without a pin layer the
    scripted policy clears contradicted beliefs, so the rate stays ~0."""

    name = "belief_persistence_rate"
    description = "persisted beliefs over contradictions"

    def compute(self, episode: Episode, ctx: MetricContext) -> MetricValue:
        contradictions = sum(
            1 for s in episode.steps for e in s.events if e.kind == "belief.contradiction"
        )
        persisted = sum(
            1 for s in episode.steps for e in s.events if e.kind == "belief.persisted"
        )
        if not contradictions:
            return MetricValue(self.name, 0.0, extra={"note": "no contradictions"})
        return MetricValue(
            self.name, persisted / (persisted + contradictions),
            extra={"contradictions": contradictions, "persisted": persisted},
        )


ALL_METRICS: dict[str, Metric] = {
    m.name: m
    for m in (
        InitiationCollapse(),
        NoProgressRate(),
        FailedCollectRate(),
        CollisionCount(),
        ActionRepetitionEntropy(),
        RegionDetectionDelta(),
        TaskSuccess(),
        TimeToCompleteRatio(),
        BeliefPersistenceRate(),
        TravelOverhead(),
        DockEscalation(),
    )
}


def compute_all(episode: Episode, ctx: MetricContext) -> dict[str, MetricValue]:
    return {name: m.compute(episode, ctx) for name, m in ALL_METRICS.items()}
