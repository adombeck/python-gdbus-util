#!/bin/bash

set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Uploading fails if the dist directory contains old releases
rm -rf "${DIR}/../dist"

DOCKER_BUILDKIT=1 docker build "${DIR}"
image=$(DOCKER_BUILDKIT=1 docker build -q "${DIR}")
docker run -it --rm -v "${DIR}/..:/app" "${image}" \
  /bin/bash -c "cd /app &&
  hatch build &&
  python3 -m twine upload --repository pypi dist/*"
