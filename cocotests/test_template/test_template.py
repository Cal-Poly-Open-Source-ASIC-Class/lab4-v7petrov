
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import (
    RisingEdge, FallingEdge,
    Timer
)

@cocotb.test()
async def template_test(dut):
    
    cocotb.start_soon(Clock(dut.clk_r, 13, units='ns').start())
    cocotb.start_soon(Clock(dut.clk_w, 7, units='ns').start())


