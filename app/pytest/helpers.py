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
            raise AssertionError(f"🔴​​​ MAC address of the device not found")
        print(f"✅ MAC address of the device is '{mac_address}'")
        return mac_address

    def assert_device_not_authenticated(self, dut: DeviceAdapter) -> None:
        try:
            output = dut.readlines_until(r".*<err>.*\[401\] Unauthorized.*|.*<inf>.*Mender client authenticated.*", timeout=300)
            match_no_lines(output[-1:], ["Mender client authenticated"])
        except (twister_harness.exceptions.TwisterHarnessTimeoutException, AssertionError):
            raise AssertionError(f"🔴​​​ Device appear to be authenticated but it should not")
        print("✅ Device is not authenticated")

    def assert_device_authenticated(self, dut: DeviceAdapter) -> None:
        try:
            output = dut.readlines_until("Mender client authenticated", timeout=300)
            match_no_lines(output[-1:], ["\[401\] Unauthorized"])
        except (twister_harness.exceptions.TwisterHarnessTimeoutException, AssertionError):
            raise AssertionError(f"🔴​​​ Device doesn't appear to be authenticated but it should")
        print("✅ Device is authenticated")
