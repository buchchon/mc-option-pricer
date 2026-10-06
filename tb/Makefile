SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(PWD)/../rtl/xorshift32.sv
COCOTB_TOPLEVEL = xorshift32
COCOTB_TEST_MODULES = test_xorshift32
export PYTHONPATH := $(PWD)/../model:$(PYTHONPATH)
include $(shell cocotb-config --makefiles)/Makefile.sim