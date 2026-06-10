---
spec: main
imports:
  - from: core
    use: [Requirement, Decision]
defines:
  concepts:
    - Thing
vocabulary:
  user.state: [active, suspended, closed]
  charge: [yes, no]
  event: [renewal, retry]
entities:
  user: [user.state]
---

# Main behavior spec

Provokes: conflict (R1 vs R2), gap (paused/other states uncovered),
dead_rule (R5 under invariant), unknown_term (R3), stale_decision_ref (R1
links a superseded decision), nonconforming_card (R4), dead_rule invariant,
duplicate_definition (Thing also defined in side.md), entities derived.

## MAIN-R1: suspended users not charged
when: user.state = suspended
then: charge = no
because: [[D1]]

## MAIN-R2: retries always charge
when: event = retry
then: charge = yes

## MAIN-R3: unknown term used
when: user.state = frozen
then: charge = no

## MAIN-R4: prose effect, nonconforming
when: user.state = active
then: the user is greeted warmly

## MAIN-R5: closed users get a final notice
when: user.state = closed
then: charge = no

## MAIN-I1 (invariant): closed users cannot be charged
invariant: user.state = closed — closed accounts are settled

## D1 (decision, 2026-01-01): old rationale
status: superseded by [[D2]]
The original reason.

## D2 (decision, 2026-02-01): new rationale
supersedes: D1
The replacement.
