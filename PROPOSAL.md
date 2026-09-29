# Ataxia — Project Proposal

**derailment for embodied agents: a harness for inducing and measuring
psychopathology-like behavioral distortions in robot policies — in
simulation first, always.**

Status: proposal (M0). Sibling project of
[derailment](https://github.com/ictechgy/derailment) (chat-side harness,
v0.1.0 on PyPI). Naming review: [NAMING.md](NAMING.md).

---

## 1. One-paragraph pitch

Ataxia takes the derailment thesis — *induce psychopathology-like
distortions by manipulating the same variables clinicians describe, then
measure against a healthy baseline* — into embodied agents. Today's VLA
stacks (RT-2 / OpenVLA / π0 class) decode actions as language-model tokens
over an observation buffer, which means the same four-layer induction
applies: instruction framing, observation-stream manipulation, action-token
sampling, and post-decoding action edits. Ataxia runs those inductions
**inside a simulator**, measures the degraded behavior episode-by-episode
against a healthy baseline, and prints the same kind of scored A/B report —
with a safety model that treats "a sick robot near people" as out of scope
by construction.

Positioning, mirroring derailment: **education > research > demo.**

## 2. Why a separate package (not a derailment module)

- **Different runtime.** Chat harnesses process message lists; embodied
  harnesses run episode loops (observe → decide → act → record). The loop
  owns timing, ground truth and reset semantics — a different core.
- **Different metrics.** Transcripts become episodes: task success,
  collisions, initiation latency, no-progress cycles. Not a text function.
- **Different safety model.** derailment's inductions are
  capability-reducing and harmless by construction. An embodied agent's
  degraded behavior is a physical hazard; the safety rules have to be
  architecture, not documentation.
- **Different optional deps.** Real simulators (MuJoCo, Isaac Lab) are
  heavy optional extras; the core must stay zero-dependency like
  derailment's.

## 3. Transfer thesis: the four layers survive

| derailment layer | embodied equivalent | Transfer |
|---|---|---|
| Persona (system message) | instruction/constitution layer of the VLA prompt | direct |
| Context-stream (memory decay, salience capture, premise pinning, intrusion) | **observation stream**: episodic scene buffer decay, old-observation re-salience, world-model belief pinning, phantom-object injection | direct concept, new surfaces |
| Sampling (temperature, logit bias) | action-token decoding temperature; cost/reward re-weighting in the planner | direct for token-decoded VLAs |
| Response (hedge/compulsion injection) | action editing: pause insertion, re-verification motion replays | direct, demonstration-grade as before |

## 4. Architecture

### 4.1 The episode loop (core)

```
Episode ──▶ observe ──▶ layers.on_observation ──▶ layers.on_instruction
   ▲                                                              │
   │                     policy.decide(obs, params) ◀── layers.on_params
   │                                                              │
   └── recorder ◀── layers.on_action ◀── policy.act ◀─────────────┘
```

- `Env` protocol: `reset()`, `observe()`, `step(action)` — the harness is
  environment-agnostic.
- `Policy` protocol: `decide(observations, params) -> action` — adapters
  for token-decoded VLA endpoints later; a deterministic offline policy
  first (see 4.2).
- Four hooks, same names and order as derailment's, embodied semantics:
  `on_observation`, `on_instruction`, `on_params`, `on_action`. Same dose
  accounting (`LayerEvent` per manipulation), same A/B experiment shape.

### 4.2 PseudoBot — the offline reference (the key decision)

derailment's power comes from `PseudoModel`: a deterministic offline
pseudo-LLM that makes demos, tests, calibration and CI run with no API key
and no network. Ataxia does the same with **PseudoBot**: a deterministic
toy gridworld (stdlib-only) with a scripted policy that has

- an attention field over grid cells (neglect / capture manipulable),
- an episodic observation buffer (decay / intrusion manipulable),
- a belief grid of object locations (pinning manipulable),
- a cost-weighted action choice with a decoding-temperature analog
  (elaboration / wavering).

Every profile must move its metrics on PseudoBot — the same
direction-of-effect rule as derailment, calibrated the same way.

### 4.3 Real simulators are extras, never the core

Adapters for MuJoCo / Isaac Lab / Habitat ship as optional extras
(`ataxia[mujoco]`). The core, the profiles, the metrics and the CI never
require them.

## 5. Profile slate

