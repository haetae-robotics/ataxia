"""Helpers for building synthetic episodes in tests."""

from __future__ import annotations

from ataxia.core.types import (
    ActionParams,
    Episode,
    LayerEvent,
    StepRecord,
)


def make_episode(
    actions: list[str],
    bumped: list[bool] | None = None,
    collected: list[bool] | None = None,
    failed: list[bool] | None = None,
    collected_left: int = 3,
    collected_right: int = 3,
    last_collect_step: int | None = None,
    events: list[list[LayerEvent]] | None = None,
) -> Episode:
    n = len(actions)
    bumped = bumped if bumped is not None else [False] * n
    collected = collected if collected is not None else [False] * n
    failed = failed if failed is not None else [False] * n
    events = events if events is not None else [[] for _ in range(n)]
    steps = [
        StepRecord(
            index=i,
            action=actions[i],
            prev=(4, 4),
            pos=(4, 4),
            bumped=bumped[i],
            collected=collected[i],
            failed_collect=failed[i],
            params=ActionParams(),
            events=events[i],
        )
        for i in range(n)
    ]
    return Episode(
        profile="test",
        seed=0,
        length=n,
        steps=steps,
        targets_total=6,
        collected_left=collected_left,
        collected_right=collected_right,
        targets_left=3,
        targets_right=3,
        last_collect_step=last_collect_step,
    )
