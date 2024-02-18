#!/bin/bash

set -euo pipefail
set -x

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

DOCKER_BUILDKIT=1 docker build "${DIR}"
image=$(DOCKER_BUILDKIT=1 docker build -q "${DIR}")

# Clean up the build directory
rm -rf "${DIR}/../docs/build"

docker run -it --rm -v "${DIR}/..:/app" "${image}" \
  /bin/bash -c "cd /app/docs && python -m sphinx -T ./source ./build/html"