MVP (three, with the strongest literature grounding):

| Profile | Construct | Mechanism (layer) | Grounding |
|---|---|---|---|
| `learned_helplessness` | initiation collapse after degraded outcomes | reward/cost signal degradation across episodes (params) | real RL phenomenon (Seligman lineage) |
| `perseveration` | repetition of completed subtasks | action-loop re-injection (action) | already a robotics bug-class name |
| `sensory_neglect` | one region of the sensor field systematically ignored | spatial attention mask on observations (observation) | hemispatial neglect (neuropsychology) |

v0.2 (three more, established analogs):

| Profile | Construct | Mechanism |
|---|---|---|
| `phantom_object` | acting toward non-existent objects | phantom-entry injection into the observation buffer |
| `world_belief_pin` | false scene belief maintained against contradicting sensors | world-model belief pinning (premise-pin analog) |
| `dock_fixation` | compulsive return-to-dock behavior | escalating dock-fragment intrusions (craving analog) |

Excluded up front, same line as derailment's ETHICS: manipulation/deception
tooling of any kind, adversarial *perception attack* generators (we edit
internal state; we do not craft sensor-level attacks), and anything run
unattended on hardware near people.

## 6. Instruments (episode-level, nine)

Initiation collapse · no-progress rate · failed-collect rate (the
perseveration signature: re-collecting a just-completed subtask) ·
collision count · action repetition entropy · region detection delta ·
task success · time-to-complete · belief persistence rate.

Same reporting rules as derailment: thresholds normed against the offline
reference (PseudoBot), healthy baseline at level 0, **delta vs. baseline is
the primary output**, disclaimer on every report.

## 7. Safety model & ethics delta

- **Sim-only default.** PseudoBot is the default environment; real
  simulators are opt-in extras. Hardware is out of scope for v1 entirely.
- **Hardware rules (for later versions, stated now):** supervised,
  cordoned, e-stop reachable, never near uninvolved people, never
  unattended. These are prerequisites, not suggestions.
- **Harm direction:** derailment's inductions are capability-reducing on a
  text channel; ataxia's are capability-reducing on a *body*. The risk of
  degraded behavior is borne by the physical environment, so the harness
  must make unsupervised hardware induction technically awkward (explicit
  flags, loud warnings, no defaults).
- **No welfare claims**, same neutral stance as derailment: induced
  behavioral distortions are not evidence about machine experience in
  either direction.
- **Not a fault-injection-for-cybersecurity tool** and not adversarial
  attack tooling: manipulations edit internal state; sensor-level attack
  generation is declined.

## 8. Milestones

| Milestone | Scope | Done when |
|---|---|---|
| M0 — proposal | this document + naming review | reviewed, name checked |
| M1 — core | episode loop, PseudoBot, healthy baseline, MVP 3 profiles, 8 metrics, direction tests, charts | `ataxia demo` runs offline; direction tests green |
| M2 — completeness | v0.2 profiles, `tour`, comorbidity (profiles chain), docs (README EN/KO, ETHICS, ARCHITECTURE), CI | mirrors derailment's release bar |
| M3 — adapters | MuJoCo or Isaac Lab adapter as extra; one real-sim example | optional; never blocks core CI |
| M4 — release | PyPI trusted publishing, repo live | `pip install ataxia` |

## 9. Non-goals

- Unattended or near-human hardware induction (v1: not at all).
- Cybersecurity fault injection / adversarial sensor-attack generation.
- Claims about robot consciousness or suffering.
- Diagnosing robots, or framing induced behavior as actual illness — the
  disclaimer carries over: *emulation, not diagnosis.*

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| VLA stack churn (decoding schemes change) | env/policy adapters behind protocols; PseudoBot carries all tests |
| Safety framing misread as "hacking robots" | ETHICS-first, sim-only default, loud warnings, no hardware defaults |
| Scope creep toward full robotics testing | non-goals section is binding; episode metrics stay behavioral |
| Calibration drift as profiles grow | derailment's rule carries over: no direction test, no merge |

## 11. Relation to derailment

Shared: thesis, four-layer induction grammar, A/B-vs-baseline methodology,
direction-test rule, zero-dependency core + offline reference, ethics
stance and disclaimer culture. Separate: runtime (episodes vs turns),
metrics, safety model, dependency surface. Cross-links in both READMEs.
