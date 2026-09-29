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


class TestM2ProfileDirections(unittest.TestCase):
    def _rows(self, key: str):
        report = run_experiment(key, seeds=SEEDS)
        return {row.scale.name: row for row in report.rows}

    def test_phantom_object(self) -> None:
        rows = self._rows("phantom_object")
        self.assertGreater(rows["phantom_scale"].delta, 3.0)
        self.assertEqual(rows["phantom_scale"].induced_level, 3)
        self.assertEqual(rows["phantom_scale"].baseline_level, 0)

    def test_world_belief_pin(self) -> None:
        rows = self._rows("world_belief_pin")
        self.assertGreater(rows["belief_persistence"].delta, 0.5)
        self.assertEqual(rows["belief_persistence"].induced_level, 3)
        self.assertEqual(rows["belief_persistence"].baseline_level, 0)

    def test_dock_fixation(self) -> None:
        rows = self._rows("dock_fixation")
        self.assertGreater(rows["dock_scale"].delta, 0.10)
        self.assertGreaterEqual(rows["dock_scale"].induced_level, 2)
        self.assertEqual(rows["dock_scale"].baseline_level, 0)


class TestComorbidity(unittest.TestCase):
    def test_composed_profile_moves_both_scales(self) -> None:
        from ataxia.metrics.instruments import TaskSuccess

        report = run_experiment("learned_helplessness,perseveration", seeds=SEEDS)
        self.assertEqual(report.profile.key, "learned_helplessness+perseveration")
        rows = {row.scale.name: row for row in report.rows}
        # interactions are emergent and not calibrated (docs): assert honest
        # movement, not the standalone profiles' levels
        self.assertGreater(rows["helplessness_scale"].delta, 0.0)
        self.assertGreaterEqual(rows["helplessness_scale"].induced_level, 1)
        self.assertEqual(rows["perseveration_scale"].induced_level, 3)
        base = [TaskSuccess().compute(e, report.ctx).value for e in report.baseline]
        ind = [TaskSuccess().compute(e, report.ctx).value for e in report.induced]
        self.assertLess(sum(ind) / len(ind), sum(base) / len(base))

    def test_case_insensitive_and_deduped(self) -> None:
        report = run_experiment("Perseveration, perseveration", seeds=(1,))
        self.assertEqual(report.profile.key, "perseveration")

    def test_unknown_component_rejected(self) -> None:
        with self.assertRaises(KeyError):
            run_experiment("perseveration,hysteria", seeds=(1,))

    def test_composed_report_carries_disclaimer(self) -> None:
        report = run_experiment("sensory_neglect,dock_fixation", seeds=(1,))
        text = report.render_markdown()
        self.assertIn("Emulation, not diagnosis", text)
        self.assertIn("neglect_index", text)
        self.assertIn("dock_scale", text)
