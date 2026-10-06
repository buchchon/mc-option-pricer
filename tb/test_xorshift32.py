"""
test_xorshift32.py - checks rtl/xorshift32.sv against the Python model
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, ReadOnly
from golden import xorshift32

SEED = 1
N = 1000

@cocotb.test()
async def test_matches_model(dut):
    """
    Hardware output matches golden.xorshift32 for N cycles
    """

    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())

    # load seed through reset
    dut.seed.value = SEED
    dut.rst_n.value = 0
    dut.en.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await ReadOnly()
    assert int(dut.out.value) == SEED

    # step N times comparing each cycle
    expected = xorshift32(SEED, N)
    await RisingEdge(dut.clk)
    dut.en.value = 1
    for i in range(N):
        await RisingEdge(dut.clk)
        await ReadOnly()
        got = int(dut.out.value)
        assert got == expected[i], \
            print(f"cycle {i}: got {got:#010x}, expected {expected[i]:#010x}")
