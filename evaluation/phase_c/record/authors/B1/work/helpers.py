"""Scratch: the quadrature upper-tail of Student's t used inside the criterion bodies; text copied into bodies by build_bodies.py."""
SF = '''    def _sf(t, df):
        # upper-tail probability of Student's t: integral of cos(x)**(df-1) over [arctan(t/sqrt(df)), pi/2], trapezoid rule
        t = np.asarray(t, dtype=float)
        df = np.broadcast_to(np.asarray(df, dtype=float), t.shape)
        u = np.linspace(0.0, 1.0, 1001)

        def tail(lo):
            x = lo[..., None] + (np.pi / 2.0 - lo[..., None]) * u
            f = np.cos(x) ** (df[..., None] - 1.0)
            return (f.sum(-1) - 0.5 * (f[..., 0] + f[..., -1])) * (np.pi / 2.0 - lo) / (len(u) - 1)

        ang = np.arctan(np.abs(t) / np.sqrt(df))
        upper = tail(ang) / (2.0 * tail(np.zeros_like(ang)))
        return np.where(t >= 0.0, upper, 1.0 - upper)
'''
