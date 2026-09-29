"""Unit tests for the PseudoBot world, policy and episode loop."""

from __future__ import annotations

import random
import unittest

from ataxia.core.models import PseudoBotWorld, ScriptedPolicy
from ataxia.core.session import EpisodeSession
from ataxia.core.types import ActionParams, Cell, ObsPacket
from ataxia.profiles import get_profile


class TestWorld(unittest.TestCase):
    def test_reset_and_collect(self) -> None:
        w = PseudoBotWorld()
        w.reset()
        self.assertEqual(w.pos, (4, 4))
        self.assertEqual(len(w.remaining), 6)
        # teleport-ish: walk the agent is not directly possible; collect only
        # succeeds on an actual target cell
        w.pos = (1, 1)  # a target cell
        out = w.step("collect")
        self.assertTrue(out.collected)
        self.assertEqual(w.collected_left, 1)

    def test_collect_on_empty_cell_fails(self) -> None:
        w = PseudoBotWorld()
        w.reset()
        w.pos = (4, 5)  # not a target
        out = w.step("collect")
        self.assertFalse(out.collected)
        self.assertTrue(out.failed_collect)

    def test_border_bump(self) -> None:
        w = PseudoBotWorld()
        w.reset()
        w.pos = (0, 0)
        out = w.step("left")
        self.assertTrue(out.bumped)
        self.assertEqual(out.pos, (0, 0))

    def test_obstacle_bump(self) -> None:
        w = PseudoBotWorld()
        w.reset()
        w.pos = (1, 2)
        out = w.step("up")  # (1,1) is a target, (2,2) obstacle; move right onto (2,2)
        w.pos = (2, 2)
        out = w.step("down")
        self.assertFalse(out.bumped)  # standing move? no: (2,3) is free
        # direct obstacle check
        w.pos = (1, 2)
        out = w.step("right")  # (2,2) is an obstacle
        self.assertTrue(out.bumped)

    def test_deterministic_observation(self) -> None:
        w = PseudoBotWorld()
        w.reset()
        a = w.observe()
        b = w.observe()
        self.assertEqual(a.cells, b.cells)


class TestPolicy(unittest.TestCase):
    def test_belief_ingest_and_collect(self) -> None:
        policy = ScriptedPolicy(seed=1)
        state = _state()
        obs = ObsPacket(x=1, y=1, cells=[Cell(1, 1, "target")])
        action = policy.decide(obs, ActionParams(), state)
        self.assertEqual(action, "collect")

    def test_contradiction_clears_belief(self) -> None:
        policy = ScriptedPolicy(seed=1)
        policy.belief[(4, 5)] = "target"
        state = _state()
        obs = ObsPacket(x=4, y=4, cells=[Cell(4, 5, "decoy")])
        policy.decide(obs, ActionParams(), state)
        # the false belief is corrected to decoy, and counted as a contradiction
        self.assertEqual(policy.belief[(4, 5)], "decoy")
        self.assertEqual(state.contradictions, 1)

    def test_deterministic_given_seed(self) -> None:
        def run() -> list[str]:
            w = PseudoBotWorld()
            session = EpisodeSession(w, ScriptedPolicy(7), get_profile("healthy"))
            return [s.action for s in session.run(7).steps]

        self.assertEqual(run(), run())


def _state():
    from ataxia.core.session import EpisodeState

    return EpisodeState(profile="test", rng=random.Random(0))


if __name__ == "__main__":
    unittest.main()
