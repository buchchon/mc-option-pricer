"""
explore_widths.py - decides fraction and integer bits for hardware
"""

import math
import numpy as np
from golden import clt_normal, mc_call_float

def quantize(x, frac_bits):
    """
    rounds x to nearest multiple of 2^-fracbits
    Args:
        x: number
        frac_bits: number of fraction bits
    return: return rounded x value
    """
    scale = 2 ** frac_bits
    return np.round(x * scale) / scale

def mc_call_fixed(S0, K, r, sigma, T, n, seed, frac_bits):
    """
    same as mc call float except every value is rounded to frac bits
    new arg: frac_bits : number of fraction bits
    """

    rng = np.random.default_rng(seed)

    #host side constants round once
    a = quantize((r - (sigma**2) / 2) * T, frac_bits)
    b = quantize(sigma * np.sqrt(T), frac_bits)

    #per path work
    Z = quantize(clt_normal(rng, n), frac_bits)
    x = quantize(a + b * Z, frac_bits)
    exp_x = quantize(np.exp(x), frac_bits)
    S_T = quantize(S0 * exp_x, frac_bits)
    payoff = quantize(np.maximum(S_T - K, 0), frac_bits)

    #host side
    discount = math.exp(-r * T)
    return discount * np.mean(payoff)

if __name__ == "__main__":
    S0 = 100
    K = 100
    r = 0.05
    sigma = 0.2
    T = 1
    SEED = 42
    N = 1_000_000

    # float reference with the SAME random numbers -> isolates rounding error
    ref = mc_call_float(S0, K, r, sigma, T, N, SEED, use_clt=True)
    print(f"float reference: {ref:.6f}")

    print(f"{'frac bits':>10} {'fixed price':>12} {'quant error':>12}")
    for f in range(4, 21, 2):
        fixed = mc_call_fixed(S0, K, r, sigma, T, N, SEED, f)
        q_err = abs(fixed - ref)
        print(f"{f:>10} {fixed:>12.6f} {q_err:>12.6f}")