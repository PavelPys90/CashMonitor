
import json
import base64
from pathlib import Path
from typing import Optional, Dict

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

from utils import get_app_dir

# Embed Public Key here (from generate_keys.py output)
PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAty+myD4zgg8SruKIk1Wp
pKz5EPVCpZrz+3BMHwa+mdIhuTNi68p4s0WArh+DxX7DKxKh/THy+Rr9uW2QJCrM
fRCLvPYhgk5XxMbtm5+SGzYeIn2woswuLoJyo0PLfAe84LooziPRRIlE4XOOG/KF
jiVclwOKhb63TWtOprzb+9FRkwE7sUVjUtkbeFHYtQgf/6GpZ3dTaNbjnfCJg+AF
6+Y2yV6BQ3Cu/91lk/gXV/SoQaiJCDZiK3n8Y0vf002xPpxYE3kVeD1F1JwgjlxP
L896o/gdExahfAny3H60F67tvmM1lHdMHTQfyjdXaxfuMdIp/LxrWWphMwXZWNCf
uQIDAQAB
-----END PUBLIC KEY-----"""

LICENSE_FILE_NAME = "license.dat"


class LicenseManager:
    def __init__(self):
        self.app_dir = get_app_dir()
        self.license_path = self.app_dir / LICENSE_FILE_NAME
        self.public_key = serialization.load_pem_public_key(PUBLIC_KEY_PEM)
        self.license_data: Optional[Dict] = None

    def load_license(self) -> bool:
        """
        Load and verify the license file.
        Returns True if valid, False otherwise.
        """
        if not self.license_path.exists():
            return False

        try:
            with open(self.license_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            signature_b64 = data.get("signature")
            if not signature_b64:
                return False

            signature = base64.b64decode(signature_b64)

            # Create verify payload (same as data but without signature)
            verify_data = data.copy()
            del verify_data["signature"]
            
            # Canonical JSON dump for verification
            payload = json.dumps(verify_data, sort_keys=True).encode("utf-8")

            # Verify
            self.public_key.verify(
                signature,
                payload,
                padding.PKCS1v15(),
                hashes.SHA256()
            )

            self.license_data = verify_data
            return True

        except (json.JSONDecodeError, InvalidSignature, Exception) as e:
            print(f"License verification failed: {e}")
            return False

    def get_info(self) -> str:
        if self.license_data:
            return f"Lizenziert für: {self.license_data.get('owner', 'Unknown')}"
        return "Keine gültige Lizenz"

    def install_license(self, source_path: Path) -> bool:
        """Copy a license file to the app directory and verify it."""
        try:
            # First verify the source file
            temp_lm = LicenseManager()
            temp_lm.license_path = source_path
            if not temp_lm.load_license():
                return False
            
            # If valid, copy it
            with open(source_path, "r", encoding="utf-8") as src:
                content = src.read()
            
            with open(self.license_path, "w", encoding="utf-8") as dst:
                dst.write(content)
                
            return self.load_license()
        except Exception:
            return False
