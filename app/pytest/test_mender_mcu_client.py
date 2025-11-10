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


import logging
import pytest
import time
import random
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from twister_harness import DeviceAdapter, Shell
from twister_harness.helpers.utils import find_in_config
from mender_management import MenderManagement
from helpers import Helpers

logger = logging.getLogger(__name__)

mender_management = MenderManagement()
helpers = Helpers()


@pytest.mark.dependency()
def test_device_registration(dut: DeviceAdapter):
    """Get the MAC address of the device."""
    mac_address = helpers.get_device_mac_address(dut)
    """Ensure the device is not authorized to the mender server."""
    helpers.assert_device_not_authenticated(dut)
    device = mender_management.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC '{mac_address}' not found on mender server"
    assert device["status"] == "pending", f"Device with MAC '{mac_address}' has unexpected status '{device["status"]}'"
    print("✅ Device has status 'pending' on the mender server")
    """Accept the device on the mender server."""
    mender_management.accept_device(device)
    """Ensure the device is authorized on the mender server."""
    helpers.assert_device_authenticated(dut)
    device = mender_management.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC '{mac_address}' not found on mender server"
    assert device["status"] == "accepted", f"Device with MAC '{mac_address}' has unexpected status '{device["status"]}'"
    print("✅ Device has status 'accepted' on the mender server")
    print("✅ Device registration done successfully on the mender server")


@pytest.mark.dependency(depends=["test_device_registration"])
def test_device_inventory(dut: DeviceAdapter):
    """Get the MAC address of the device."""
    mac_address = helpers.get_device_mac_address(dut)
    """Ensure the device is authorized on the mender server."""
    helpers.assert_device_authenticated(dut)
    device = mender_management.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC '{mac_address}' not found on mender server"
    assert device["status"] == "accepted", f"Device with MAC '{mac_address}' has unexpected status '{device["status"]}'"
    print("✅ Device has status 'accepted' on the mender server")
    """Wait until the device inventory is updated."""
    def get_device_inventory():
        inventory = mender_management.get_device_inventory(device)
        if inventory.get("updated_ts"):
            if datetime.fromisoformat(inventory.get("updated_ts")) > datetime.now() - timedelta(seconds=10):
                return inventory
        return None
    inventory = helpers.run_until(get_device_inventory, 60, 5)
    if inventory == None:
        raise AssertionError("🔴​​​ Device inventory not found")
    """Ensure of the device inventory content."""
    inventory = {item["name"]: item["value"] for item in inventory.get("attributes", [])}
    print(f"Device reported inventory: '{inventory}'")
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
    print(f"Device expected inventory: '{expected_inventory}'")
    for key, val in expected_inventory.items():
        m = re.search(val, inventory.get(key))
        if m is None:
            raise AssertionError("🔴​​​ Device inventory is invalid")
    print("✅ Device inventory contains expected inventory items")


@pytest.mark.dependency(depends=["test_device_registration"])
def test_device_configuration(dut: DeviceAdapter):
    """Get the MAC address of the device."""
    mac_address = helpers.get_device_mac_address(dut)
    """Ensure the device is authorized on the mender server."""
    helpers.assert_device_authenticated(dut)
    device = mender_management.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC '{mac_address}' not found on mender server"
    assert device["status"] == "accepted", f"Device with MAC '{mac_address}' has unexpected status '{device["status"]}'"
    print("✅ Device has status 'accepted' on the mender server")
    """Wait to let time to the device to push the configuration content."""
    time.sleep(60)
    """Print the device configuration content."""
    configuration = mender_management.get_device_configuration(device)
    print(f"Device reported configuration: '{configuration["reported"]}'")
    """Generate a random configuration content with several uuids."""
    """Generating such configuration ensure very easily the previous one was different."""
    expected_configuration = {f"uuid{index+1}": str(uuid.uuid4()) for index in range(random.randint(4, 8))}
    """Set device configuration."""
    mender_management.set_device_configuration(device, expected_configuration)
    mender_management.deploy_device_configuration(device)
    """Wait to let time to the device to download and push the configuration content."""
    time.sleep(600)
    """Ensure of the device configuration content."""
    configuration = mender_management.get_device_configuration(device)
    print(f"Device reported configuration: '{configuration["reported"]}'")
    print(f"Device expected configuration: '{expected_configuration}'")
    if configuration["reported"] != expected_configuration:
        raise AssertionError("🔴​​​ Device configuration is invalid")
    print("✅ Device configuration contains expected configuration items")


@pytest.mark.dependency(depends=["test_device_registration"])
def test_device_valid_firmware_update(dut: DeviceAdapter):
    """Get the MAC address of the device."""
    mac_address = helpers.get_device_mac_address(dut)
    """Ensure the device is authorized on the mender server."""
    helpers.assert_device_authenticated(dut)
    device = mender_management.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC '{mac_address}' not found on mender server"
    assert device["status"] == "accepted", f"Device with MAC '{mac_address}' has unexpected status '{device["status"]}'"
    print("✅ Device has status 'accepted' on the mender server")
    """Create a new firmware update."""
    expected_version = "0.0.2+0"
    key_file = find_in_config(Path(dut.device_config.build_dir) / "mcuboot" / "zephyr" / ".config", "CONFIG_BOOT_SIGNATURE_KEY_FILE")
    device_type = find_in_config(Path(dut.device_config.app_build_dir) / "zephyr" / ".config", "CONFIG_EXAMPLE_DEVICE_TYPE")
    artifact_name_prefix = find_in_config(Path(dut.device_config.app_build_dir) / "zephyr" / ".config", "CONFIG_EXAMPLE_ARTIFACT_NAME_PREFIX")
    artifact = helpers.create_mender_artifact(dut.device_config.app_build_dir, key_file, device_type, artifact_name_prefix, expected_version)
    print(f"artifact file path is '{artifact}'")


@pytest.mark.dependency(depends=["test_device_inventory", "test_device_configuration", "test_device_valid_firmware_update"])
def test_device_decomissioning(dut: DeviceAdapter):
    """Get the MAC address of the device."""
    mac_address = helpers.get_device_mac_address(dut)
    """Ensure the device is authorized on the mender server."""
    helpers.assert_device_authenticated(dut)
    device = mender_management.get_device_by_mac(mac_address)
    assert device is not None, f"Device with MAC '{mac_address}' not found on mender server"
    assert device["status"] == "accepted", f"Device with MAC '{mac_address}' has unexpected status '{device["status"]}'"
    print("✅ Device has status 'accepted' on the mender server")
    """Decomissioning of the device on the server."""
    mender_management.delete_device(device)
    """Ensure the device is not authorized to the mender server."""
    helpers.assert_device_not_authenticated(dut)
    print("✅ Device decomissioning done successfully on the mender server")
