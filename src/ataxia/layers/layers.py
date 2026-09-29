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
