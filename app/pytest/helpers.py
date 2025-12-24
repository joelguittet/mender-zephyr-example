# @file      helpers.py
# @brief     Helpers
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

import os
import re
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from twister_harness import DeviceAdapter
from twister_harness.exceptions import TwisterHarnessTimeoutException
from twister_harness.helpers.utils import match_no_lines


class Helpers:
    """
    Provides helper methods for device management.
    """

    def get_device_mac_address(self, dut: DeviceAdapter) -> str:
        try:
            output = dut.readlines_until(regex="MAC address of the device '[0-9A-Za-z:]+'", timeout=60)
        except (TwisterHarnessTimeoutException, AssertionError):
            raise AssertionError(f"🔴​​​ MAC address of the device not found")
        m = re.search(".*<inf>.*MAC address of the device '(.+?)'.*", output[-1])
        if m:
            mac_address = m.group(1)
        else:
            raise AssertionError("🔴​​​ MAC address of the device not found")
        print(f"✅ MAC address of the device is '{mac_address}'")
        return mac_address

    def get_device_firmware_version(self, dut: DeviceAdapter) -> str:
        try:
            output = dut.readlines_until(regex="Running project 'mender-zephyr-example' version '[0-9.+]+'", timeout=60)
        except (TwisterHarnessTimeoutException, AssertionError):
            raise AssertionError(f"🔴​​​ Firmware version of the device not found")
        m = re.search(".*<inf>.*Running project 'mender-zephyr-example' version '(.+?)'.*", output[-1])
        if m:
            fw_version = m.group(1)
        else:
            raise AssertionError("🔴​​​ Firmware version of the device not found")
        print(f"✅ Firmware version of the device is '{fw_version}'")
        return fw_version

    def assert_device_not_authenticated(self, dut: DeviceAdapter):
        try:
            output = dut.readlines_until(regex=r".*<err>.*\[401\] Unauthorized.*|.*<inf>.*Mender client authenticated.*", timeout=300)
            match_no_lines(output[-1:], ["Mender client authenticated"])
        except (TwisterHarnessTimeoutException, AssertionError):
            raise AssertionError("🔴​​​ Device appear to be authenticated but it should not")
        print("✅ Device is not authenticated")

    def assert_device_authenticated(self, dut: DeviceAdapter):
        try:
            #output = dut.readlines_until(regex=".*Mender client authenticated.*", timeout=300) # TODO check for unauthorized here ?
            output = dut.readlines_until(regex=r".*<err>.*\[401\] Unauthorized.*|.*<inf>.*Mender client authenticated.*", timeout=300)
            match_no_lines(output[-1:], [r"\[401\] Unauthorized"])
        except (TwisterHarnessTimeoutException, AssertionError):
            raise AssertionError("🔴​​​ Device doesn't appear to be authenticated but it should")
        print("✅ Device is authenticated")

    def assert_device_troubleshoot_connected(self, dut: DeviceAdapter):
        try:
            output = dut.readlines_until(regex="Troubleshoot client connected", timeout=300)
        except (TwisterHarnessTimeoutException, AssertionError):
            raise AssertionError("🔴​​​ Device troubleshoot doesn't appear to be connected but it should")
        print("✅ Device troubleshoot connected")

    def create_mender_artifact(self, build_dir: Path, key_file: Path, device_type: str, artifact_name_prefix: str, version: str) -> Path:
        # Sign binary using west sign (key file is optional)
        cmd = f"west sign --tool imgtool --build-dir {build_dir} -- --version {version}"
        if os.path.exists(key_file):
            cmd += f" --key {key_file}"
        subprocess.run(cmd, shell=True, check=True)
        # Create artifact using mender-artifact
        zephyr_signed_bin = Path(build_dir) / "zephyr" / "zephyr.signed.bin"
        artifact_file = Path(build_dir) / "zephyr" / f"{artifact_name_prefix}-v{version}.mender"
        cmd = f"mender-artifact write rootfs-image --compression none --device-type {device_type} --artifact-name {artifact_name_prefix}-v{version} --output-path {artifact_file} --file {zephyr_signed_bin}"
        subprocess.run(cmd, shell=True, check=True)
        return artifact_file

    def run_until_data_refreshed(self, f, timeout=600, interval=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            data, updated_ts = f()
            if data is not None and updated_ts is not None:
                delta = interval * 1.5
                if datetime.fromisoformat(updated_ts) > datetime.now(timezone.utc) - timedelta(seconds=delta):
                    return data
            time.sleep(interval)
        return None

    def run_until_data_available(self, f, timeout=600, interval=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            data = f()
            if data is not None:
                return data
            time.sleep(interval)
        return None
