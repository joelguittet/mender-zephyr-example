# @file      test_foo.py
# @brief     Foo test file
#
# Copyright joelguittet and mender-mcu-client contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from twister_harness import Shell
from twister_harness import DeviceAdapter
from mender_management import MenderManagement

logger = logging.getLogger(__name__)

mender = MenderManagement()

def test_device_registration(dut: DeviceAdapter):
    # Get device
    # TODO get MAC from command line
    mac_address = "00:08:dc:01:02:03"
    # TODO with timeout and not 'Mender client authenticated'
    dut.readlines_until('.*<err>.*\[401\] Unauthorized: Unauthorized.*')
    device, auth_id = mender.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC {mac_address} not found"
    logger.info(f"Found device ID: {device['id']} status={device['status']}")
    assert device['status'] == "pending", f"Device with MAC {mac_address} has not the expected status"
    # Accept the device
    mender.accept_device(mac_address)
    # TODO with timeout and not Unauthorized
    dut.readlines_until('Mender client authenticated')
    dut.readlines_until('No deployment available')
