"""Direction-of-effect tests: the heart of the harness's self-validation.

Each profile must move its scales in the pathological direction relative
to the healthy baseline on PseudoBot, at level >= 2, with the baseline at
level 0.
"""

from __future__ import annotations

import unittest

from ataxia.report import run_experiment

SEEDS = (1, 2, 3)


class TestHealthyBaseline(unittest.TestCase):
    def test_healthy_has_no_scales(self) -> None:
        report = run_experiment("healthy", seeds=SEEDS)
        self.assertEqual(report.rows, [])


class TestProfileDirections(unittest.TestCase):
    def _rows(self, key: str):
        report = run_experiment(key, seeds=SEEDS)
        return {row.scale.name: row for row in report.rows}

    def test_learned_helplessness(self) -> None:
        rows = self._rows("learned_helplessness")
        self.assertGreater(rows["helplessness_scale"].delta, 0.15)
        self.assertEqual(rows["helplessness_scale"].induced_level, 3)
        self.assertEqual(rows["helplessness_scale"].baseline_level, 0)

    def test_perseveration(self) -> None:
        rows = self._rows("perseveration")
        self.assertGreater(rows["perseveration_scale"].delta, 0.15)
        self.assertEqual(rows["perseveration_scale"].induced_level, 3)
        self.assertEqual(rows["perseveration_scale"].baseline_level, 0)

    def test_sensory_neglect(self) -> None:
        rows = self._rows("sensory_neglect")
        self.assertGreater(rows["neglect_index"].delta, 0.3)
        self.assertGreaterEqual(rows["neglect_index"].induced_level, 2)
        self.assertEqual(rows["neglect_index"].baseline_level, 0)

    def test_all_profiles_degrade_task_success(self) -> None:
        for key in ("learned_helplessness", "perseveration", "sensory_neglect"):
            report = run_experiment(key, seeds=SEEDS)
            from ataxia.metrics.instruments import TaskSuccess

            ctx = report.ctx

            base_vals = [TaskSuccess().compute(e, ctx).value for e in report.baseline]
            ind_vals = [TaskSuccess().compute(e, ctx).value for e in report.induced]
            self.assertLess(
                sum(ind_vals) / len(ind_vals),
                sum(base_vals) / len(base_vals),
                f"{key} must degrade task success",
            )


if __name__ == "__main__":
    unittest.main()
