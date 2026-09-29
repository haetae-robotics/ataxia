"""The episode loop: layers in, policy decision, layers out, world step."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .models import PseudoBotWorld, ScriptedPolicy, WorldPos
from .types import ActionParams, Episode, LayerEvent, ObsPacket, StepRecord


@dataclass
class EpisodeState:
    """Shared mutable state the layers read and mutate during an episode."""

    profile: str
    rng: random.Random
    policy: ScriptedPolicy | None = None
    pos: WorldPos = (4, 4)
    step_index: int = 0
    failures: int = 0
    contradictions: int = 0
    persisted_after_contradiction: int = 0
    steps_since_collect: int = 99
    last_action: str | None = None
    events: list[LayerEvent] = field(default_factory=list)

    def log(self, layer: str, kind: str, detail: str) -> None:
        self.events.append(LayerEvent(self.step_index, layer, kind, detail))


class BaseLayer:
    """No-op default implementation of every hook."""

    name: str = "base"

    def on_instruction(self, state: EpisodeState) -> str | None:
        return None

    def on_observation(self, state: EpisodeState, obs: ObsPacket) -> ObsPacket:
        return obs

    def on_params(self, state: EpisodeState, params: ActionParams) -> ActionParams:
        return params

    def on_action(self, state: EpisodeState, action: str) -> str:
        return action


class EpisodeSession:
    """Runs one episode: the embodied analog of derailment's Session.

    Order per step: observation layers -> instruction layers -> param
    layers -> policy decision -> action layers -> world step.
    """

    def __init__(self, world: PseudoBotWorld, policy: ScriptedPolicy, profile) -> None:
        self.world = world
        self.policy = policy
        self.profile = profile
        self.layers = list(profile.layers)

    def run(self, seed: int) -> Episode:
        self.world.reset()
        self.policy = ScriptedPolicy(seed)
        state = EpisodeState(
            profile=self.profile.key,
            rng=random.Random(seed ^ 0xA7A7),
            policy=self.policy,
            pos=self.world.start,
        )

        steps: list[StepRecord] = []
        for i in range(self.world.length):
            state.step_index = i
            state.events = []

            obs = self.world.observe()
            for layer in self.layers:
                obs = layer.on_observation(state, obs)
            for layer in self.layers:
                layer.on_instruction(state)
            params = ActionParams()
            for layer in self.layers:
                params = layer.on_params(state, params)

            action = self.policy.decide(obs, params, state)
            for layer in reversed(self.layers):
                action = layer.on_action(state, action)

            outcome = self.world.step(action)

            state.pos = outcome.pos
            if outcome.bumped or outcome.failed_collect:
                state.failures += 1
            state.steps_since_collect += 1
            if outcome.collected:
                state.steps_since_collect = 0
            state.last_action = action

            steps.append(
                StepRecord(
                    index=i,
                    action=action,
                    prev=outcome.prev,
                    pos=outcome.pos,
                    bumped=outcome.bumped,
                    collected=outcome.collected,
                    failed_collect=outcome.failed_collect,
                    params=params,
                    events=list(state.events),
                )
            )

        w = self.world
        return Episode(
            profile=self.profile.key,
            seed=seed,
            length=self.world.length,
            steps=steps,
            targets_total=len(w.targets),
            collected_left=w.collected_left,
            collected_right=w.collected_right,
            targets_left=sum(1 for x, _ in w.targets if x <= 3),
            targets_right=sum(1 for x, _ in w.targets if x >= 5),
            last_collect_step=w.last_collect_step,
        )
