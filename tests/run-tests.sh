#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

# Install the package in a virtual environment
python3 -m venv --system-site-packages "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install "${SCRIPT_DIR}/.."

# Activate the virtual environment
source "${VENV_DIR}/bin/activate"

# Run the tests
"${VENV_DIR}/bin/python3" "$(command -v behave)" "${SCRIPT_DIR}"
