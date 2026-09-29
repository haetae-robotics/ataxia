# Changelog

All notable changes to this project are documented here.

## [0.2.0] - 2026-09-29

### Added

- Three v0.2 profiles: `phantom_object` (empty cells injected as targets —
  travel-overhead signature), `world_belief_pin` (a decoy cell pinned as
  target against sensor evidence — belief-persistence signature),
  `dock_fixation` (escalating return-to-dock steering — positional craving
  analog). Six profiles + healthy baseline total.
- Policy-level pinned-belief support with `belief.persisted` /
  `belief.contradiction` event logging; the belief-persistence instrument
  now measures kept-vs-corrected beliefs.
- Two new instruments: travel overhead, dock escalation (eleven total).
- Combined chains: `--profile learned_helplessness,perseveration`
  concatenates layer chains and unions scales (interactions emergent).

## [0.1.0] - 2026-09-29

### Added

- M1 core: PseudoBot gridworld (deterministic, stdlib-only), scripted
  belief-grid policy, episode loop with four induction hooks, dose
  accounting.
- Three profiles: `learned_helplessness`, `perseveration`,
  `sensory_neglect`, plus the healthy baseline.
- Nine episode-level instruments, three symptom scales, comparison
  reports ("clinical charts") with the emulation-not-diagnosis
  disclaimer.
- CLI: `ataxia` (interactive menu), `ataxia demo`, `ataxia tour`,
  `ataxia profiles`.
