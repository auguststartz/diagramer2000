#!/usr/bin/env python3
"""Download official AWS Architecture Icons and extract EC2, RDS, FSx PNGs."""

import io
import shutil
import zipfile
from pathlib import Path
from urllib.request import urlopen

ICON_URL = (
    "https://d1.awsstatic.com/onedam/marketing-channels/website/aws/en_US/"
    "architecture/approved/architecture-icons/"
    "Icon-package_01302026.31b40d126ed27079b708594940ad577a86150582.zip"
)

DEST_DIR = Path(__file__).resolve().parent.parent / "app" / "icons" / "aws"

# Exact paths inside the ZIP for the 64@5x (high-res) variants.
# These are the generic service icons (not sub-service variants).
TARGETS = {
    "ec2.png": "Architecture-Service-Icons_01302026/Arch_Compute/64/Arch_Amazon-EC2_64@5x.png",
    "rds.png": "Architecture-Service-Icons_01302026/Arch_Databases/64/Arch_Amazon-RDS_64@5x.png",
    "fsx.png": "Architecture-Service-Icons_01302026/Arch_Storage/64/Arch_Amazon-FSx_64@5x.png",
}


def main() -> None:
    print(f"Downloading AWS icon pack from:\n  {ICON_URL}")
    with urlopen(ICON_URL) as resp:
        data = resp.read()
    print(f"  Downloaded {len(data) / 1_048_576:.1f} MB")

    zf = zipfile.ZipFile(io.BytesIO(data))
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    for out_name, zip_path in TARGETS.items():
        if zip_path not in zf.namelist():
            print(f"  WARNING: {zip_path} not found in archive, skipping {out_name}")
            continue

        dest_path = DEST_DIR / out_name
        with zf.open(zip_path) as src, open(dest_path, "wb") as dst:
            shutil.copyfileobj(src, dst)
        print(f"  {out_name} <- {zip_path}")

    print("Done. Icons saved to:", DEST_DIR)


if __name__ == "__main__":
    main()
