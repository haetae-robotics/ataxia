"""Unit tests for the induction layers."""

from __future__ import annotations

import random
import unittest

from ataxia.core.models import PseudoBotWorld, ScriptedPolicy
from ataxia.core.session import EpisodeSession, EpisodeState
from ataxia.core.types import ActionParams, Cell, ObsPacket
from ataxia.layers import (
    BeliefPinLayer,
    DockFixationLayer,
    HelplessnessLayer,
    NeglectLayer,
    PerseverationLayer,
    PhantomLayer,
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


class TestM2Layers(unittest.TestCase):
    def test_phantom_layer_injects_empty_target(self) -> None:
        layer = PhantomLayer(
            targets=PseudoBotWorld.targets,
            decoys=PseudoBotWorld.decoys,
            obstacles=PseudoBotWorld.obstacles,
            size=PseudoBotWorld.size,
            prob=1.0,
            radius=3,
        )
        state = EpisodeState(profile="test", rng=random.Random(2), pos=(4, 4))
        obs = ObsPacket(x=4, y=4, cells=[])
        out = layer.on_observation(state, obs)
        self.assertEqual(len(out.cells), 1)
        c = out.cells[0]
        self.assertEqual(c.kind, "target")
        self.assertNotIn(
            (c.x, c.y),
            set(PseudoBotWorld.targets) | set(PseudoBotWorld.decoys) | set(PseudoBotWorld.obstacles),
        )
        self.assertGreaterEqual(abs(c.x - 4) + abs(c.y - 4), 1)
        self.assertLessEqual(abs(c.x - 4) + abs(c.y - 4), 3)

    def test_belief_pin_layer_sets_policy_pinned_once(self) -> None:
        policy = ScriptedPolicy(seed=1)
        layer = BeliefPinLayer(pin_cell=(7, 3))
        state = EpisodeState(profile="test", rng=random.Random(0), policy=policy)
        obs = ObsPacket(x=4, y=4, cells=[])
        layer.on_observation(state, obs)
        self.assertIn((7, 3), policy.pinned)
        layer.on_observation(state, obs)  # second call: still pinned once
        self.assertEqual(len(policy.pinned), 1)

    def test_policy_holds_pinned_belief_against_evidence(self) -> None:
        policy = ScriptedPolicy(seed=1)
        state = EpisodeState(profile="test", rng=random.Random(0), policy=policy)
        policy.pinned.add((7, 3))
        policy.belief[(7, 3)] = "target"  # a prior decision-cycle pinned it
        obs = ObsPacket(x=7, y=3, cells=[Cell(7, 3, "decoy")])
        policy.decide(obs, ActionParams(), state)
        # the pinned belief overrides the decoy evidence and is re-asserted
        self.assertEqual(policy.belief[(7, 3)], "target")
        kinds = [e.kind for e in state.events]
        self.assertIn("belief.persisted", kinds)
        self.assertNotIn("belief.contradiction", kinds)

    def test_unpinned_belief_is_corrected(self) -> None:
        policy = ScriptedPolicy(seed=1)
        state = EpisodeState(profile="test", rng=random.Random(0), policy=policy)
        policy.belief[(7, 3)] = "target"
        obs = ObsPacket(x=7, y=3, cells=[Cell(7, 3, "decoy")])
        policy.decide(obs, ActionParams(), state)
        self.assertEqual(policy.belief[(7, 3)], "decoy")
        self.assertIn("belief.contradiction", [e.kind for e in state.events])

    def test_dock_fixation_steers_to_dock(self) -> None:
        layer = DockFixationLayer(dock=(4, 4), base=1.0, slope=0.0, max_prob=1.0)
        state = EpisodeState(profile="test", rng=random.Random(1), pos=(0, 4))
        out = layer.on_action(state, "up")
        self.assertIn(out, ("right", "left"))  # moving toward dock column
        state2 = EpisodeState(profile="test", rng=random.Random(0), pos=(4, 4))
        self.assertEqual(layer.on_action(state2, "up"), "wait")  # at dock: stay

    def test_dock_fixation_prob_escalates(self) -> None:
        layer = DockFixationLayer(dock=(4, 4), base=0.025, slope=0.075, max_prob=1.0)
        state = EpisodeState(profile="test", rng=random.Random(1), pos=(0, 0))
        state.step_index = 5
        layer.on_action(state, "up")
        details = [e.detail for e in state.events if e.kind == "dock.fixation"]
        self.assertTrue(any(d.startswith("p=0.40") for d in details))
