# Testing: `erdos_grid(n)`, `unit_distance_count(points)`

Plan: [../unit_distance_construction.md](../unit_distance_construction.md). This plan covers the grid and the counter. The tower construction is research and is left out until it has an explicit field and an output-size contract.

## 1. Reference values

- Small configurations with known unit-distance counts: the unit triangle (3), the unit square (4), the Moser spindle (7 points, 11 unit distances), and the hexagonal lattice patch.
- Published maximum unit-distance counts for small n (source to be located): the grid's count must never exceed the known maximum.

## 2. Oracle comparison

- `unit_distance_count` against a naive O(n²) exact pair check, on random integer point sets with random scale m.

## 3. Properties

- **Exactness:**
  - Points are stored as integer lattice coordinates plus a common squared scale m.
  - A pair counts exactly when dx² + dy² = m.
  - No floating point is used anywhere. A lint test forbids `float` in the module.
- `erdos_grid(n)` returns exactly n distinct points. The output-size contract: the largest grid with at most n points, padded deterministically, or exactly n by construction (to be decided in the spec).
- The count grows faster than linearly in n for the grid: fit the exponent for n from 10² to 10⁶ and compare with 1 + c/log log n.
- Invariance under translation, and under the lattice symmetries (rotation by 90°, reflection).

## 4. Edge cases

- n ∈ {0, 1, 2}. m with no representation as a sum of two squares (count 0). Duplicate points in the counter's input (rejected or deduplicated, as specified).

## 5. Bases and policy

- The grid is classical (Erdős 1946). Results report that basis. No 2026 basis is involved.

## 6. Certificates

- The list of unit pairs (i, j). The verifier checks each pair's squared distance and, for small n, that the list is complete.

## 7. Failure paths

- Non-integer coordinates and non-positive m are rejected.

## 8. Performance

- Counting time for 10⁶ points. Pair enumeration should run in O(n · r₂(m)) using a hash of the points.
