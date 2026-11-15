"""
convergence.py - Monte Carlo price vs number of paths, with a +/-2 SE band,
converging on the exact Black-Scholes price. Run from repo root.
"""

import math
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))
from golden import mc_call_float, black_scholes_call   # noqa: E402

INK, MUTED, ACCENT, GRID = "#1d2433", "#6b7280", "#2b6cb0", "#e5e7eb"

S0, K, r, sigma, T = 100, 100, 0.05, 0.2, 1
SEED = 42
bs = black_scholes_call(S0, K, r, sigma, T)

# payoff standard deviation, measured from a 1M-path run
rng = np.random.default_rng(SEED)
Z = rng.standard_normal(1_000_000)
payoff = math.exp(-r * T) * np.maximum(S0 * np.exp((r - sigma**2 / 2) * T + sigma * math.sqrt(T) * Z) - K, 0)
std = payoff.std()
print(f"Black-Scholes = {bs:.4f}, discounted payoff std = {std:.3f}")

ns = np.unique(np.logspace(2, 6.5, 30).astype(int))
prices = [mc_call_float(S0, K, r, sigma, T, int(n), SEED) for n in ns]
band = 2 * std / np.sqrt(ns)

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.fill_between(ns, bs - band, bs + band, color=ACCENT, alpha=0.15, lw=0, label="±2 standard errors")
ax.axhline(bs, color=INK, lw=1.2, label=f"Black-Scholes = {bs:.4f}")
ax.semilogx(ns, prices, "o-", color=ACCENT, ms=4, lw=1.5, label="Monte Carlo estimate")
ax.set_xlabel("number of simulated paths", color=INK)
ax.set_ylabel("call price", color=INK)
ax.set_title("Error shrinks as 1/√n: each extra digit costs 100× the paths",
             loc="left", color=INK, fontsize=12)
ax.grid(color=GRID, which="major", zorder=0)
ax.legend(frameon=False)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "convergence.svg"), transparent=True)
fig.savefig(os.path.join(OUT, "convergence.png"), dpi=200, transparent=True)
print("wrote figures/out/convergence.svg")
