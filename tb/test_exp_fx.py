"""
test_exp_fx.py - checks rtl/exp_fx.sv against the Python model (any latency)
"""

import math
import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, ReadOnly
from golden import exp_fixed, X_FRAC, E_FRAC

N = 2000
X_MIN = -(2 << X_FRAC)          # -2.0 in Q2.16
X_MAX = (2 << X_FRAC) - 1       # just under +2.0


async def reset(dut):
    """Starts the clock and holds reset for 2 cycles."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 0
    dut.in_valid.value = 0
    dut.x.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def drive_and_wait(dut, x):
    """Drives one x for one cycle, then waits until out_valid goes high."""
    dut.x.value = x
    dut.in_valid.value = 1
    await RisingEdge(dut.clk)
    dut.in_valid.value = 0
    while True:
        await ReadOnly()
        if int(dut.out_valid.value) == 1:
            break
        await RisingEdge(dut.clk)


async def drive_and_check(dut, x):
    """Drives one x, waits for the result, checks y. Returns y."""
    await drive_and_wait(dut, x)
    assert int(dut.out_of_range.value) == 0, f"x={x}: flagged out of range"
    got = int(dut.y.value)
    exp = exp_fixed(x)
    assert got == exp, f"x={x}: got {got}, expected {exp}"
    await RisingEdge(dut.clk)
    return got


@cocotb.test()
async def test_corners(dut):
    """0, +/-1 LSB, both range ends, and table-boundary inputs."""
    await reset(dut)
    for x in (0, 1, -1, X_MIN, X_MAX, 255, 256, -256):
        await drive_and_check(dut, x)


@cocotb.test()
async def test_random(dut):
    """N random x match the model; also reports error vs true e^x."""
    await reset(dut)
    rng = random.Random(42)
    worst = 0.0
    for _ in range(N):
        x = rng.randint(X_MIN, X_MAX)
        got = await drive_and_check(dut, x)
        err = abs(got / (1 << E_FRAC) - math.exp(x / (1 << X_FRAC)))
        worst = max(worst, err)
    dut._log.info(f"worst abs error vs math.exp: {worst:.2e} "
                  f"({worst * (1 << E_FRAC):.2f} LSB)")


@cocotb.test()
async def test_out_of_range(dut):
    """x = +2.0 and just below -2.0 must raise out_of_range."""
    await reset(dut)
    for x in (2 << X_FRAC, -(2 << X_FRAC) - 1):
        await drive_and_wait(dut, x)
        assert int(dut.out_of_range.value) == 1, f"x={x}: not flagged"
        await RisingEdge(dut.clk)