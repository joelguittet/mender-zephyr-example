# @file      test_device_registration.py
# @brief     Device registration test file
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

import re
import logging
from twister_harness import Shell
from twister_harness import DeviceAdapter
from mender_management import MenderManagement

logger = logging.getLogger(__name__)

mender = MenderManagement()

def get_device_mac_address() -> str:
    output = dut.readlines_until(".*<inf>.*MAC address of the device '.*'", timeout: 60)
    f = re.search(".*<inf>.*MAC address of the device '(.+?)'", output)
    if f:
        mac_address = x.group(1)
        print(f"✅ MAC address of the device is '{mac_address}'")
        return mac_address
    else:
        raise AssertionError(f"🔴​​ MAC address of the device not found")
    return None

def test_device_registration(dut: DeviceAdapter):
    """ Get the MAC address of the device. """
    mac_address = get_device_mac_address()
    """ Ensure the device is not authorized to the mender server. """
    output = dut.readlines_until(".*<err>.*\[401\] Unauthorized: Unauthorized.*", timeout: 60)
    match_no_lines(output, ["Mender client authenticated"])
    print("✅ Device doesn't succeed to authenticate")
    device, auth_id = mender.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC {mac_address} not found on mender server"
    assert device['status'] == "pending", f"Device with MAC {mac_address} has unexpected status '{device['status']}'"
    print("✅ Device has status 'pending' on the mender server")
    """ Accept the device on the mender server. """
    mender.accept_device(mac_address)
    output = dut.readlines_until("Mender client authenticated", timeout: 300)
    match_no_lines(output, ["\[401\] Unauthorized: Unauthorized"])
    device, auth_id = mender.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC {mac_address} not found on mender server"
    assert device['status'] == "accepted", f"Device with MAC {mac_address} has unexpected status '{device['status']}'"
    print("✅ Device has status 'accepted' on the mender server")
