#!/usr/bin/env python3
"""Build and package script for Lambda functions.

Packages Ingress and Worker Lambda functions into standalone zip archives.
Uses standard Python libraries so it runs anywhere without external `zip` CLI dependencies.
"""

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT_DIR / ".build"


def zip_directory(source_dir: Path, output_zip: Path):
    """Zip the contents of a directory."""
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(source_dir)
                z.write(file_path, arcname)
    print(f"[+] Created zip: {output_zip} ({output_zip.stat().st_size / 1024 / 1024:.2f} MB)")


def build_ingress():
    print("[*] Building Ingress Lambda...")
    pkg_dir = BUILD_DIR / "ingress"
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Install dependencies (pynacl)
    req_file = ROOT_DIR / "src" / "ingress" / "requirements.txt"
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--target",
        str(pkg_dir),
        "--upgrade",
        "-r",
        str(req_file),
    ]
    subprocess.check_call(cmd)

    # Copy source code
    shutil.copy2(ROOT_DIR / "src" / "ingress" / "handler.py", pkg_dir / "handler.py")

    # Clean up unnecessary files to reduce zip size
    for item in pkg_dir.rglob("__pycache__"):
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)
    for item in pkg_dir.glob("*.dist-info"):
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)

    # Zip
    zip_directory(pkg_dir, BUILD_DIR / "ingress.zip")


def build_worker():
    print("[*] Building Worker Lambda...")
    pkg_dir = BUILD_DIR / "worker"
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Worker only uses standard libraries and boto3 (provided by Lambda runtime)
    # Copy all worker source files
    worker_src = ROOT_DIR / "src" / "worker"
    for py_file in worker_src.glob("*.py"):
        shutil.copy2(py_file, pkg_dir / py_file.name)

    # Zip
    zip_directory(pkg_dir, BUILD_DIR / "worker.zip")


def main():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    build_ingress()
    build_worker()
    print("[+] All Lambda packages built successfully!")


if __name__ == "__main__":
    main()
