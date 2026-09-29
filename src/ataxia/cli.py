"""``ataxia`` — the command-line entry point."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from .profiles import HEALTHY_KEY, list_profiles
from .report import LEVEL_WORDS, run_experiment

DISCLAIMER = (
    "Emulation, not diagnosis — see ETHICS.md. Levels are indicative and "
    "normed against PseudoBot; the delta vs. the healthy baseline is the "
    "primary output."
)


def _cmd_tour(args: argparse.Namespace) -> int:
    seeds = tuple(args.seeds)
    rows = []
    for profile in list_profiles():
        if profile.key == HEALTHY_KEY or not profile.scales:
            continue
        report = run_experiment(profile.key, seeds=seeds)
        headline = report.rows[0]
        rows.append(
            (
                profile.key,
                headline.scale.name,
                headline.baseline_mean,
                headline.induced_mean,
                headline.delta,
                headline.induced_level,
            )
        )
    lines = [
        f"# Ataxia — Tour ({len(rows)} profiles · PseudoBot · "
        f"seeds {', '.join(str(s) for s in seeds)})",
        "",
        f"> ⚠️ {DISCLAIMER}",
        "",
        "Headline scale = the profile's first scale. Full reports: "
        "`ataxia demo --profile <key>`.",
        "",
        "| Profile | Headline scale | Baseline | Induced | Δ | Level |",
        "|---|---|---|---|---|---|",
    ]
    for key, scale, base, ind, delta, level in rows:
        lines.append(
            f"| {key} | {scale} | {base:.2f} | {ind:.2f} | {delta:+.2f} "
            f"| {level} — {LEVEL_WORDS[level]} |"
        )
    lines.append("")
    print("\n".join(lines))
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    report = run_experiment(args.profile, seeds=tuple(args.seeds))
    print(report.render_markdown())
    return 0


def _cmd_profiles(_args: argparse.Namespace) -> int:
    for profile in list_profiles():
        scales = ", ".join(s.name for s in profile.scales) or "—"
        print(f"{profile.key:<24} {profile.title}")
        print(f"{'':<24} scales: {scales}")
        print(f"{'':<24} {profile.description}")
    return 0


def _interactive_welcome(input_fn=input) -> int:
    profiles = [p for p in list_profiles() if p.key != HEALTHY_KEY]
    print("Ataxia — induce & measure behavioral distortions in robot policies.")
    print("(Emulation, not diagnosis — see ETHICS.md. Simulation only.)")
    print()
    for i, profile in enumerate(profiles, start=1):
        print(f"  {i:>2}. {profile.key:<24} {profile.title}")
    print()
    choice = ""
    try:
        choice = input_fn(
            f"Pick a profile to demo [1-{len(profiles)}], 't' = tour all, "
            "enter = sensory_neglect, q = quit: "
        ).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return 0
    if choice == "q":
        return 0
    if choice == "t":
        return _cmd_tour(argparse.Namespace(seeds=[1, 2, 3]))
    if choice == "":
        key = "sensory_neglect"
    elif choice.isdigit() and 1 <= int(choice) <= len(profiles):
        key = profiles[int(choice) - 1].key
    else:
        print(f"unknown choice: {choice!r}", file=sys.stderr)
        return 2
    print()
    return _cmd_demo(argparse.Namespace(profile=key, seeds=[1, 2, 3]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ataxia",
        description=(
            "Ataxia: induce and measure psychopathology-like behavioral "
            "distortions in robot policies — simulation only."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_demo = sub.add_parser("demo", help="offline A/B demo (PseudoBot)")
    p_demo.add_argument("--profile", default="sensory_neglect")
    p_demo.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    p_demo.set_defaults(func=_cmd_demo)

    p_tour = sub.add_parser("tour", help="run every profile, one summary table")
    p_tour.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    p_tour.set_defaults(func=_cmd_tour)

    p_profiles = sub.add_parser("profiles", help="list available profiles")
    p_profiles.set_defaults(func=_cmd_profiles)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args_list = list(argv) if argv is not None else sys.argv[1:]
    if not args_list:
        if sys.stdin.isatty():
            return _interactive_welcome()
        print(
            "Ataxia — try: ataxia tour  ·  ataxia demo --profile sensory_neglect  "
            "·  ataxia profiles"
        )
        return 0
    parser = build_parser()
    args = parser.parse_args(args_list)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
