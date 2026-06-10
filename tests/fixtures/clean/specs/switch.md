---
spec: switch
imports:
  - from: core
    use: [Requirement]
vocabulary:
  light: [on, off]
  bulb.lit: [yes, no]
entities:
  bulb: [bulb.lit]
---

# Switch

Total coverage over `light`, well-formed, no conflicts.

## SW-R1: on lights the bulb
when: light = on
then: bulb.lit = yes

## SW-R2: off darkens the bulb
when: light = off
then: bulb.lit = no
