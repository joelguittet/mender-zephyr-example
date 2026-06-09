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

import subprocess
import pytest
from twister_harness import DeviceAdapter


def run_uhubctl(location, port, action):
    subprocess.run(["uhubctl", "-l", location, "-p", str(port), "-a", action,], check=True)


@pytest.fixture(autouse=True)
def powered_target(dut: DeviceAdapter):
    print(dut.device_config)
    location = "33-22"
    port = "1"
    run_uhubctl(location, port, "on")
    try:
        yield dut
    finally:
        run_uhubctl(location, port, "off")
