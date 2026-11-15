"""
fmax.py - Fmax after each pipelining step (nextpnr post-route, ECP5-85F).
Numbers copied from synth/pnr.log of each run (tags baseline-61mhz, pipelined-89mhz).
Run from repo root: python figures/fmax.py
"""

import os
import matplotlib.pyplot as plt

# ---- site palette: change these to match your website ----
INK, MUTED, ACCENT, GRID = "#1d2433", "#6b7280", "#2b6cb0", "#e5e7eb"

STEPS = [
    ("Baseline",              61.6, 376, "BRAM read → multiply\n→ 2 adds in one cycle"),
    ("+ pipelined exp",       72.6, 423, "S0×e^x → round\n→ compare → subtract"),
    ("+ split payoff stage",  89.1, 445, "exp multiply → 2 adds\n(~40% routing)"),
]

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

fig, ax = plt.subplots(figsize=(8, 4.5))
names = [s[0] for s in STEPS]
fmax = [s[1] for s in STEPS]
bars = ax.bar(names, fmax, color=[MUTED, MUTED, ACCENT], width=0.55, zorder=2)

for bar, (_, f, ff, path) in zip(bars, STEPS):
    x = bar.get_x() + bar.get_width() / 2
    ax.text(x, f + 2, f"{f} MHz", ha="center", fontsize=13, weight="bold", color=INK)
    ax.text(x, f / 2, f"{ff} FFs", ha="center", fontsize=9, color="white")
    ax.text(x, -14, f"critical path:\n{path}", ha="center", va="top", fontsize=8, color=MUTED)

ax.set_ylim(0, 105)
ax.set_ylabel("Fmax (MHz) = paths/s per lane, in millions", color=INK)
ax.set_title("One lane, Lattice ECP5-85F: +45% throughput for +69 flip-flops",
             loc="left", color=INK, fontsize=12)
ax.grid(axis="y", color=GRID, zorder=0)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.subplots_adjust(bottom=0.32)
fig.savefig(os.path.join(OUT, "fmax.svg"), transparent=True)
fig.savefig(os.path.join(OUT, "fmax.png"), dpi=200, transparent=True)
print("wrote figures/out/fmax.svg")
