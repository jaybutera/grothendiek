---
spec: billing
imports:
  - from: core
    use: [Requirement, Decision]
vocabulary:
  user.state: [active, suspended, closed]
  event: [renewal_due, payment_retry]
  charge: [yes, no]
entities:
  user: [user.state]
---

# Billing and dunning

A suspended user with payment retries: R1 says do not charge, R9 says retry
charges. Overlapping guards, clashing `charge` effect, no overrides: link —
a conflict with a witness.

## BILL-R1: suspended users are never charged
when: user.state = suspended
then: charge = no
because: [[D9]]

## BILL-R9: payment retries do charge
when: event = payment_retry
then: charge = yes
because: [[D9]]

## D9 (decision, 2026-01-01): conflict is write-write on a shared variable
Overlapping guards with different values for the same effect variable conflict
unless an overrides: link resolves them.
