"""B3-12: fixed criterion's minus rate with the declared season term and with it removed (same rng draws)."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stats_run import load, stream_rng, SEED
fix = load("B3-12", "fixed")
ar1 = fix._ar1
def world(rng, season_amp, wave_sd=55.0):
    months = 120
    time_years = np.arange(months) / 12.0
    population = 250.0 + 1.5 * time_years + ar1(rng, months, 0.9, 4.0)
    season = season_amp * np.cos(2.0 * np.pi * np.arange(months) / 12.0)
    waves = ar1(rng, months, 0.6, wave_sd)
    month_noise = rng.normal(0.0, 20.0, months)
    adm = np.round(8.0 * population + season + waves + month_noise)
    return {"admissions": adm, "population": population, "time_years": time_years}
N = 2000
for amp in (80.0, 0.0):
    h = sum(fix.criterion(world(stream_rng(SEED, "world:minus", i), amp))[1] for i in range(N))
    print(f"season amplitude {amp}: fixed holds {h}/{N} = {h/N:.3f}")
h = sum(fix.criterion(world(stream_rng(SEED, "world:minus", i), 80.0, wave_sd=0.0))[1] for i in range(N))
print(f"season 80, no AR waves: fixed holds {h}/{N} = {h/N:.3f}")
