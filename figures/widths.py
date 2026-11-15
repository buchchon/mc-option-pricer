"""
widths.py - quantization error vs fraction bits, against the Monte Carlo noise floor.
Fixed-point and float use the SAME random numbers (same seed), so the gap is
pure rounding error. Run from repo root: python figures/widths.py  (~30 s)
"""

import math
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))
from golden import mc_call_float, clt_normal          # noqa: E402
from explore_widths import mc_call_fixed              # noqa: E402

INK, MUTED, ACCENT, WARN, GRID = "#1d2433", "#6b7280", "#2b6cb0", "#c2410c", "#e5e7eb"

S0, K, r, sigma, T = 100, 100, 0.05, 0.2, 1
N, SEED = 1_000_000, 42

# Monte Carlo noise floor: standard error of the estimate at N paths
rng = np.random.default_rng(SEED)
Z = clt_normal(rng, N)
payoff = math.exp(-r * T) * np.maximum(S0 * np.exp((r - sigma**2 / 2) * T + sigma * math.sqrt(T) * Z) - K, 0)
se = payoff.std() / math.sqrt(N)
print(f"payoff std = {payoff.std():.3f}, MC standard error at {N:,} paths = {se:.4f}")

ref = mc_call_float(S0, K, r, sigma, T, N, SEED, use_clt=True)
bits = list(range(4, 21))
errs = []
for f in bits:
    e = abs(mc_call_fixed(S0, K, r, sigma, T, N, SEED, f) - ref)
    errs.append(e)
    print(f"F={f:2d}  quant error = {e:.6f}  ({se / e:5.1f}x below noise)" if e else f"F={f:2d}  0")

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.semilogy(bits, errs, "o-", color=ACCENT, lw=2, zorder=3, label="quantization error")
ax.axhline(se, color=WARN, ls="--", lw=1.5, label=f"Monte Carlo noise (1 SE, {N:,} paths)")
ax.annotate("14 bits worse than 12:\nconstant-rounding bias",
            xy=(14, errs[bits.index(14)]), xytext=(15.2, 0.02),
            arrowprops=dict(arrowstyle="->", color=MUTED), color=MUTED, fontsize=9)
ax.set_xlabel("fraction bits (all signals)", color=INK)
ax.set_ylabel("|fixed − float| price error", color=INK)
ax.set_title("Precision matched to the noise floor", loc="left", color=INK, fontsize=12)
ax.set_xticks(bits)
ax.grid(color=GRID, which="major", zorder=0)
ax.legend(frameon=False)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "widths.svg"), transparent=True)
fig.savefig(os.path.join(OUT, "widths.png"), dpi=200, transparent=True)
print("wrote figures/out/widths.svg")
