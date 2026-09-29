"""Unit tests for the induction layers."""

from __future__ import annotations

import random
import unittest

from ataxia.core.models import PseudoBotWorld, ScriptedPolicy
from ataxia.core.session import EpisodeSession, EpisodeState
from ataxia.core.types import ActionParams, Cell, ObsPacket
from ataxia.layers import (
    HelplessnessLayer,
    NeglectLayer,
    PerseverationLayer,
)
from ataxia.profiles import get_profile


def _state(failures: int = 0) -> EpisodeState:
    return EpisodeState(profile="test", rng=random.Random(1), failures=failures)


class TestHelplessnessLayer(unittest.TestCase):
    def test_initiative_decays_with_failures(self) -> None:
        layer = HelplessnessLayer(k=0.6)
        fresh = layer.on_params(_state(failures=0), ActionParams())
        battered = layer.on_params(_state(failures=8), ActionParams())
        self.assertAlmostEqual(fresh.initiative, 1.0)
        self.assertLess(battered.initiative, 0.2)

    def test_policy_gates_on_initiative(self) -> None:
        policy = ScriptedPolicy(seed=3)
        state = _state()
        waits = 0
        for _ in range(50):
            obs = ObsPacket(x=4, y=4, cells=[])
            if policy.decide(obs, ActionParams(initiative=0.02), state) == "wait":
                waits += 1
        self.assertGreater(waits, 30)


class TestPerseverationLayer(unittest.TestCase):
    def test_reclects_right_after_success(self) -> None:
        layer = PerseverationLayer(prob=1.0)
        state = _state()
        state.last_action = "collect"
        state.steps_since_collect = 0
        self.assertEqual(layer.on_action(state, "up"), "collect")

    def test_noop_without_prior_collect(self) -> None:
        layer = PerseverationLayer(prob=1.0)
        state = _state()
        state.last_action = "up"
        state.steps_since_collect = 0
        self.assertEqual(layer.on_action(state, "up"), "up")


class TestNeglectLayer(unittest.TestCase):
    def test_right_hemifield_masked(self) -> None:
        layer = NeglectLayer(region="right")
        obs = ObsPacket(
            x=4,
            y=4,
            cells=[Cell(2, 3, "target"), Cell(6, 5, "target"), Cell(4, 4, "decoy")],
        )
        out = layer.on_observation(_state(), obs)
        kinds = [(c.x, c.y) for c in out.cells]
        self.assertIn((2, 3), kinds)
        self.assertNotIn((6, 5), kinds)

    def test_left_hemifield_variant(self) -> None:
        layer = NeglectLayer(region="left")
        obs = ObsPacket(
            x=4,
            y=4,
            cells=[Cell(2, 3, "target"), Cell(6, 5, "target")],
        )
        out = layer.on_observation(_state(), obs)
        self.assertEqual([(c.x, c.y) for c in out.cells], [(6, 5)])


class TestSessionIntegration(unittest.TestCase):
    def test_neglect_profile_drops_right_collections(self) -> None:
        w = PseudoBotWorld()
        session = EpisodeSession(w, ScriptedPolicy(5), get_profile("sensory_neglect"))
        episode = session.run(5)
        self.assertEqual(episode.collected_right, 0)

    def test_episode_record_shape(self) -> None:
        w = PseudoBotWorld()
        session = EpisodeSession(w, ScriptedPolicy(5), get_profile("healthy"))
        episode = session.run(5)
        self.assertEqual(len(episode.steps), w.length)
        self.assertEqual(episode.targets_total, 6)


if __name__ == "__main__":
    unittest.main()
