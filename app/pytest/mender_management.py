import os
import json
import time
import requests

class MenderManagement:
    """
    Wrapper around Mender Management API (v1/v2).
    Provides methods for device management and deployments.
    """

    def __init__(self,
                 server=None,
                 username=None,
                 password=None,
                 ca_cert=None):
        self.server = server or os.getenv("MENDER_SERVER", "https://mender.mycompany.local")
        self.username = username or os.getenv("MENDER_USER", "admin@mycompany.local")
        self.password = password or os.getenv("MENDER_PASS", "MySecretPassword")
        self.ca_cert = ca_cert or os.getenv("MENDER_CA", "/etc/ssl/certs/my-ca.crt")

        self.token = None
        self.headers = None
        self.login()

    # -----------------------------
    # Authentication
    # -----------------------------
    def login(self):
        """Authenticate to Mender Management API and store JWT token."""
        url = f"{self.server}/api/management/v1/useradm/auth/login"
        resp = requests.post(url,
                             auth=HTTPBasicAuth(self.username, self.password),
                             verify=self.ca_cert)
        resp.raise_for_status()
        self.token = resp.text.strip()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    # -----------------------------
    # Devices
    # -----------------------------
    def list_devices(self):
        """Return all devices."""
        url = f"{self.server}/api/management/v2/devauth/devices"
        r = requests.get(url, headers=self.headers, verify=self.ca_cert)
        r.raise_for_status()
        return r.json()

    def get_device_by_mac(self, mac_address):
        """Return a single device and auth_set by MAC address."""
        devices = self.list_devices()
        for dev in devices:
            try:
                identity = json.loads(dev["identity_data"])
                if identity.get("mac") == mac_address:
                    auth_sets = dev.get("auth_sets", [])
                    if not auth_sets:
                        raise RuntimeError(f"Device {dev['id']} has no auth sets")
                    return dev, auth_sets[0]
            except (KeyError, json.JSONDecodeError):
                continue
        return None, None

    def accept_device(self, mac_address):
        """Accept device by MAC."""
        device, auth = self.get_device_by_mac(mac_address)
        if not device:
            raise ValueError(f"No device found with MAC {mac_address}")

        url = f"{self.server}/api/management/v2/devauth/devices/{device['id']}/auth/{auth['id']}/status"
        payload = {"status": "accepted"}
        r = requests.put(url, headers=self.headers, json=payload, verify=self.ca_cert)
        r.raise_for_status()
        return True

    def reject_device(self, mac_address):
        """Reject (deny) a device by MAC."""
        device, auth = self.get_device_by_mac(mac_address)
        if not device:
            raise ValueError(f"No device found with MAC {mac_address}")

        url = f"{self.server}/api/management/v2/devauth/devices/{device['id']}/auth/{auth['id']}/status"
        payload = {"status": "rejected"}
        r = requests.put(url, headers=self.headers, json=payload, verify=self.ca_cert)
        r.raise_for_status()
        return True

    # -----------------------------
    # Deployments
    # -----------------------------
    def upload_artifact(self, filepath, description=None):
        """Upload a new artifact (deployment package)."""
        url = f"{self.server}/api/management/v1/deployments/artifacts"
        files = {
            "artifact": open(filepath, "rb"),
        }
        data = {}
        if description:
            data["description"] = description

        r = requests.post(url, headers=self.headers, files=files, data=data, verify=self.ca_cert)
        r.raise_for_status()
        return r.json()

    def create_deployment(self, name, artifact_name, device_ids):
        """Create a deployment for one or more devices."""
        url = f"{self.server}/api/management/v1/deployments/deployments"
        payload = {
            "name": name,
            "artifact_name": artifact_name,
            "devices": device_ids
        }
        r = requests.post(url, headers=self.headers, json=payload, verify=self.ca_cert)
        r.raise_for_status()
        return r.json()

    def get_deployments(self):
        """Return list of all deployments."""
        url = f"{self.server}/api/management/v1/deployments/deployments"
        r = requests.get(url, headers=self.headers, verify=self.ca_cert)
        r.raise_for_status()
        return r.json()

    def get_deployment_status(self, deployment_id):
        """Get status of a deployment."""
        url = f"{self.server}/api/management/v1/deployments/deployments/{deployment_id}"
        r = requests.get(url, headers=self.headers, verify=self.ca_cert)
        r.raise_for_status()
        return r.json()

    def wait_for_deployment_success(self, deployment_id, timeout=600, interval=10):
        """Wait until deployment completes or fails."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            status = self.get_deployment_status(deployment_id)
            state = status.get("status")
            if state in ("finished", "success", "failure", "aborted"):
                return state
            time.sleep(interval)
        raise TimeoutError(f"Deployment {deployment_id} did not complete within {timeout}s")

