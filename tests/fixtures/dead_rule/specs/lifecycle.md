---
spec: lifecycle
imports:
  - from: core
    use: [Requirement]
vocabulary:
  sub.state: [active, paused, closed]
  action: [notify, archive]
entities:
  sub: [sub.state]
---

# Lifecycle

The invariant declares closed subscriptions impossible to act on; the rule
that fires only on closed subscriptions is therefore dead.

## LIFE-I1 (invariant): closed subscriptions are terminal
invariant: sub.state = closed — no further state exists past closed

## LIFE-R1: closed subscriptions are archived
when: sub.state = closed
then: action = archive

## LIFE-R2: active subscriptions are notified
when: sub.state = active
then: action = notify
