# @file      power.py
# @brief     Control power of boards
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
import sys


def run_uhubctl(location: str, port: str, action: str) -> None:
    server = os.getenv("USBPOWER_SERVER", "server")
    username = os.getenv("USBPOWER_USERNAME", "username")
    password = os.getenv("USBPOWER_PASSWORD", "password")
    subprocess.run(
        [
            "sshpass",
            "-p",
            password,
            "ssh",
            "-oStrictHostKeyChecking=no",
            f"{username}@{server}",
            "sudo",
            "/usr/sbin/uhubctl",
            "-l",
            location,
            "-p",
            port,
            "-a",
            action,
        ],
        check=True,
    )


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "Usage: power.py <on|off> <location,port> [<location,port> ...]",
            file=sys.stderr,
        )
        return 1

    action = sys.argv[1]

    if action not in ("on", "off"):
        print(f"Invalid action: {action}", file=sys.stderr)
        return 1

    ports = []

    for arg in sys.argv[2:]:
        location, port = arg.split(",", 1)
        ports.append((location, port))

    if action == "on":
        for location, port in ports:
            print(f"🔌 Power ON device on uhubctl at location {location}:{port}")
            run_uhubctl(location, port, "on")

    else:
        for location, port in reversed(ports):
            print(f"🔌 Power OFF device on uhubctl at location {location}:{port}")
            run_uhubctl(location, port, "off")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
