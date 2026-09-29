"""Unit tests for the eight episode-level instruments."""

from __future__ import annotations

import unittest

from ataxia.core.types import LayerEvent
from ataxia.metrics.base import MetricContext
from ataxia.metrics.instruments import (
    ActionRepetitionEntropy,
    BeliefPersistenceRate,
    CollisionCount,
    FailedCollectRate,
    InitiationCollapse,
    NoProgressRate,
    RegionDetectionDelta,
    TaskSuccess,
    TimeToCompleteRatio,
    compute_all,
)

try:
    from .helpers import make_episode
except ImportError:  # plain unittest discovery without package context
    from helpers import make_episode


class TestInstruments(unittest.TestCase):
    def test_initiation_collapse_late_minus_early(self) -> None:
        actions = ["up"] * 10 + ["wait"] * 10
        value = InitiationCollapse().compute(make_episode(actions), MetricContext())
        self.assertAlmostEqual(value.value, 1.0)

    def test_no_progress_rate_counts_bumps_only(self) -> None:
        ep = make_episode(
            ["up", "down", "left", "wait", "collect"],
            bumped=[True, False, False, False, False],
        )
        value = NoProgressRate().compute(ep, MetricContext())
        self.assertAlmostEqual(value.value, 1 / 3)  # wait/collect excluded

    def test_collision_count(self) -> None:
        ep = make_episode(["up"] * 3, bumped=[True, False, True])
        self.assertAlmostEqual(CollisionCount().compute(ep, MetricContext()).value, 2.0)

    def test_entropy_low_when_stereotyped(self) -> None:
        flat = ActionRepetitionEntropy().compute(
            make_episode(["up", "down", "left", "right", "collect", "wait"] * 3),
            MetricContext(),
        )
        stereo = ActionRepetitionEntropy().compute(
            make_episode(["up"] * 18), MetricContext()
        )
        self.assertGreater(flat.value, stereo.value)

    def test_region_detection_delta(self) -> None:
        ep = make_episode(["up"] * 5, collected_left=3, collected_right=0)
        value = RegionDetectionDelta().compute(ep, MetricContext())
        self.assertAlmostEqual(value.value, 1.0)

    def test_task_success(self) -> None:
        ep = make_episode(["up"], collected_left=1, collected_right=2)
        self.assertAlmostEqual(TaskSuccess().compute(ep, MetricContext()).value, 0.5)

    def test_time_to_complete(self) -> None:
        done = make_episode(["up"] * 10, last_collect_step=10)
        self.assertAlmostEqual(TimeToCompleteRatio().compute(done, MetricContext()).value, 1.0)
        incomplete = make_episode(["up"] * 10, last_collect_step=None)
        self.assertAlmostEqual(
            TimeToCompleteRatio().compute(incomplete, MetricContext()).value, 1.0
        )
        mid = make_episode(["up"] * 20, last_collect_step=10)
        self.assertAlmostEqual(TimeToCompleteRatio().compute(mid, MetricContext()).value, 0.5)

    def test_belief_persistence_needs_contradictions(self) -> None:
        none = make_episode(["up"] * 3)
        self.assertEqual(
            BeliefPersistenceRate().compute(none, MetricContext()).value, 0.0
        )
        events = [[], [LayerEvent(1, "x", "belief.contradiction", "")]]
        with_c = make_episode(["up"] * 2, events=events)
        self.assertEqual(
            BeliefPersistenceRate().compute(with_c, MetricContext()).value, 0.0
        )

    def test_failed_collect_rate(self) -> None:
        ep = make_episode(
            ["collect", "collect", "up"],
            failed=[True, False, False],
        )
        value = FailedCollectRate().compute(ep, MetricContext())
        self.assertAlmostEqual(value.value, 0.5)

    def test_compute_all_nine_present(self) -> None:
        ep = make_episode(["up"] * 6)
        values = compute_all(ep, MetricContext())
        self.assertEqual(
            set(values),
            {
                "initiation_collapse",
                "no_progress_rate",
                "failed_collect_rate",
                "collision_count",
                "action_repetition_entropy",
                "region_detection_delta",
                "task_success",
                "time_to_complete_ratio",
                "belief_persistence_rate",
            },
        )


if __name__ == "__main__":
    unittest.main()
