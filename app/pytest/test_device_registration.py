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

import logging
from twister_harness import DeviceAdapter, Shell
from mender_management import MenderManagement
from helpers import Helpers

logger = logging.getLogger(__name__)

mender_management = MenderManagement()
helpers = Helpers()

#@pytest.mark.dependency()
def test_device_registration(shell: Shell, dut: DeviceAdapter):
    """Get the MAC address of the device."""
    mac_address = helpers.get_device_mac_address(dut)
    """Decomissioning of the device on the server (if it is already registered)."""
    try:
        mender_management.delete_device(mac_address)
    except:
        pass
    """Reset the device to force reconnection to the server."""
    shell.exec_command("kernel reboot")
    """Ensure the device is not authorized to the mender server."""
    helpers.assert_device_not_authenticated(dut)
    device, auth_id = mender_management.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC {mac_address} not found on mender server"
    assert device['status'] == "pending", f"Device with MAC {mac_address} has unexpected status '{device['status']}'"
    print("✅ Device has status 'pending' on the mender server")
    """Accept the device on the mender server."""
    mender_management.accept_device(mac_address)
    """Ensure the device is authorized on the mender server."""
    helpers.assert_device_authenticated(dut)
    device, auth_id = mender_management.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC {mac_address} not found on mender server"
    assert device['status'] == "accepted", f"Device with MAC {mac_address} has unexpected status '{device['status']}'"
    print("✅ Device has status 'accepted' on the mender server")
