"""Metric protocol and shared plumbing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.types import Episode


@dataclass
class MetricContext:
    """Episode-level metadata (region layout etc.). Filled from the world."""

    left_edge: int = 3
    right_edge: int = 5
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricValue:
    name: str
    value: float
    series: list[float] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


class Metric:
    """A pure function over an episode. No simulation, no I/O."""

    name: str = "metric"
    description: str = ""

    def compute(self, episode: Episode, ctx: MetricContext) -> MetricValue:
        raise NotImplementedError
