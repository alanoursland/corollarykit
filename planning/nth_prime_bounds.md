# `nth_prime_bounds(n)`

Return `lo, hi` with `lo ≤ p_n ≤ hi`, where `p_n` is the nth prime. A companion `nth_prime(n)` computes the exact value using the bounds to limit the work.

## Old implementation

**Bounds:** Rosser and Dusart give, for example (Dusart 2010),

    n(ln n + ln ln n − 1 + (ln ln n − 2.1)/ln n) ≤ p_n             for n ≥ 2
    p_n ≤ n(ln n + ln ln n − 1 + (ln ln n − 2)/ln n)               for n ≥ 688 383

The width is about 0.1·n/ln n, computed in O(1) operations.

**Exact `p_n`:**
1. Estimate x ≈ li⁻¹(n).
2. Compute π(x) exactly with LMO, at O(x^(2/3)/log² x).
3. Sieve between x and the true p_n.

The sieve window is unknown in advance. Implementations either guess and retry, or allocate for the Dusart width, which costs O(n/ln n) memory in the worst case.

## What changes it

**RH** (Alpöge–Claude, `lean-compiled`), through Schoenfeld's bound (see `prime_count_interval.md`). Inverting |π(x) − li(x)| < √x·ln x/(8π) gives a window for p_n of width about **√n · ln^(5/2) n**, a little more than √(p_n)·ln p_n.

## New implementation

1. Get the unconditional Dusart interval [L, U] as the starting bracket.
2. Using Arb interval arithmetic, find the smallest x with `li(x) − √x·ln x/(8π) ≥ n` (giving `hi`) and the largest x with `li(x) + √x·ln x/(8π) < n` (giving `lo`). Do this by bisection or interval Newton. Each step evaluates li once, at O(polylog n), over O(log n) steps.
3. Return the result object with its bases (RH via Schoenfeld; Dusart as the fallback).

**Exact `nth_prime(n)`:**
1. Compute `lo, hi` as above.
2. Find c = π(lo) exactly, using LMO (or `primesieve` when available).
3. Run a segmented sieve on [lo, hi] and take the (n − c)th prime in it.

The memory is **O(√n · polylog n), known before the sieve starts**, with no retries.

**Complexity:** the bounds cost O(polylog n), unchanged. The exact computation is still dominated by π(lo) at O(n^(2/3)/log² n), so the asymptotic cost of exact p_n does not change. What improves is the certified window (about √n·polylog n instead of about n/ln n) and a memory size you can guarantee up front.

## Testing

- Compare against known p_n (OEIS A006988, the 10^k-th primes) for k ≤ 24.
- Run random n below 10⁸ against an exact sieve.
- Check that lo ≤ hi and that the window always contains p_n.

## Open questions

- Is it worth building our own LMO in Python, or should exact π come only from optional native dependencies (`primesieve`, `primecount`)? Suggestion: use native `primecount` when installed, and have the pure-Python fallback stop around 10¹².
