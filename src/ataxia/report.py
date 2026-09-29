"""Comparison reports and the experiment runner.

A report is always an A/B: the same standard episode run through the
profile's layer chain and through the healthy baseline, same seeds. The
delta is the primary output; the 0-3 level on each scale is indicative and
normed against PseudoBot.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from .core.models import PseudoBotWorld, ScriptedPolicy
from .core.session import EpisodeSession
from .core.types import Episode
from .metrics.base import MetricContext
from .metrics.instruments import ALL_METRICS
from .metrics.scales import SymptomScale
from .profiles import HEALTHY_KEY, Profile, compose_profile, get_profile

DISCLAIMER = (
    "Emulation, not diagnosis. Levels describe a scripted, manipulated "
    "policy in a simulator — not a robot having a disorder, and not a claim "
    "about machine experience. See ETHICS.md."
)

LEVEL_WORDS = ("absent", "mild", "moderate", "marked")


@dataclass
class ScaleRow:
    scale: SymptomScale
    baseline_mean: float
    induced_mean: float
    delta: float
    baseline_level: int
    induced_level: int


@dataclass
class ComparisonReport:
    profile: Profile
    seeds: list[int]
    baseline: list[Episode]
    induced: list[Episode]
    rows: list[ScaleRow]
    ctx: MetricContext

    def render_markdown(self) -> str:
        p = self.profile
        lines = [
            "# Ataxia — Induction Report",
            "",
            f"**Profile:** {p.title} (`{p.key}`) · "
            f"**Environment:** PseudoBot · "
            f"**Seeds:** {', '.join(str(s) for s in self.seeds)} · "
            f"**Date:** {date.today().isoformat()}",
            "",
            f"> ⚠️ {DISCLAIMER}",
            "",
            "## Scales",
            "",
        ]
        if self.rows:
            lines.append(
                "| Scale | Metric | Baseline | Induced | Δ | Level (induced) |"
            )
            lines.append("|---|---|---|---|---|---|")
            for row in self.rows:
                arrow = "↑" if row.scale.direction == "higher" else "↓"
                lines.append(
                    f"| {row.scale.name} | {row.scale.metric} {arrow} "
                    f"| {row.baseline_mean:.2f} | {row.induced_mean:.2f} "
                    f"| {row.delta:+.2f} | {row.induced_level} — "
                    f"{LEVEL_WORDS[row.induced_level]} |"
                )
            lines.append("")
            lines.append(
                "Level legend: 0 absent · 1 mild · 2 moderate · 3 marked "
                "(thresholds normed against PseudoBot)."
            )
        else:
            lines.append("_Baseline profile — no distortion scales._")
        lines.append("")

        lines.append("## Induction dose (layer events per step)")
        lines.append("")
        dose = _dose_table(self.induced)
        if dose:
            lines.append("| Layer | Kind | Events/step (induced) |")
            lines.append("|---|---|---|")
            for (layer, kind), per_step in dose:
                lines.append(f"| {layer} | {kind} | {per_step:.2f} |")
        else:
            lines.append("_No layer events recorded._")
        lines.append("")

        lines.append("## Mechanism notes")
        lines.append("")
        for note in p.mechanism_notes:
            lines.append(f"- {note}")
        lines.append("")
        return "\n".join(lines)

    def render_json(self) -> str:
        data: dict[str, Any] = {
            "profile": self.profile.key,
            "title": self.profile.title,
            "environment": "PseudoBot",
            "seeds": self.seeds,
            "disclaimer": DISCLAIMER,
            "scales": [
                {
                    "name": r.scale.name,
                    "metric": r.scale.metric,
                    "direction": r.scale.direction,
                    "baseline_mean": round(r.baseline_mean, 4),
                    "induced_mean": round(r.induced_mean, 4),
                    "delta": round(r.delta, 4),
                    "baseline_level": r.baseline_level,
                    "induced_level": r.induced_level,
                }
                for r in self.rows
            ],
            "baseline_episodes": [e.to_dict() for e in self.baseline],
            "induced_episodes": [e.to_dict() for e in self.induced],
        }
        return json.dumps(data, indent=2)


def _dose_table(episodes: list[Episode]) -> list[tuple[tuple[str, str], float]]:
    counts: dict[tuple[str, str], int] = {}
    n_steps = 0
    for ep in episodes:
        n_steps += len(ep.steps)
        for step in ep.steps:
            for event in step.events:
                key = (event.layer, event.kind)
                counts[key] = counts.get(key, 0) + 1
    if not n_steps:
        return []
    table = [(key, n / n_steps) for key, n in counts.items()]
    return sorted(table, key=lambda kv: (-kv[1], kv[0]))


def run_experiment(
    profile_key: str,
    seeds: tuple[int, ...] = (1, 2, 3),
) -> ComparisonReport:
    """Run the standard PseudoBot episode through a profile and the healthy
    baseline with identical seeds, and score both."""
    profile = compose_profile(profile_key)
    ctx = MetricContext()

    def _run(target: Profile, seed: int) -> Episode:
        world = PseudoBotWorld()
        policy = ScriptedPolicy(seed)
        return EpisodeSession(world, policy, target).run(seed)

    baseline = [_run(get_profile(HEALTHY_KEY), s) for s in seeds]
    induced = [_run(profile, s) for s in seeds]

    rows: list[ScaleRow] = []
    for scale in profile.scales:
        metric = ALL_METRICS[scale.metric]
        base_vals = [metric.compute(e, ctx).value for e in baseline]
        ind_vals = [metric.compute(e, ctx).value for e in induced]
        base_mean = sum(base_vals) / len(base_vals)
        ind_mean = sum(ind_vals) / len(ind_vals)
        rows.append(
            ScaleRow(
                scale=scale,
                baseline_mean=base_mean,
                induced_mean=ind_mean,
                delta=ind_mean - base_mean,
                baseline_level=scale.level(base_mean),
                induced_level=scale.level(ind_mean),
            )
        )

    return ComparisonReport(
        profile=profile,
        seeds=list(seeds),
        baseline=baseline,
        induced=induced,
        rows=rows,
        ctx=ctx,
    )
