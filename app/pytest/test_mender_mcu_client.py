# @file      test_mender_mcu_client.py
# @brief     Mender MCU client test file
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
import time
import pytest
import logging
from pathlib import Path
from twister_harness import DeviceAdapter, Shell
from twister_harness.helpers.utils import find_in_config
from mender_management import MenderManagement
from helpers import Helpers

logger = logging.getLogger(__name__)

mender_management = MenderManagement()
helpers = Helpers()

@pytest.mark.dependency()
def test_device_registration(dut: DeviceAdapter, shell: Shell):
    """Get the MAC address of the device."""
    mac_address = helpers.get_device_mac_address(dut)
    """Decomissioning of the device on the server (if it is already registered)."""
    try:
        mender_management.delete_device(mac_address)
    except:
        pass
    """Reset the device to force reconnection to the server."""
    print(f"TODO REMOVE shell is {shell}")# TODO REM
    shell.exec_command("kernel reboot")
    """Ensure the device is not authorized to the mender server."""
    helpers.assert_device_not_authenticated(dut)
    device, auth_id = mender_management.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC {mac_address} not found on mender server"
    assert device["status"] == "pending", f"Device with MAC {mac_address} has unexpected status '{device["status"]}'"
    print("✅ Device has status 'pending' on the mender server")
    """Accept the device on the mender server."""
    mender_management.accept_device(mac_address)
    """Ensure the device is authorized on the mender server."""
    helpers.assert_device_authenticated(dut)
    device, auth_id = mender_management.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC {mac_address} not found on mender server"
    assert device["status"] == "accepted", f"Device with MAC {mac_address} has unexpected status '{device["status"]}'"
    print("✅ Device has status 'accepted' on the mender server")

@pytest.mark.dependency(depends=['test_device_registration'])
def test_device_inventory(dut: DeviceAdapter):
    """Get the MAC address of the device."""
    mac_address = helpers.get_device_mac_address(dut)
    """Ensure the device is authorized on the mender server."""
    # TODO simplify
    try:
        helpers.assert_device_authenticated(dut)
    except:
        mender_management.accept_device(mac_address)
        helpers.assert_device_authenticated(dut)
    device, auth_id = mender_management.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC {mac_address} not found on mender server"
    assert device["status"] == "accepted", f"Device with MAC {mac_address} has unexpected status '{device["status"]}'"
    print("✅ Device has status 'accepted' on the mender server")
    """Wait to let time to the device to push the inventory content."""
    time.sleep(60)
    """Ensure of the device inventory content."""
    inventory = mender_management.get_device_inventory(device["id"])
    print(f"Device inventory: {inventory}")
    expected_inventory = {}
    expected_inventory["artifact_name"] = f"{find_in_config(
        Path(dut.device_config.app_build_dir) / "zephyr" / ".config",
        "CONFIG_EXAMPLE_ARTIFACT_NAME_PREFIX")}-v0.1.0"
    expected_inventory["rootfs-image.version"] = f"{find_in_config(
        Path(dut.device_config.app_build_dir) / "zephyr" / ".config",
        "CONFIG_EXAMPLE_ARTIFACT_NAME_PREFIX")}-v0.1.0"
    expected_inventory["device_type"] = find_in_config(
        Path(dut.device_config.app_build_dir) / "zephyr" / ".config",
        "CONFIG_EXAMPLE_DEVICE_TYPE")
    expected_inventory["latitude"] = "45.8325"
    expected_inventory["longitude"] = "6.864722"
    expected_inventory["mender-mcu-client"] = "[0-9]+.[0-9]+.[0-9]+"
    expected_inventory["zephyr-rtos"] = "[0-9]+.[0-9]+.[0-9]+"
    print(f"Device expected inventory: {expected_inventory}")
    for key, val in expected_inventory.items():
        print(f"TODO REM check {inventory.get(key)} for {val}") # TODO REM
        m = re.search(val, inventory.get(key))
        if m is None:
            raise AssertionError(f"🔴​​​ Device inventory is invalid")
    print("✅ Device inventory contains expected inventory items")
