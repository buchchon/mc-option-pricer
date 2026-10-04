"""
golden.py - reference golden model hardware will be checked against
aka the hardware's outputs will be checked against these function
"""

import math
import numpy as np


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


def mc_call_float(S0, K, r, sigma, T, n, seed):
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
    return: fair/premium price same currency as S0
    """
    rng = np.random.default_rng(seed)

    #host side constants
    a = (r - (sigma**2) / 2) * T
    b = sigma * np.sqrt(T)

    #per-path work
    Z = rng.standard_normal(n)
    S_T = S0 * np.exp(a + b*Z)
    payoff = np.maximum(S_T - K, 0)

    #host side compute
    discount = math.exp(-r * T)
    return discount * np.mean(payoff)



if __name__ == "__main__":
    S0 = 100
    K = 100
    r = 0.05
    sigma = 0.2
    T = 1
    EXPECTED = 10.4506
    SEED = 42

    #1 exact price
    price = black_scholes_call(S0, K, r, sigma, T)
    print(f"computed: {price:.4f}. expected: {EXPECTED}")

    #2 monte carlo
    print(f"{'n':>10} {'MC price':>10} {'abs error':>10}")
    for n in [1_000, 10_000, 100_000, 1_000_000]:
        mc_price = mc_call_float(S0, K, r, sigma, T, n, SEED)
        error = abs(mc_price - price)
        print(f"{n:>10} {mc_price:>10.4f} {error:>10.4f}")