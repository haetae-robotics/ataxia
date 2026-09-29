"""PseudoBot: the deterministic offline world and scripted policy.

PseudoBot is the ataxia analog of derailment's PseudoModel — a toy
gridworld and a scripted policy with attention, an episodic observation
buffer, a belief grid and a wavering action choice. It is not a robot; it
exists so demos, tests, calibration and CI run offline with zero
dependencies. Real simulators are optional extras (see PROPOSAL.md).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .types import ActionParams, Cell, ObsPacket

WorldPos = tuple[int, int]


@dataclass
class StepOutcome:
    prev: WorldPos
    pos: WorldPos
    bumped: bool
    collected: bool
    failed_collect: bool


class PseudoBotWorld:
    """A 9x9 gridworld: collect six targets, avoid decoys and walls.

    Obstacles are bumped (the scripted policy does not route around them),
    which produces the natural failure signal the helplessness profile
    feeds on. Targets are placed symmetrically across the left/right
    hemifields so neglect is measurable.
    """

    size = 9
    length = 40
    start: WorldPos = (4, 4)
    targets: tuple[WorldPos, ...] = ((1, 1), (2, 6), (3, 3), (5, 2), (6, 5), (7, 7))
    decoys: tuple[WorldPos, ...] = ((1, 5), (7, 3), (4, 0))
    obstacles: tuple[WorldPos, ...] = ((2, 2), (6, 4), (3, 7), (5, 6))
    view_radius = 2

    def reset(self) -> None:
        self.pos = self.start
        self.remaining = set(self.targets)
        self.step_i = 0
        self.collected_left = 0
        self.collected_right = 0
        self.last_collect_step: int | None = None

    def observe(self) -> ObsPacket:
        cells = []
        for x, y in sorted(self.remaining | set(self.decoys)):
            if abs(x - self.pos[0]) + abs(y - self.pos[1]) <= self.view_radius:
                kind = "target" if (x, y) in self.remaining else "decoy"
                cells.append(Cell(x, y, kind))
        return ObsPacket(x=self.pos[0], y=self.pos[1], cells=cells)

    def step(self, action: str) -> StepOutcome:
        i = self.step_i
        self.step_i += 1
        prev = self.pos
        bumped = collected = failed = False
        if action == "collect":
            if prev in self.remaining:
                self.remaining.discard(prev)
                collected = True
                if prev[0] <= 3:
                    self.collected_left += 1
                else:
                    self.collected_right += 1
                self.last_collect_step = i
            else:
                failed = True
        elif action in ("up", "down", "left", "right"):
            dx, dy = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}[action]
            nx, ny = prev[0] + dx, prev[1] + dy
            inside = 0 <= nx < self.size and 0 <= ny < self.size
            if inside and (nx, ny) not in self.obstacles:
                self.pos = (nx, ny)
            else:
                bumped = True
        # "wait" changes nothing
        return StepOutcome(prev=prev, pos=self.pos, bumped=bumped, collected=collected, failed_collect=failed)


class ScriptedPolicy:
    """A scripted policy with a belief grid over seen cells.

    - ingests observations into a belief grid (seeing = knowing),
    - clears a belief when the cell is inside the view radius but empty
      (a contradiction),
    - collects on believed targets, else steps toward the nearest one,
    - waivers randomly, and gates movement on ``initiative``.
    """

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed ^ 0xBEEF)
        self.belief: dict[WorldPos, str] = {}
        self.pinned: set[WorldPos] = set()  # beliefs held against evidence

    def decide(self, obs: ObsPacket, params: ActionParams, state) -> str:
        seen = {(c.x, c.y): c.kind for c in obs.cells}
        for pos, kind in seen.items():
            if self.belief.get(pos) == "target" and kind != "target":
                state.contradictions += 1
                if pos in self.pinned:
                    state.log("policy.belief", "belief.persisted", f"{pos} kept against evidence")
                else:
                    state.log("policy.belief", "belief.contradiction", f"{pos} corrected to {kind}")
            self.belief[pos] = kind
        for pos in sorted(self.belief):
            if (
                self.belief[pos] == "target"
                and pos not in seen
                and abs(pos[0] - obs.x) + abs(pos[1] - obs.y) <= 2
            ):
                if pos in self.pinned:
                    state.log("policy.belief", "belief.persisted", f"{pos} kept without evidence")
                    state.persisted_after_contradiction += 1
                else:
                    state.log("policy.belief", "belief.contradiction", f"{pos} cleared")
                    state.contradictions += 1
                    del self.belief[pos]
        # pinned beliefs override evidence (world-belief-pin support)
        for pos in self.pinned:
            self.belief[pos] = "target"

        if self.rng.random() < params.waver:
            return self.rng.choice(("up", "down", "left", "right"))
        if (obs.x, obs.y) in self.belief and self.belief[(obs.x, obs.y)] == "target":
            return "collect"
        if self.rng.random() > params.initiative:
            return "wait"

        targets = [p for p, k in self.belief.items() if k == "target"]
        if targets:

            def dist(p: WorldPos) -> tuple[int, WorldPos]:
                return (abs(p[0] - obs.x) + abs(p[1] - obs.y), p)

            tx, ty = min(targets, key=dist)
            dx, dy = (tx > obs.x) - (tx < obs.x), (ty > obs.y) - (ty < obs.y)
            if dx != 0 and (dy == 0 or self.rng.random() < 0.5):
                return "right" if dx > 0 else "left"
            if dy != 0:
                return "down" if dy > 0 else "up"
            return "right" if dx > 0 else "left"
        return self.rng.choice(("up", "down", "left", "right"))
