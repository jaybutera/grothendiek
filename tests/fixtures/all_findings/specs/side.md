---
spec: side
defines:
  concepts:
    - Thing
vocabulary:
  widget.color: [red, blue]
---

# Side spec

Imports nothing, is imported by nothing -> orphan_spec. Also defines Thing
without importing it from core -> duplicate_definition with main.

## SIDE-R1: red widgets stay red
when: widget.color = red
then: widget.color = red
