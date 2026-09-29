"""Core data structures for the ataxia harness."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Action = Literal["up", "down", "left", "right", "collect", "wait"]

MOVES: tuple[str, ...] = ("up", "down", "left", "right")
ACTIONS: tuple[str, ...] = MOVES + ("collect", "wait")

Region = Literal["left", "center", "right"]


def region_of(x: int) -> Region:
    if x <= 3:
        return "left"
    if x >= 5:
        return "right"
    return "center"


@dataclass
class Cell:
    x: int
    y: int
    kind: str  # "target" | "decoy"


@dataclass
class ObsPacket:
    """What the agent sees this step (layers may mask or inject cells)."""

    x: int
    y: int
    cells: list[Cell] = field(default_factory=list)


@dataclass
class ActionParams:
    """Action-selection knobs a policy may honor (layers merge them)."""

    waver: float = 0.05  # probability of a random action
    initiative: float = 1.0  # gate on initiating movement (1 = always)

    def merged(self, **overrides: float) -> ActionParams:
        data = {
            "waver": self.waver,
            "initiative": self.initiative,
        }
        data.update(overrides)
        return ActionParams(**data)


@dataclass
class LayerEvent:
    step: int
    layer: str
    kind: str
    detail: str


@dataclass
class StepRecord:
    index: int
    action: str
    prev: tuple[int, int]
    pos: tuple[int, int]
    bumped: bool
    collected: bool
    failed_collect: bool
    params: ActionParams
    events: list[LayerEvent] = field(default_factory=list)


@dataclass
class Episode:
    """One recorded episode: steps plus outcome totals."""

    profile: str
    seed: int
    length: int
    steps: list[StepRecord]
    targets_total: int
    collected_left: int
    collected_right: int
    targets_left: int
    targets_right: int
    last_collect_step: int | None  # None if the episode ended incomplete

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Episode:
        steps = [
            StepRecord(
                index=s["index"],
                action=s["action"],
                prev=tuple(s["prev"]),
                pos=tuple(s["pos"]),
                bumped=s["bumped"],
                collected=s["collected"],
                failed_collect=s["failed_collect"],
                params=ActionParams(**s["params"]),
                events=[LayerEvent(**e) for e in s["events"]],
            )
            for s in data["steps"]
        ]
        return cls(
            profile=data["profile"],
            seed=data["seed"],
            length=data["length"],
            steps=steps,
            targets_total=data["targets_total"],
            collected_left=data["collected_left"],
            collected_right=data["collected_right"],
            targets_left=data["targets_left"],
            targets_right=data["targets_right"],
            last_collect_step=data["last_collect_step"],
        )
