p='reference.py'
s=open(p).read()
old="PAT = np.zeros(P)\nPAT[0:24:3] = np.array([1.0, 1.0, -1.0, 1.0, -1.0, 1.0, 1.0, -1.0])\n"
new="PAT = np.zeros(P) + np.isin(np.arange(P), np.arange(0, 24, 3)) * np.tile(np.array([1.0, 1.0, -1.0, 1.0, -1.0, 1.0, 1.0, -1.0, 1.0]), 3)[:P]\n"
assert old in s
open(p,'w').write(s.replace(old,new))
