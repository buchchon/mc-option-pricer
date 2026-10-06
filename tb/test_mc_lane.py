"""
test_mc_lane.py - checks rtl/mc_lane.sv: bit-exact vs model, then price vs Black-Scholes
"""

import math
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, ReadOnly, NextTimeStep
from golden import (mc_lane_model, black_scholes_call, to_fx,
                    AB_FRAC, S_FRAC)

S0, K, R, SIGMA, T = 100.0, 100.0, 0.05, 0.2, 1.0
SEEDS = [0x12345678, 0x9ABCDEF1, 0x0BADF00D, 0xDEADBEEF, 0x13579BDF, 0x2468ACE0]
N_EXACT = 2_000
N_PRICE = 100_000

A_FX = to_fx((R - SIGMA**2 / 2) * T, AB_FRAC)
B_FX = to_fx(SIGMA * math.sqrt(T), AB_FRAC)
S0_FX = to_fx(S0, S_FRAC)
K_FX = to_fx(K, S_FRAC)


def pack_seeds(seeds):
    """Packs 6 seeds into the 192-bit bus: seeds[0] in bits 31:0."""
    return sum(s << (32 * i) for i, s in enumerate(seeds))


async def setup(dut):
    """Starts the clock, loads constants, holds reset for 2 cycles."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 0
    dut.start.value = 0
    dut.n_paths.value = 0
    dut.seeds.value = pack_seeds(SEEDS)
    dut.a.value = A_FX
    dut.b.value = B_FX
    dut.s0.value = S0_FX
    dut.k.value = K_FX
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def run(dut, n):
    """Pulses start for n paths, waits for done, returns (sum, oor_seen)."""
    dut.n_paths.value = n
    dut.start.value = 1
    await RisingEdge(dut.clk)
    dut.start.value = 0
    while True:
        await ClockCycles(dut.clk, 1000)
        await ReadOnly()
        if int(dut.done.value) == 1:
            break
    result = (int(dut.sum.value), int(dut.oor_seen.value))
    await NextTimeStep()
    return result


@cocotb.test()
async def test_bit_exact(dut):
    """Hardware sum equals the Python model's sum exactly."""
    await setup(dut)
    got, oor = await run(dut, N_EXACT)
    exp, exp_oor = mc_lane_model(SEEDS, A_FX, B_FX, S0_FX, K_FX, N_EXACT)
    assert got == exp, f"sum: got {got}, expected {exp}"
    assert oor == int(exp_oor), "out_of_range flag mismatch"


@cocotb.test()
async def test_rerun_reproducible(dut):
    """Two runs with the same seeds give the same sum."""
    await setup(dut)
    first, _ = await run(dut, 500)
    second, _ = await run(dut, 500)
    assert first == second, f"rerun differs: {first} vs {second}"


@cocotb.test()
async def test_price(dut):
    """Hardware Monte Carlo price lands within 4 standard errors of Black-Scholes."""
    await setup(dut)
    total, oor = await run(dut, N_PRICE)
    assert oor == 0, "some x went out of range"
    price = total / (1 << S_FRAC) / N_PRICE * math.exp(-R * T)
    bs = black_scholes_call(S0, K, R, SIGMA, T)
    std_err = 14.7 / math.sqrt(N_PRICE)    # payoff std ~14.7 for these inputs
    dut._log.info(f"hardware price {price:.4f}  Black-Scholes {bs:.4f}  "
                  f"diff {price - bs:+.4f}  (std err {std_err:.4f})")
    assert abs(price - bs) < 4 * std_err, "price too far from Black-Scholes"