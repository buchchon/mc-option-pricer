"""
test_gaussian_clt.py - checks rtl/gaussian_clt.sv against the Python model
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, ReadOnly, NextTimeStep
from golden import clt_normal_fixed, U_BITS

N = 1000


def pack(us):
    """Packs 12 ints into one 144-bit int: us[0] in bits 11:0, etc."""
    return sum(x << (U_BITS * i) for i, x in enumerate(us))


async def reset(dut):
    """Starts the clock and holds reset for 2 cycles."""
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 0
    dut.in_valid.value = 0
    dut.u.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


async def drive_and_check(dut, us):
    """Drives one set of 12 uniforms and checks z one cycle later."""
    dut.u.value = pack(us)
    dut.in_valid.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.out_valid.value) == 1, "out_valid not high"
    got = dut.z.value.to_signed()
    exp = clt_normal_fixed(us)
    assert got == exp, f"u={us}: got {got}, expected {exp}"
    await NextTimeStep()


@cocotb.test()
async def test_corners(dut):
    """All-zero, all-max, and all-middle inputs."""
    await reset(dut)
    for us in ([0] * 12, [4095] * 12, [2048] * 12):
        await drive_and_check(dut, us)


@cocotb.test()
async def test_random(dut):
    """N random input sets match the model."""
    await reset(dut)
    rng = random.Random(42)
    for _ in range(N):
        us = [rng.getrandbits(U_BITS) for _ in range(12)]
        await drive_and_check(dut, us)