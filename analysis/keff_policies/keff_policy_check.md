# K_eff policy uniqueness check

- Config: `config/keff_policies.json`
- Catalog drift vs training_data.py: none
- K240 reproduces production resolve_case_output: True

| Policy | C | E | I | Lattice | Reachable | Target | Collisions | Hue snaps | Max ΔH | Min pair dist | Pairs inside strict box |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| K48 | 3 | 3 | 3 | 48 | 48 | 48 | 0 | 0 | 7° | 0.0182 | 108 / 1128 |
| A2K192 | 15 | 11 | 1 | 192 | 192 | 192 | 0 | 0 | 4° | 0.0253 | 478 / 18336 |
| K240 | 7 | 5 | 5 | 240 | 240 | 240 | 0 | 0 | 7° | 0.008 | 1115 / 28680 |
| K480 | 11 | 7 | 5 | 480 | 480 | 480 | 0 | 0 | 7° | 0.008 | 3021 / 114960 |
| K960 | 15 | 11 | 5 | 960 | 960 | 960 | 0 | 0 | 7° | 0.008 | 10932 / 460320 |

## Nesting
- K48 ⊂ K240: True
- K240 ⊂ K480: True
- K480 ⊂ K960: True

## Closest pair per policy
- K48: ('yellow', 'anger', 'strong') (57, 100, 100, 100, 210)  vs  ('yellow', 'happiness', 'strong') (59, 100, 100, 100, 205)
- A2K192: ('apricot', 'surprise', 'neutral') (36, 50, 100, 100, 230)  vs  ('apricot', 'happiness', 'neutral') (37, 52, 100, 100, 235)
- K240: ('yellow', 'anger', 'bright') (56, 100, 100, 100, 212)  vs  ('yellow', 'anger', 'strong') (57, 100, 100, 100, 210)
- K480: ('yellow', 'anger', 'bright') (56, 100, 100, 100, 212)  vs  ('yellow', 'anger', 'strong') (57, 100, 100, 100, 210)
- K960: ('yellow', 'anger', 'bright') (56, 100, 100, 100, 212)  vs  ('yellow', 'anger', 'strong') (57, 100, 100, 100, 210)

**ALL OK: True**
