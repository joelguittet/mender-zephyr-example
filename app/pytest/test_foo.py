# @file      test_foo.py
# @brief     Foo test file
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
import json
import logging
import requests

from twister_harness import Shell
from twister_harness import DeviceAdapter

logger = logging.getLogger(__name__)

MENDER_SERVER_URL = os.getenv("MENDER_SERVER_URL", "https://docker.mender.io")
MENDER_USERNAME = os.getenv("MENDER_USERNAME", "MyAdminUser")
MENDER_PASSWORD = os.getenv("MENDER_PASSWORD", "MySecretPassword")
MENDER_CRT_PATH = os.getenv("MENDER_CRT_PATH", "path/to/mender.crt")

@pytest.fixture(scope="session")
def mender_token():
    """Authenticate and return JWT token."""
    url = f"{MENDER_SERVER_URL}/api/management/v1/useradm/auth/login"
    payload = {"username": MENDER_USERNAME, "password": MENDER_PASSWORD}
    response = requests.post(url, json=payload, verify=MENDER_CRT_PATH)
    response.raise_for_status()
    return response.text.strip()

@pytest.fixture(scope="session")
def mender_headers(mender_token):
    return {"Authorization": f"Bearer {mender_token}"}

def find_device_by_mac(headers, mac_address):
    """Find device and its auth set by MAC address."""
    url = f"{MENDER_SERVER_URL}/api/management/v2/devauth/devices"
    r = requests.get(url, headers=headers, verify=MENDER_CRT_PATH)
    r.raise_for_status()
    devices = r.json()

    for dev in devices:
        try:
            identity = json.loads(dev["identity_data"])
            if identity.get("mac") == mac_address:
                # return both device id and auth id, plus device status
                # TODO keep like that or just return the device, then extract expectd info with dedicated function: should be better
                auth_sets = dev.get("auth_sets", [])
                if not auth_sets:
                    raise ValueError(f"Device {dev['id']} has no auth sets")
                # normally only one auth_set
                auth_id = auth_sets[0]["id"]
                return dev["id"], auth_id, dev["status"]
        except (KeyError, json.JSONDecodeError):
            continue
    return None, None

def accept_device_by_mac(mac_address):
    """Accept a device given its MAC address."""
    token = mender_login()
    headers = {"Authorization": f"Bearer {token}"}

    device_id, auth_id = find_device_by_mac(headers, mac_address)
    if not device_id:
        raise ValueError(f"No device found with MAC {mac_address}")

    url = f"{MENDER_SERVER_URL}/api/management/v2/devauth/devices/{device_id}/auth/{auth_id}/status"
    payload = {"status": "accepted"}
    r = requests.put(url, headers=headers, json=payload, verify=MENDER_CRT_PATH)
    r.raise_for_status()

    logger.info(f"✅ Device {device_id} ({mac_address}) accepted successfully.")
    return True

def test_device_registration(dut: DeviceAdapter):

    # Get device
    # TODO get MAC from command line
    mac = "00:08:dc:01:02:03"
    # TODO with timeout and not 'Mender client authenticated'
    dut.readlines_until('.*<err>.*\[401\] Unauthorized: Unauthorized.*')
    device_id, auth_id, device_status = find_device_by_mac(mender_headers, mac)
    assert device_id is not None, f"Device with MAC {mac} not found"
    logger.info(f"Found device ID: {device_id} status={device_status}")
    # TODO check status is not auth assert...
    # Accept the device
    accept_device_by_mac(mac)
    # TODO with timeout and not Unauthorized
    dut.readlines_until('Mender client authenticated')
    dut.readlines_until('No deployment available')
