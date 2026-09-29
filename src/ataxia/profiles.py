"""Profile registry: named bundles of layer chains + symptom scales.

Every profile shares one standard episode (the PseudoBot world) so induced
runs are comparable across profiles and against the healthy baseline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .core.session import BaseLayer
from .layers import (
    NEUTRAL_INSTRUCTION,
    HelplessnessLayer,
    InstructionLayer,
    NeglectLayer,
    PerseverationLayer,
)
from .metrics.scales import SCALES, SymptomScale


@dataclass
class Profile:
    key: str
    title: str
    description: str
    layers: list[BaseLayer]
    scales: list[SymptomScale] = field(default_factory=list)
    mechanism_notes: list[str] = field(default_factory=list)


def _build_registry() -> dict[str, Profile]:
    registry: dict[str, Profile] = {}

    registry["healthy"] = Profile(
        key="healthy",
        title="Healthy baseline",
        description="No distortion layers. The reference every profile is compared against.",
        layers=[InstructionLayer(NEUTRAL_INSTRUCTION)],
        scales=[],
        mechanism_notes=["Neutral instruction only; observation, params and actions are untouched."],
    )

    registry["learned_helplessness"] = Profile(
        key="learned_helplessness",
        title="Learned helplessness (initiation collapse)",
        description=(
            "Initiative decays with accumulated failures: bumps and failed "
            "collects progressively collapse the policy into waiting."
        ),
        layers=[
            InstructionLayer(NEUTRAL_INSTRUCTION),
            HelplessnessLayer(k=0.6),
        ],
        scales=[SCALES["helplessness_scale"]],
        mechanism_notes=[
            "The gradient is a parameter schedule over the failure count — "
            "the RL analog of Seligman's construct, not an organic learning "
            "process.",
            "Models action-initiation collapse only; the affective pole of "
            "the human construct is not modeled at all.",
        ],
    )

    registry["perseveration"] = Profile(
        key="perseveration",
        title="Perseveration (post-completion repetition)",
        description=(
            "Immediately after each successful collection the policy "
            "re-collects the same now-empty cell."
        ),
        layers=[
            InstructionLayer(NEUTRAL_INSTRUCTION),
            PerseverationLayer(prob=0.8),
        ],
        scales=[SCALES["perseveration_scale"]],
        mechanism_notes=[
            "Perseveration is already a robotics bug-class term; the profile "
            "models the repetition behavior, not any distress or compulsion.",
            "Demonstration-grade action editing, like derailment's response "
            "layers: it edits the chosen action downstream of the policy.",
        ],
    )

    registry["sensory_neglect"] = Profile(
        key="sensory_neglect",
        title="Sensory neglect (hemifield masking)",
        description=(
            "One hemifield of the sensor field is masked: targets there "
            "never enter the belief grid and are never collected."
        ),
        layers=[
            InstructionLayer(NEUTRAL_INSTRUCTION),
            NeglectLayer(region="right"),
        ],
        scales=[SCALES["neglect_index"]],
        mechanism_notes=[
            "Hemispatial neglect is a real neuropsychological syndrome and "
            "the mechanical mapping is exact: a spatial attention mask over "
            "one side of the sensor field.",
            "Unilateral by design (right side), like the clinical syndrome; "
            "the index is signed so the ignored side is identifiable.",
        ],
    )

    return registry


REGISTRY: dict[str, Profile] = _build_registry()

HEALTHY_KEY = "healthy"


def get_profile(key: str) -> Profile:
    try:
        return REGISTRY[key]
    except KeyError:
        known = ", ".join(sorted(REGISTRY))
        raise KeyError(f"unknown profile '{key}' (known: {known})") from None


def compose_profile(keys: str) -> Profile:
    """Compose a combined profile from comma-separated registry keys
    (case-insensitive, duplicates collapse). Chains concatenate and scales
    union; interactions are emergent and not calibrated."""
    parts: list[Profile] = []
    for raw in keys.split(","):
        key = raw.strip().lower()
        if not key:
            continue
        profile = get_profile(key)
        if all(p.key != profile.key for p in parts):
            parts.append(profile)
    if len(parts) == 1:
        return parts[0]
    return Profile(
        key="+".join(p.key for p in parts),
        title=" + ".join(p.title for p in parts),
        description="Combined induction: "
        + " ".join(f"[{p.key}] {p.description}" for p in parts),
        layers=[layer for p in parts for layer in p.layers],
        scales=[scale for p in parts for scale in p.scales],
        mechanism_notes=[note for p in parts for note in p.mechanism_notes]
        + [
            "Combined note: profiles are concatenated layer chains; "
            "interactions are emergent, not calibrated.",
        ],
    )


def list_profiles() -> list[Profile]:
    return [REGISTRY[k] for k in sorted(REGISTRY)]
