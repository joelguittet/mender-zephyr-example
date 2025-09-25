#import logging
from twister_harness import Shell
from twister_harness import DeviceAdapter

#logger = logging.getLogger(__name__)

def test_sample(dut: DeviceAdapter):
    dut.readlines_until('.*<err>.*\[401\] Unauthorized: Unauthorized.*')
    #dut.readlines_until('Mender client authenticated')
    #dut.readlines_until('No deployment available')

def test_sample(dut: DeviceAdapter):
    dut.readlines_until('.*<err>.*\[401\] Unauthorized: Unauthorized.*')
    #dut.readlines_until('Mender client authenticated')
    #dut.readlines_until('No deployment available')
