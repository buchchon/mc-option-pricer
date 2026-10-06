TOP ?= xorshift32
SIM ?= verilator
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(wildcard $(PWD)/../rtl/*.sv)
COCOTB_TOPLEVEL = $(TOP)
COCOTB_TEST_MODULES = test_$(TOP)
SIM_BUILD = sim_build/$(TOP)
export PYTHONPATH := $(PWD)/../model:$(PYTHONPATH)
include $(shell cocotb-config --makefiles)/Makefile.sim