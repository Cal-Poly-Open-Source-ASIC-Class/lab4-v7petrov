import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb.queue import Queue
import random
import logging

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncFifoTB:
    def __init__(self, dut):
        self.dut = dut
        self.expected_data = []
        self.actual_data = []

    async def reset_dut(self):
        self.dut.i_wrst_n.value = 0
        self.dut.i_rrst_n.value = 0
        self.dut.i_wr_en.value = 0
        self.dut.i_rd_en.value = 0
        self.dut.i_wdata.value = 0
        await Timer(100, units='ns')
        self.dut.i_wrst_n.value = 1
        self.dut.i_rrst_n.value = 1
        await Timer(50, units='ns')
        logger.info("Reset done")

    async def write_data(self, data):
        await RisingEdge(self.dut.i_wclk)
        if not self.dut.o_wfull.value:
            self.dut.i_wr_en.value = 1
            self.dut.i_wdata.value = data
            await RisingEdge(self.dut.i_wclk)
            self.dut.i_wr_en.value = 0
            self.expected_data.append(data)
            return True
        else:
            logger.warning("Write blocked: FIFO full")
            return False

    async def read_data(self):
        await RisingEdge(self.dut.i_rclk)
        if not self.dut.o_rempty.value:
            self.dut.i_rd_en.value = 1
            await RisingEdge(self.dut.i_rclk)
            self.dut.i_rd_en.value = 0
            data = self.dut.o_rdata.value.integer
            self.actual_data.append(data)
            return data
        else:
            logger.warning("Read blocked: FIFO empty")
            return None

    def verify_data(self):
        if self.expected_data != self.actual_data:
            logger.error("Data mismatch!")
            for i, (exp, act) in enumerate(zip(self.expected_data, self.actual_data)):
                if exp != act:
                    logger.error(f"Index {i}: expected 0x{exp:02x}, got 0x{act:02x}")
            return False
        logger.info("Data verified successfully")
        return True

@cocotb.test()
async def test_cocomelon_concurrent_rw(dut):
    """Test concurrent reads and writes on asynchronous FIFO"""
    tb = AsyncFifoTB(dut)

    cocotb.start_soon(Clock(dut.i_wclk, 11, units="ns").start())
    cocotb.start_soon(Clock(dut.i_rclk, 9, units="ns").start())

    await tb.reset_dut()

    logger.info("Starting concurrent read/write test")

    async def writer():
        for i in range(20):
            while dut.o_wfull.value:
                await RisingEdge(dut.i_wclk)
            await tb.write_data(i)
            await Timer(random.randint(20, 60), units="ns")

    async def reader():
        read_count = 0
        while read_count < 20:
            while dut.o_rempty.value:
                await RisingEdge(dut.i_rclk)
            data = await tb.read_data()
            if data is not None:
                read_count += 1
            await Timer(random.randint(10, 50), units="ns")

    writer_task = cocotb.start_soon(writer())
    reader_task = cocotb.start_soon(reader())

    await writer_task
    await reader_task

    assert tb.verify_data(), "Concurrent RW test: Data verification failed"
    logger.info("Concurrent RW test passed")

@cocotb.test()
async def test_cocomelon_independent_domains(dut):
    """Test read and write domains independently"""
    tb = AsyncFifoTB(dut)

    cocotb.start_soon(Clock(dut.i_wclk, 8, units="ns").start())
    cocotb.start_soon(Clock(dut.i_rclk, 12, units="ns").start())

    await tb.reset_dut()

    logger.info("Testing write-only phase")

    # Write some data without reading
    for i in range(8):
        success = await tb.write_data(0xA0 + i)
        assert success, f"Write {i} failed"

    await Timer(200, units="ns")

    logger.info("Testing read-only phase")

    # Now read the data without any writes
    for expected in [0xA0 + i for i in range(8)]:
        data = await tb.read_data()
        assert data == expected, f"Expected {expected}, got {data}"

    await Timer(100, units="ns")

    assert tb.verify_data(), "Independent domains test: Data mismatch"
    logger.info("Independent domain test passed")
