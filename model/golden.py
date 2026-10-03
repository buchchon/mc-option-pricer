import math

def norm_cdf(x):
    return 0.5 * (1 + math.erf(x/math.sqrt(2)))

def black_scholes_call(S0, K, r, sigma, T):
    d1 = ((math.log(S0/K) + (r + 0.5 * sigma**2) * T)
          /(sigma * math.sqrt(T)))
    d2 = d1 - sigma * math.sqrt(T)
    
    return S0 * norm_cdf(d1) - K * math.e ** (-r * T) * norm_cdf(d2)


if __name__ == "__main__":
    print(black_scholes_call(100, 100, 0.05, 0.2, 1))