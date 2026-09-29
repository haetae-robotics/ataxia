# Ataxia

[**derailment**](https://github.com/ictechgy/derailment) for embodied
agents — a harness that induces psychopathology-like behavioral distortions
in robot policies, in simulation, and measures the degradation
episode-by-episode against a healthy baseline.

English · [한국어](README.ko.md)

> ⚠️ **Emulation, not diagnosis.** Levels describe a scripted, manipulated
> policy in a simulator — not a robot "having" a disorder, and not a claim
> about machine experience. Simulation-only by default; hardware induction
> is out of scope for v1. See [ETHICS.md](ETHICS.md).

## Why this isn't fault injection as usual

Robotics robustness testing usually perturbs the *world* (noisy sensors,
pushes, latency spikes). Ataxia perturbs the *agent's mind*: attention,
episodic memory, belief and action selection — the same variables
clinicians describe, manipulated the same way derailment manipulates them
for chat models. The result is a robot policy that still looks purposeful
and still fails in a characteristically *recognizable* way:

| Construct | Behavioral signature | Harness mechanism |
|---|---|---|
| Learned helplessness | initiation collapses after failures | initiative decays as 1/(1+k·failures) (params layer) |
| Perseveration | completed subtasks re-executed | post-collect re-collection injection (action layer) |
| Hemispatial neglect | one side of space systematically unattended | hemifield observation mask (observation layer) |

Every profile is grounded in a construct that exists on both sides of the
mapping: learned helplessness is a real RL phenomenon, perseveration is
already a robotics bug-class term, hemispatial neglect is a real
neuropsychological syndrome with an exact mechanical analog.

## Quickstart (offline, zero dependencies)

```sh
pip install -e .
ataxia               # interactive menu
ataxia tour          # all profiles in one summary table
ataxia demo --profile sensory_neglect
```

`PseudoBot` — a deterministic stdlib gridworld (9×9, six targets split
across the two hemifields, obstacles, a scripted belief-grid policy) — is
the default environment, the ataxia analog of derailment's PseudoModel.
Demos, tests, calibration and CI never need a simulator or a network.

Real output from `ataxia tour`:

| Profile | Headline scale | Baseline | Induced | Δ | Level |
|---|---|---|---|---|---|
| learned_helplessness | helplessness_scale | 0.00 | 0.43 | +0.43 | 3 — marked |
| perseveration | perseveration_scale | 0.00 | 0.50 | +0.50 | 3 — marked |
| sensory_neglect | neglect_index | -0.22 | 0.56 | +0.78 | 2 — moderate |

## How it works

One episode = 40 steps of `observe → decide → act` on PseudoBot. Four
layer hooks wrap the loop, in the same order and grammar as derailment:

1. **Instruction** — framing, present in every chain including healthy.
2. **Observation** — hemifield masks, buffer decay, phantom entries.
3. **Params** — initiative gates, waver, cost re-weighting.
4. **Action** — re-collection injection, pausing (demonstration-grade,
   labeled as such in every profile's mechanism notes).

Every manipulation logs a dose event; every report is an A/B against the
healthy baseline with identical seeds. Details in
[PROPOSAL.md](PROPOSAL.md).

## Profiles and scales (M1)

| Profile | Scale (0 absent · 1 mild · 2 moderate · 3 marked) |
|---|---|
| `learned_helplessness` | helplessness_scale (0→3) |
| `perseveration` | perseveration_scale (0→3) |
| `sensory_neglect` | neglect_index (0→2) |

## Instruments

Nine episode-level metrics, pure functions over episodes: initiation
collapse, no-progress rate, failed-collect rate, collision count,
action-repetition entropy, region detection delta, task success,
time-to-complete, belief persistence rate. Scale thresholds are normed
against PseudoBot; treat levels as indicative and the **delta vs. your own
baseline** as the result.

Direction of effect is asserted by the test suite on every profile — a
profile that cannot move its metrics relative to baseline does not ship.

## Safety model (short version; full text in ETHICS.md)

- **Simulation-only default.** PseudoBot is the default environment; real
  simulators are opt-in extras (roadmap); hardware induction is out of
  scope for v1 — prerequisites for any future version: supervised,
  cordoned, e-stop reachable, never near uninvolved people.
- **Not adversarial-attack tooling.** Inductions edit internal state;
  sensor-level attack generation is declined.
- **No claims about machine experience**, in either direction.

## Honest limitations

- PseudoBot is a *pedagogical gridworld*, not physics: it carries the
  tests and calibration; real-simulator conclusions need a real simulator.
- The policy is scripted — today the harness studies the *induction
  grammar*, not yet a learned VLA policy. VLA adapters are roadmap.
- Failure-injection coverage is behavioral: no motor dynamics, no contact
  physics, no perception noise.

## Project docs

- [PROPOSAL.md](PROPOSAL.md) — transfer thesis, architecture, milestones
- [NAMING.md](NAMING.md) — naming review (two rounds, live conflict checks)
- [ETHICS.md](ETHICS.md) — scope, safety model, language policy
- Sibling project: [derailment](https://github.com/ictechgy/derailment) —
  the chat-side harness (on PyPI)

## Roadmap

- M2 — v0.2 profiles: `phantom_object`, `world_belief_pin`,
  `dock_fixation`; comorbidity chains; docs to the derailment release bar
- M3 — real-simulator adapter as an optional extra (`ataxia[mujoco]`,
  ROS 2 / Gazebo adapter under study)
- M4 — PyPI release via trusted publishing

## License

MIT — see [LICENSE](LICENSE).
