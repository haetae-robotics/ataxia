"""ataxia — derailment for embodied agents.

Induce and measure psychopathology-like behavioral distortions in robot
policies, in simulation. Emulation, not diagnosis. See ETHICS.md.
"""

from .core.models import ActionParams, PseudoBotWorld, ScriptedPolicy
from .core.session import Episode, EpisodeSession
from .profiles import HEALTHY_KEY, Profile, get_profile, list_profiles
from .report import run_experiment

__version__ = "0.1.0"

__all__ = [
    "HEALTHY_KEY",
    "ActionParams",
    "Episode",
    "EpisodeSession",
    "Profile",
    "PseudoBotWorld",
    "ScriptedPolicy",
    "__version__",
    "get_profile",
    "list_profiles",
    "run_experiment",
]
