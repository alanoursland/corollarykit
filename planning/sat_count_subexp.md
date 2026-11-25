# `count_sat_subexp(cnf)` (experimental)

Count the satisfying assignments of a k-CNF formula exactly, in subexponential time and polynomial space. This is a **reference implementation**: it will never beat existing solvers on any formula that can actually be stored.

## Old implementation

n = number of variables, m = number of clauses.

| Problem | Best known | Notes |
|---|---|---|
| 3-SAT (decision), randomized | O(1.307ⁿ) | PPSZ, Hansen–Kaplan–Zamir–Zwick 2019 |
| 3-SAT (decision), deterministic | about O(1.33ⁿ) | derandomized local search; check the current record |
| #3-SAT (counting) | about O(1.5ⁿ) to O(1.65ⁿ) | branching algorithms; check the current record |
| Practical | CDCL solvers; #SAT via d-DNNF compilation (d4, sharpSAT-TD) | exponential worst case, excellent on structured inputs |

ETH conjectured that 3-SAT needs 2^(δn) time for some δ > 0. Hundreds of fine-grained lower bounds are conditional on it.

## What changes it

There are **two separate claims** (Oct 2026), both `claimed`:
- **OpenAI**, "The Exponential Time Hypothesis is False", in `openai/math/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/`. A deterministic algorithm exactly counts the satisfying assignments of fixed-width CNF formulas in subexponential time and polynomial space. The bound, as others restate it, is (n+m)^O(1) · 2^(n/(log n)^(1/2+o(1))). Kintali's abstract summarizes the technique as sparsification, bounded occurrences, spectral replacement, and rational interpolation.
- **Anthropic / Claude**: a separate proof (hexagonmath.org 2610.00577, not yet read). It contracts a complete-graph tensor network using "signed sums of networks". As Majdoddin restates it, the bound is 2^(O(k·m/√log m)) in clauses and 2^(O(k²·n·log log n/√log n)) in variables.

Impagliazzo, Paturi and Williams have formed a working group to review the OpenAI claim. They say their involvement "should not be taken as certification."

## Crossover (correction)

Earlier we said the algorithm only wins above 2⁶⁰⁰⁰ variables. That was wrong. In Majdoddin's analysis (arXiv 2610.41622), 2⁶⁰⁰⁰ is a lower bound for an entire class of approaches. The estimated crossovers against brute force are much larger:

| Algorithm | Crossover (Majdoddin's estimates) |
|---|---|
| Anthropic, clause bound, density 1 | about 2⁴²⁰ clauses after his improvements (2³³⁸⁵⁸ as written) |
| Anthropic, general 3-SAT | about 2^(8.6·10⁹) variables (2^(2.2·10¹²) as written) |
| OpenAI | about 2^(4.4·10¹⁰) clauses at density 1; at least 2^(1.09·10¹⁰) variables by its main-text route |

These are crossovers against **brute force**, not against PPSZ or CDCL. Against modern solvers they are later still.

## New implementation

1. Implement the Anthropic tensor-network method first. Majdoddin's paper gives enough detail to follow, and its clause-based crossover is the least absurd.
2. Implement the OpenAI pipeline in stages (sparsify → bounded occurrence → spectral replacement → rational interpolation) once its PDF has been read.
3. Instrument both to report the predicted and measured operation counts. The useful output for researchers is a cost model, not satisfying assignments.
4. Validate correctness by comparing counts against brute force and sharpSAT-TD on small formulas. With constants this large, "small" may mean the algorithm takes its fallback branches. Document which code paths the tests actually reach.

**Complexity:** 2^(n/(log n)^(1/2+o(1))) time and poly(n+m) space, as claimed. In practice, always slower than brute force for any n below the crossovers above.

## Open questions

- Read both primary papers before writing any code.
- Does it make sense to ship this as a library function at all? It might be better as a separate research repository that uses corollarykit's assumption registry.
