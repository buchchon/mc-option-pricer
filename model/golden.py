"""
golden.py - reference golden model hardware will be checked against
aka the hardware's outputs will be checked against these function
"""

import math
import numpy as np

MASK32 = 0xFFFF_FFFF
U_BITS = 12 #bits per hardware uniform 
SIX_FX = 6 << U_BITS 

def norm_cdf(x):
    """
    computes cumulative distribution function. Ex. given a value what is the 
    probability of a standard normal random variable Z will show up that is
    less than or equal to x
    """
    return 0.5 * (1 + math.erf(x/math.sqrt(2)))


def black_scholes_call(S0, K, r, sigma, T):
    """
    Computes the fair price of a European call option as of right now
    Args:
        S0: current stock price
        K: strike price (price to exercise)
        r: risk free interest annual rate in decimal
        sigma: annual stock volatility in decimal
        T: time until expiration in years
    return: returns fair/premium price
    """
    d1 = ((math.log(S0/K) + (r + 0.5 * sigma**2) * T)
          /(sigma * math.sqrt(T)))
    d2 = d1 - sigma * math.sqrt(T)
    
    return S0 * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)


def mc_call_float(S0, K, r, sigma, T, n, seed, use_clt = False):
    """
    Estimates the fair price of a European call option by Monte Carlo 
    simulation
    Args:
        S0: current stock price
        K: strike price (price to exercise)
        r: risk free interest annual rate in decimal
        sigma: annual stock volatility in decimal
        T: time until expiration in years
        n: number of simulated price paths
        seed: seed for the random number generator; the same seed 
              gives the same result.
        use_clt: if true draw Z using hardware method, if false use numpy
    return: fair/premium price same currency as S0
    """
    rng = np.random.default_rng(seed)

    #host side constants
    a = (r - (sigma**2) / 2) * T
    b = sigma * np.sqrt(T)

    #per-path work
    if use_clt:
        Z = clt_normal(rng, n) # cheap hardware Gaussian
    else:
        Z = rng.standard_normal(n) # exact Gaussian (reference)
    S_T = S0 * np.exp(a + b*Z)
    payoff = np.maximum(S_T - K, 0)

    #host side compute
    discount = math.exp(-r * T)
    return discount * np.mean(payoff)

def clt_normal(rng, n):
    """
    Generates approximate standard normal random numbers using central limit
    theorem: sum 12 uniforms on [0, 1) and subtract by 6. This is software
    model of the hardware Gaussian generator (uses adders only)
    Args:
        rng: random numpy generator
        n: number of samples to generate per simulated path
    return: array of n values with mean ~0 and variance ~1, limited to [-6, 6]
    """
    U = rng.random((n, 12))
    return U.sum(axis = 1) - 6

def xorshift32(state, n):
    """
    return next n states of xorshift from a seed
    """
    out = []
    for i in range(n):
        state ^= (state << 13) & MASK32
        state ^= (state >> 17)
        state ^= (state << 5) & MASK32
        out.append(state)
    return out

def clt_normal_fixed(u_list):
    """
    bit-exact model of rtl/gaussian_clt.sv
    Args: u_list = 12 ints in [0, 4095]
    Returns: signed int, Z in Q3.12
    """
    total = 0
    for u in u_list:
        total = total + u
    return total - SIX_FX

if __name__ == "__main__":
    S0 = 100
    K = 100
    r = 0.05
    sigma = 0.2
    T = 1
    EXPECTED = 10.4506
    SEED = 42
    N_STATS = 1_000_000

    #1 exact price
    price = black_scholes_call(S0, K, r, sigma, T)
    print(f"computed: {price:.4f}. expected: {EXPECTED}")

    #2 monte carlo
    print(f"{'n':>10} {'MC price':>10} {'abs error':>10}"
          f"{'CLT Price':>10} {'CLT Error':>10}")
    for n in [1_000, 10_000, 100_000, 1_000_000]:
        mc_price = mc_call_float(S0, K, r, sigma, T, n, SEED)
        error = abs(mc_price - price)
        clt_price = mc_call_float(S0, K, r, sigma, T, n, SEED, use_clt=True)
        clt_error = abs(clt_price - price)
        print(f"{n:>10} {mc_price:>10.4f} {error:>10.4f}"
              f" {clt_price:>10.4f} {clt_error:>10.4f}")

    #3 Z stats: does the CLT trick look like a standard normal
    Z_np = np.random.default_rng(SEED).standard_normal(N_STATS)
    Z_clt = clt_normal(np.random.default_rng(SEED), N_STATS)
    print(f"numpy: mean {Z_np.mean():.4f}  var {Z_np.var():.4f}"
          f"  max|Z| {np.abs(Z_np).max():.2f}")
    print(f"CLT:   mean {Z_clt.mean():.4f}  var {Z_clt.var():.4f}"
          f"  max|Z| {np.abs(Z_clt).max():.2f}")