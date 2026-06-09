# @file      conftest.py
# @brief     conftest pytest file
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
import subprocess
import pytest
from twister_harness import DeviceAdapter


def run_uhubctl(location, port, action):
    server = os.getenv("USBPOWER_SERVER", "server")
    username = os.getenv("USBPOWER_USERNAME", "username")
    password = os.getenv("USBPOWER_PASSWORD", "password")
    try:
        result = subprocess.run(["sshpass", "-p", password, "ssh", "-oStrictHostKeyChecking=no", f"{username}@{server}", "sudo", "/usr/sbin/uhubctl", "-l", location, "-p", port, "-a", action,], text=True, capture_output=True, check=True)
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Return code: {e.returncode}")
        print("STDOUT:")
        print(e.stdout)
        print("STDERR:")
        print(e.stderr)
        # TODO CLEANUP
        raise


def get_uhubctl_ports(dut: DeviceAdapter) -> list[tuple[str, str]]:
    ports = []
    for param in dut.device_config.runner_params:
        if param.startswith("--uhubctl="):
            value = param.removeprefix("--uhubctl=")
            location, port = value.split(",", maxsplit=1)
            ports.append((location, port))
    return ports


@pytest.fixture(autouse=True)
def powered_target(dut: DeviceAdapter):
    # TODO CLEAN
    print(f"DEV_CONF={dut.device_config}")
    ports = get_uhubctl_ports(dut)
    print(f"DEV_PORTS={ports}")
    if not ports:
        yield dut
        return
    for location, port in ports:
        print(f"🔌 Power ON {dut.device_config.platform} located on uhubctl at {location}:{port}")
        run_uhubctl(location, port, "on")
    try:
        yield dut
    finally:
        for location, port in reversed(ports):
            print(f"🔌 Power OFF {dut.device_config.platform} located on uhubctl at {location}:{port}")
            run_uhubctl(location, port, "off")
