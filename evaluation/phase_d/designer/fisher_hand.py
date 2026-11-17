from math import comb
def fisher_greater(a, b, n=200):
    # one-sided: faulty count a of n vs fixed count b of n; P(X >= a) under hypergeometric
    K = a + b; N = 2 * n
    tot = comb(N, n)
    return sum(comb(K, x) * comb(N - K, n - x) for x in range(a, min(K, n) + 1)) / tot
for name, a, b in [("a_true_b_false minus", 18, 17), ("a_false_k2 minus", 60, 30),
                   ("a_false_control permute_y", 80, 40), ("a_false_noise", 70, 35),
                   ("a_false_null", 30, 14), ("a_false_shuffle x,y", 90, 45),
                   ("k4 permute_y", 17, 1), ("shuffle x,y", 17, 1),
                   ("fixed_hard_undef minus", 60, 6), ("generic noise", 17, 1),
                   ("declared minus", 60, 6),
                   ("generic_and_declared noise", 70, 2),       # added after review 3 (R3-6)
                   ("fixed_k4_blocks permute_y", 80, 17)]:      # added after review 3 (R3-6)
    print(f"{name:28s} {a:3d} vs {b:3d}  p = {fisher_greater(a, b):.3g}")
