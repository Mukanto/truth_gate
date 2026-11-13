import numpy as np, textwrap
from helpers import *
from scipy import stats
src = "def host():\n    pass\n" 
code = "import numpy as np\ndef mk():\n" + H_LG + H_TQ + "\n    return _tsf, _tq, _ib\n"
ns = {}
exec(code, ns)
tsf, tq, ib = ns["mk"]()
mx = 0
for df in [1,2,5,10,12.7,22,26.3,58,119,1000]:
    for t in [-3,-1,0.2,1,1.7,2.5,4,8]:
        mx = max(mx, abs(tsf(t,df) - stats.t.sf(t,df)))
    print(df, tq(0.025, df), stats.t.isf(0.025, df))
print("max abs err t", mx)
# F test
m=0
for d1,d2 in [(7,120),(7,56),(3,10)]:
    for f in [0.1,1,2.09,3,6]:
        m=max(m,abs(ib(d2/(d2+d1*f),d2/2,d1/2)-stats.f.sf(f,d1,d2)))
print("max abs err F", m)
