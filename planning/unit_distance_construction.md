# `unit_distance_points(n)` (experimental)

Generate a set of n points in the plane with many pairs at distance exactly 1. This is a demonstration of the 2026 disproof, not a practical improvement.

## Old implementation

**Erdős (1946) grid:**
1. Take the √n × √n integer lattice.
2. Choose m ≤ n with the largest number of representations as a sum of two squares (a product of many primes ≡ 1 mod 4).
3. Scale by 1/√m.

That gives n^(1 + c/log log n) unit distances. Generation costs O(n) and counting pairs costs O(n · r₂(m)), where r₂(m) is the number of representations of m as a sum of two squares. Exact rational coordinates, easy to verify.

The upper bound is O(n^(4/3)) (Spencer–Szemerédi–Trotter). Erdős conjectured that n^(1+o(1)) was the truth.

## What changes it

**OpenAI model (May 20 2026), human write-up arXiv 2605.20695** (Alon, Bloom, Gowers, Litt, Sawin, Shankar, Tsimerman, Wang, Wood). `peer-verified`.

Theorem 1.1: there are point sets P_i with at least |P_i|^(1+ε) unit distances.

The construction:
1. **Tower of fields:** r = 510510 = 2·3·5·7·11·13·17. Golod–Shafarevich gives an infinite class field tower of totally real fields L_j, unramified outside {3,…,17}, with 101 splitting completely. The base field is L = ℚ(√5, √13, √17, √21, √33). Set K_j = L_j(i), a CM field.
2. **Unit-modulus elements (Lemma 2.2):** a pigeonhole argument on the class group gives many u in Q^(−2) with |u| = 1, with denominators bounded by D = 101^(2k), where k = ⌈18r³/π⌉ − 1.
3. **Geometry of numbers (Lemma 2.1):**
   - Embed Λ = 101^(−2k)·O_K into ℂ^f.
   - Because K is CM, |u| = 1 in one embedding means |u| = 1 in all of them.
   - Take a window (a + Λ) ∩ B_R and project to one coordinate, which is injective, to get a planar set P.
   - The differences that are unit-modulus elements are unit distances.
4. **Exponent:** ε ≈ 6.24·10⁻³⁸ with the paper's explicit choices. Sawin's refinement, described as forthcoming and using primes above a single rational prime, reportedly reaches ε = 0.014. That figure comes from OpenAI's blog, and we haven't seen the refinement itself.

## New implementation

**The real problem:** the fields L_j exist by Golod–Shafarevich, but they aren't given explicitly. Computing even the first few layers of a class field tower of degree f over ℚ is a hard computation (PARI `bnrclassfield`), and the gain only appears as f → ∞. So the construction can't be carried out to beat the grid at any size we could compute.

Where it overtakes the grid: the grid exponent is 1 + c/log log n with c on the order of 0.3 to 0.7. It falls to Sawin's 1.014 only once log log n exceeds about 25 to 50, which is n > e^(e²⁵) at the least. That is not a practical regime.

What we can build:
1. **`erdos_grid(n)`:** the classical construction, exact, with a pair counter. This is the practical function.
2. **`tower_construction(K, k, R)`:** given an explicit CM field K, given as a PARI number field, plus the parameters, produce P and count unit distances exactly, using algebraic coordinates through PARI (`cypari2`). This demonstrates the mechanism on small fields, where it loses to the grid, and computes the actual exponent achieved.
3. **`unit_distance_count(P)`:** exact counting for algebraic point sets, by hashing differences through an exact norm check.

**Complexity:** for a degree-f field, |P| ≤ (9R²/δ²)^f, so the sets grow exponentially in f. Class group computations for K cost subexponential in the discriminant and assume GRH for Dedekind zeta functions, which this year's results do not cover. PARI's `bnfcertify` can remove that assumption at high cost.

## Open questions

- Is anything usable at small f? It could serve as test data for unit-distance-graph algorithms, such as chromatic number experiments (Hadwiger–Nelson), even when it is not extremal.
- Find Sawin's refinement, and the Sept 23 2026 OpenAI preprint "A power saving for planar unit distances".
- Recommendation: build only `erdos_grid` and `unit_distance_count` in v1. Leave the tower construction until someone needs it.
