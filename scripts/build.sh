#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/.build"

echo "[*] Packaging Ingress Lambda..."
mkdir -p "${BUILD_DIR}/ingress"
pip install \
  --platform manylinux2014_x86_64 \
  --target "${BUILD_DIR}/ingress" \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: \
  --upgrade \
  -r "${ROOT_DIR}/src/ingress/requirements.txt" || \
pip install \
  --target "${BUILD_DIR}/ingress" \
  --upgrade \
  -r "${ROOT_DIR}/src/ingress/requirements.txt"

cp "${ROOT_DIR}/src/ingress/handler.py" "${BUILD_DIR}/ingress/"

(cd "${BUILD_DIR}/ingress" && zip -r -q "${BUILD_DIR}/ingress.zip" .)
echo "[+] Ingress packaged at ${BUILD_DIR}/ingress.zip"

echo "[*] Packaging Worker Lambda..."
mkdir -p "${BUILD_DIR}/worker"
pip install \
  --target "${BUILD_DIR}/worker" \
  --upgrade \
  -r "${ROOT_DIR}/src/worker/requirements.txt" || true

cp "${ROOT_DIR}/src/worker/"*.py "${BUILD_DIR}/worker/"

(cd "${BUILD_DIR}/worker" && zip -r -q "${BUILD_DIR}/worker.zip" .)
echo "[+] Worker packaged at ${BUILD_DIR}/worker.zip"

echo "[+] Build complete!"
