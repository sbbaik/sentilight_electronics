**T01_policies_keff.** Nested lighting policies and their effective action spaces. Lattice = (colours+1)(emotions+1)×intensities; reachable = distinct actuator tuples produced by running the policy over the lattice.

| policy | colours | emotions | intensities | lattice size | reachable tuples K_eff | collisions | hue snaps fired | coarse-bin cells occupied | tuples with a strict-box neighbour | note |
|---|---|---|---|---|---|---|---|---|---|---|
| K48 | 3 | 3 | 3 | 48 | 48 | 0 | 0 | 16 | 46 | nested extension |
| K240 | 7 | 5 | 5 | 240 | 240 | 0 | 0 | 39 | 238 | production policy |
| K480 | 11 | 7 | 5 | 480 | 480 | 0 | 0 | 44 | 478 | nested extension |
| K960 | 15 | 11 | 5 | 960 | 960 | 0 | 0 | 54 | 959 | nested extension |

Source: `backend/reports/keff_policies/keff_policy_check.json; keff_policy_diagnostics.json`
