"""
exp_error.py - EXHAUSTIVE error of the hardware exp model (bit-exact with
rtl/exp_fx.sv) vs math.exp, over every valid input x in [-2, 2):
2^18 = 262,144 values. Run from repo root: python figures/exp_error.py
"""

import math
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "model"))
from golden import exp_fixed, X_FRAC, E_FRAC   # noqa: E402

INK, MUTED, ACCENT, WARN, GRID = "#1d2433", "#6b7280", "#2b6cb0", "#c2410c", "#e5e7eb"

xs = np.arange(-(2 << X_FRAC), 2 << X_FRAC)                    # every valid input
hw = np.array([exp_fixed(int(x)) for x in xs]) / (1 << E_FRAC)
true = np.exp(xs / (1 << X_FRAC))
err_lsb = (hw - true) * (1 << E_FRAC)

worst = np.abs(err_lsb).max()
print(f"inputs checked: {len(xs):,}")
print(f"worst-case |error| = {worst:.2f} LSB = {worst / (1 << E_FRAC):.2e}")
print(f"mean error = {err_lsb.mean():+.3f} LSB")

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(xs / (1 << X_FRAC), err_lsb, ",", color=ACCENT, alpha=0.5, rasterized=True)
for y in (worst, -worst):
    ax.axhline(y, color=WARN, ls="--", lw=1)
ax.text(-1.95, worst + 0.1, f"worst case ±{worst:.2f} LSB", color=WARN, fontsize=9)
ax.set_xlabel("x", color=INK)
ax.set_ylabel("error vs. math.exp (LSB = 2⁻¹⁵)", color=INK)
ax.set_title(f"exp unit: all {len(xs):,} inputs checked", loc="left", color=INK, fontsize=12)
ax.set_ylim(-worst - 0.6, worst + 0.6)
ax.grid(color=GRID, zorder=0)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "exp_error.svg"), transparent=True)
fig.savefig(os.path.join(OUT, "exp_error.png"), dpi=200, transparent=True)
print("wrote figures/out/exp_error.svg")
