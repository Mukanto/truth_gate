H_LG = '''
    def _lg(z):
        c = (0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
             -176.61502916214059, 12.507343278686905, -0.13857109526572012,
             9.9843695780195716e-6, 1.5056327351493116e-7)
        z = z - 1.0
        x = c[0]
        for i in range(1, 9):
            x += c[i] / (z + i)
        t = z + 7.5
        return 0.5 * np.log(2.0 * np.pi) + (z + 0.5) * np.log(t) - t + np.log(x)

    def _cf(a, b, x):
        tiny = 1e-300
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c = 1.0
        dd = 1.0 - qab * x / qap
        dd = 1.0 / (dd if abs(dd) > tiny else tiny)
        h = dd
        for m in range(1, 400):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= dd * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            de = dd * c
            h *= de
            if abs(de - 1.0) < 1e-13:
                break
        return h

    def _ib(x, a, b):
        # regularized incomplete beta function I_x(a, b)
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        bt = np.exp(_lg(a + b) - _lg(a) - _lg(b) + a * np.log(x) + b * np.log(1.0 - x))
        if x < (a + 1.0) / (a + b + 2.0):
            return float(bt * _cf(a, b, x) / a)
        return float(1.0 - bt * _cf(b, a, 1.0 - x) / b)

    def _tsf(t, df):
        # one-sided upper-tail probability of Student's t
        t = float(t)
        if t == 0.0:
            return 0.5
        p = 0.5 * _ib(df / (df + t * t), 0.5 * df, 0.5)
        return p if t > 0 else 1.0 - p
'''
H_TQ = '''
    def _tq(alpha, df):
        # t value whose upper-tail probability is alpha
        lo, hi = 0.0, 1e3
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if _tsf(mid, df) > alpha:
                lo = mid
            else:
                hi = mid
        return hi
'''
H_CORR = '''
    def _corr(a, y):
        # Pearson correlation of every column of a with y
        a = a - a.mean(axis=0)
        y = y - y.mean()
        den = np.sqrt((a ** 2).sum(axis=0) * (y ** 2).sum())
        return np.where(den > 0, (a * y[:, None]).sum(axis=0) / np.where(den > 0, den, 1.0), 0.0)
'''
H_WELCH = '''
    def _welch(x, y):
        # Welch t statistic and degrees of freedom along axis 0
        nx, ny = x.shape[0], y.shape[0]
        vx = x.var(axis=0, ddof=1) / nx
        vy = y.var(axis=0, ddof=1) / ny
        se2 = vx + vy
        ok = se2 > 0
        t = np.where(ok, (x.mean(axis=0) - y.mean(axis=0)) / np.sqrt(np.where(ok, se2, 1.0)), 0.0)
        df = np.where(ok, se2 ** 2 / (vx ** 2 / (nx - 1) + vy ** 2 / (ny - 1) + 1e-300), 1.0)
        return t, df
'''
