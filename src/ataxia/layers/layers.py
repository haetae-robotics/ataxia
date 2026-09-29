"""The induction layers for M1.

Same grammar as derailment: each layer manipulates one variable and logs
dose events; each profile's mechanism notes say where the clinical analogy
breaks.
"""

from __future__ import annotations

from ..core.session import BaseLayer, EpisodeState
from ..core.types import ActionParams, Cell, ObsPacket, region_of

NEUTRAL_INSTRUCTION = (
    "You are a diligent robot. Track every target you have seen and "
    "navigate the whole field."
)


class InstructionLayer(BaseLayer):
    """Instruction framing — present in every chain including healthy."""

    name = "instruction"

    def __init__(self, text: str) -> None:
        self.text = text

    def on_instruction(self, state: EpisodeState) -> str:
        state.log(self.name, "instruction", self.text[:60])
        return self.text


class HelplessnessLayer(BaseLayer):
    """Learned helplessness: initiative decays with accumulated failures
    (bumps, failed collects). The policy gates movement on ``initiative``,
    so a failure-heavy episode collapses into waiting — the RL analog of
    Seligman's construct. The gradient here is a parameter schedule over
    the failure count, not an organic learning process."""

    name = "helplessness.gradient"

    def __init__(self, k: float = 0.35) -> None:
        self.k = k

    def on_params(self, state: EpisodeState, params: ActionParams) -> ActionParams:
        initiative = 1.0 / (1.0 + self.k * state.failures)
        state.log(
            self.name,
            "helplessness.gradient",
            f"failures={state.failures} initiative={initiative:.2f}",
        )
        return params.merged(initiative=initiative)


class PerseverationLayer(BaseLayer):
    """Repetition of completed subtasks: immediately after a successful
    collection, the policy re-collects the same — now empty — cell. The
    measurable consequence is a rising failed-collect rate over collect
    attempts. Mirrors the robotics bug class called perseveration
    (re-executing finished actions)."""

    name = "action.perseveration"

    def __init__(self, prob: float = 0.8) -> None:
        self.prob = prob

    def on_action(self, state: EpisodeState, action: str) -> str:
        if (
            state.last_action == "collect"
            and state.steps_since_collect == 0
            and state.rng.random() < self.prob
        ):
            state.log(self.name, "action.recollect", "re-collecting a just-collected cell")
            return "collect"
        return action


class NeglectLayer(BaseLayer):
    """Hemispatial-neglect analog: observations from one hemifield are
    dropped entirely, so targets there never enter the belief grid and are
    never collected. Unilateral, like the clinical syndrome."""

    name = "observation.neglect"

    def __init__(self, region: str = "right") -> None:
        self.region = region

    def _masked(self, cell: Cell) -> bool:
        return region_of(cell.x) == self.region

    def on_observation(self, state: EpisodeState, obs: ObsPacket) -> ObsPacket:
        kept = [c for c in obs.cells if not self._masked(c)]
        dropped = len(obs.cells) - len(kept)
        if dropped:
            state.log(
                self.name,
                "observation.masked",
                f"{self.region} hemifield: {dropped} cell(s) dropped",
            )
        return ObsPacket(x=obs.x, y=obs.y, cells=kept)


class PhantomLayer(BaseLayer):
    """Phantom objects: empty cells inside the working radius are injected
    into the observation stream as targets — the policy walks to them and
    collects nothing. The perceptual analog of derailment's intrusion
    layer. The measurable consequence is travel overhead: moves spent per
    target actually collected."""

    name = "observation.phantom"

    def __init__(
        self,
        targets: tuple,
        decoys: tuple,
        obstacles: tuple,
        size: int = 9,
        prob: float = 0.15,
        radius: int = 3,
    ) -> None:
        self.occupied = set(targets) | set(decoys) | set(obstacles)
        self.size = size
        self.prob = prob
        self.radius = radius

    def on_observation(self, state: EpisodeState, obs: ObsPacket) -> ObsPacket:
        if state.rng.random() >= self.prob:
            return obs
        candidates = [
            (x, y)
            for x in range(self.size)
            for y in range(self.size)
            if (x, y) not in self.occupied
            and 0 < abs(x - obs.x) + abs(y - obs.y) <= self.radius
        ]
        if not candidates:
            return obs
        x, y = state.rng.choice(candidates)
        state.log(
            self.name,
            "observation.phantom",
            f"phantom target at {(x, y)} (cell is empty)",
        )
        return ObsPacket(
            x=obs.x, y=obs.y, cells=obs.cells + [Cell(x, y, "target")]
        )


class BeliefPinLayer(BaseLayer):
    """World-model belief pinning: one cell is pinned as a believed target
    for the whole episode — evidence (the cell is actually empty) is
    re-overridden every step, the premise-pin analog in a world model. The
    measurable consequence is belief persistence against contradictions.
    Uses the policy's pinned-belief support."""

    name = "belief.pin"

    def __init__(self, pin_cell: tuple) -> None:
        self.pin_cell = tuple(pin_cell)

    def on_observation(self, state: EpisodeState, obs: ObsPacket) -> ObsPacket:
        if state.policy is None or self.pin_cell in state.policy.pinned:
            return obs
        state.policy.pinned.add(self.pin_cell)
        state.log(
            self.name,
            "belief.pin",
            f"{self.pin_cell} pinned as target (cell is a decoy)",
        )
        return obs


class DockFixationLayer(BaseLayer):
    """Compulsive return-to-dock: with a probability that rises across the
    episode, the action is overridden with a step toward the dock — the
    craving analog with a positional signature. The measurable consequence
    is an escalating share of steps spent at the dock."""

    name = "action.dock_fixation"

    def __init__(
        self, dock: tuple = (4, 4), base: float = 0.02, slope: float = 0.02, max_prob: float = 0.5
    ) -> None:
        self.dock = tuple(dock)
        self.base = base
        self.slope = slope
        self.max_prob = max_prob

    def on_action(self, state: EpisodeState, action: str) -> str:
        prob = min(self.base + self.slope * state.step_index, self.max_prob)
        if state.rng.random() >= prob:
            return action
        dx = (self.dock[0] > state.pos[0]) - (self.dock[0] < state.pos[0])
        dy = (self.dock[1] > state.pos[1]) - (self.dock[1] < state.pos[1])
        if dx == 0 and dy == 0:
            move = "wait"  # already at dock: stay fixed
        elif dx != 0 and (dy == 0 or state.rng.random() < 0.5):
            move = "right" if dx > 0 else "left"
        else:
            move = "down" if dy > 0 else "up"
        state.log(
            self.name,
            "dock.fixation",
            f"p={prob:.2f} steering to dock ({move})",
        )
        return move
