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

import re
import subprocess
import time
from pathlib import Path
from twister_harness import DeviceAdapter
from twister_harness.helpers.utils import match_no_lines


class Helpers:
    """
    Provides helper methods for device management.
    """

    def get_device_mac_address(self, dut: DeviceAdapter) -> str:
        output = dut.readlines_until(".*<inf>.*MAC address of the device '.*'", timeout=60)
        m = re.search(".*<inf>.*MAC address of the device '(.+?)'", output[-1])
        if m:
            mac_address = m.group(1)
        else:
            raise AssertionError("🔴​​​ MAC address of the device not found")
        print(f"✅ MAC address of the device is '{mac_address}'")
        return mac_address

    def assert_device_not_authenticated(self, dut: DeviceAdapter) -> None:
        try:
            output = dut.readlines_until(r".*<err>.*\[401\] Unauthorized.*|.*<inf>.*Mender client authenticated.*", timeout=300)
            match_no_lines(output[-1:], ["Mender client authenticated"])
        except (twister_harness.exceptions.TwisterHarnessTimeoutException, AssertionError):
            raise AssertionError("🔴​​​ Device appear to be authenticated but it should not")
        print("✅ Device is not authenticated")

    def assert_device_authenticated(self, dut: DeviceAdapter) -> None:
        try:
            output = dut.readlines_until("Mender client authenticated", timeout=300)
            match_no_lines(output[-1:], [r"\[401\] Unauthorized"])
        except (twister_harness.exceptions.TwisterHarnessTimeoutException, AssertionError):
            raise AssertionError("🔴​​​ Device doesn't appear to be authenticated but it should")
        print("✅ Device is authenticated")

    def create_mender_artifact(self, build_dir: Path, key_file: Path, device_type: str, artifact_name_prefix: str, version: str) -> Path:
        # Sign binary using west sign (key file is optional)
        cmd = f"west sign --tool imgtool --build-dir {build_dir} -- --version {version}"
        if key_file.is_file():
            cmd.append(f" --key {key_file}")
        subprocess.run(cmd, shell=True, check=True)
        # Create artifact using mender-artifact
        zephyr_signed_bin = Path(build_dir) / "zephyr" / "zephyr.signed.bin"
        artifact_file = Path(build_dir) / "zephyr" / f"{artifact_name_prefix}-v{version}.mender"
        cmd = f"mender-artifact write rootfs-image --compression none --device-type {device_type} --artifact-name {artifact_name_prefix}-v{version} --output-path {artifact_file} --file {zephyr_signed_bin}"
        subprocess.run(cmd, shell=True, check=True)
        return artifact_file

    def run_until(self, f, timeout: int, interval: int):
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = f()
            if result != None:
                return result
            time.sleep(interval)
        return None