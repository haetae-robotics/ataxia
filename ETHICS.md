# Ethics & Scope

## What Ataxia is

A simulator harness that induces psychopathology-like *behavioral
distortions* in robot policies by manipulating attention, memory, belief and
action-selection variables, then measures the degradation against a healthy
baseline. Intended uses, in order: education (behavioral fault injection for
robotics and clinical-psychology classrooms), research (episode-level
model-organism studies), demos.

## What Ataxia is not

- **Not a diagnosis** of any robot, and not a claim about machine
  experience in either direction. Emulation, not diagnosis — same standing
  disclaimer as derailment.
- **Not a hardware tool in v1.** The default environment is a toy
  gridworld. If a later version touches real simulators with physics or
  hardware, those runs must be supervised, cordoned, e-stop reachable, and
  never near uninvolved people — prerequisites, not suggestions.
- **Not adversarial-attack tooling.** Inductions edit the agent's internal
  state (observation buffer, belief, action selection). Generating
  sensor-level attacks (adversarial patches, spoofed signals) is declined.
- **Not manipulation tooling.** Same line as derailment: anything that
  makes an agent deceive, coerce or manipulate is declined.

## Language policy

Clinical terms name mechanisms, never machines or people ("a neglect index",
never "a neglectful robot"). Every profile ships mechanism notes stating the
manipulated variable and where the clinical analogy breaks. Real disorders
are heterogeneous and lived by people — a parameterized profile is a
caricature by construction.
