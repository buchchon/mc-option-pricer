"""
golden.py - reference golden model hardware will be checked against
aka the hardware's outputs will be checked against these function
"""

import math


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
    """
    d1 = ((math.log(S0/K) + (r + 0.5 * sigma**2) * T)
          /(sigma * math.sqrt(T)))
    d2 = d1 - sigma * math.sqrt(T)
    
    return S0 * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)


if __name__ == "__main__":
    S0 = 100
    K = 100
    r = 0.05
    sigma = 0.2
    T = 1
    EXPECTED = 10.4506
    price = black_scholes_call(S0, K, r, sigma, T)
    print(f"computed: {price:.4f}. expected: {EXPECTED}")