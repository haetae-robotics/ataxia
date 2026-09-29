# Ataxia — Naming Review

Naming grammar used in this workspace: **a metaphorical word with an exact
functional correspondence** (family precedent: `derailment` = clinical term
*and* the harness verb). Review date: 2026-09-29.

## The word

**ataxia** — adopted.

1. *Clinical:* ataxia is the neurology term for incoordination — movements
   that are ordered in intent but disordered in execution (gait, reach,
   posture). Exactly the construct the harness induces: purposeful policies
   executing in a degraded, uncoordinated way.
2. *Etymology:* Greek ἀταξία = "disorder, lack of order" (a- "without" +
   taxis "order"). The umbrella reading is literally "disorder" — it covers
   perception, memory and action distortions, not only motor.
3. *Family:* sibling of `derailment` (chat-side harness). Same grammar:
   clinical term + the mechanical verb of what the tool does. Repo tagline:
   "derailment for embodied agents".

CLI: `ataxia` (subcommands mirror `derail`: `demo`, `tour`, `run`,
`profiles`).

## Candidate comparison

| Candidate | Fit | Rejected because |
|---|---|---|
| **ataxia** | clinical motor term; etymologically "disorder" (umbrella); short | — adopted |
| apraxia | "cannot perform purposeful action" — very exact for policy degradation | narrower than the umbrella (action-only; no perception/memory reading); harder to pronounce |
| catatonia | motor freezing is a real induced profile | names one profile, not the harness; charged register |
| perseveration | robotics already uses it for the exact bug class | profile name, not harness name; long |
| dyskinesia | involuntary movement | drug-induced movement connotation; narrow |
| stall | mechanical + motor-freezing double meaning | not clinical; collision-heavy word in engineering |
| unmoor | poetic (rejected once already in derailment review) | vaguer correspondence than ataxia |

## Conflict check (2026-09-29, live)

- **PyPI:** `ataxia` -> 404, free. (`apraxia` -> 404 free; `catatonia` -> 404
  free — all checked live.)
- **Software search:** no Python package or tool named Ataxia; hits are the
  medical literature and unrelated robotics toolboxes. Same acceptable noise
  profile as `derailment` (train news).
- **Family search:** `derailment` on PyPI is now TAKEN — by us (published
  2026-09-29).

## Verdict

Adopted: **ataxia** (package) / `ataxia` (CLI). Rejection reasons recorded
for auditability.

## Second review (2026-09-29) — before repo creation

Stress-testing the adoption with live checks (PyPI JSON API, GitHub repo
search) before the repository is created.

### Live collision check

- **PyPI:** `ataxia` still free (404 re-confirmed).
- **GitHub:** `xenith-studios/ataxia` — a Rust MUD engine, 72 stars, the
  only notable software occupant. Different domain (game engine vs.
  robotics/ML evaluation), modest traction; the rest are medical/research
  repos (ENIGMA-Ataxia, gait-analysis, detection GCNs) and inactive
  personal repos. Search noise profile: same class as `derailment` (train
  news) — acceptable. Note: the Frusciante side-project band "Ataxia"
  dominates generic web search; software-scoped searches are clean.
- `ictechgy/ataxia` itself: available.

### Fresh candidate sweep

| Candidate | Fit | Verdict |
|---|---|---|
| **ataxia** (incumbent) | clinical motor term + ἀταξία "disorder" umbrella; short | **kept** |
| apraxia | "cannot perform purposeful action" — exact for policy degradation; PyPI free (re-confirmed) | action-only, no perception/memory umbrella reading; ataxia stays ahead on fit + brevity |
| abulia | absence of initiative — maps helplessness exactly; PyPI free | single-profile scope; obscure |
| lurch | mechanical, evocative | PyPI **taken** (astronomy calibration); not clinical |
| runaway | real robotics safety term | common word, collision-heavy, not clinical |

Scope-growth test: the umbrella concern (ataxia = motor only) is answered
by the etymology — "sensory ataxia" is an established neurology
construction, so non-motor "X ataxia" readings generalize honestly.

### Verdict

Unchanged: **ataxia**. Green light for `ictechgy/ataxia`.
