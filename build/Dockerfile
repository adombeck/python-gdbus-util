FROM python

RUN --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y \
    libgirepository1.0-dev \
    libsystemd-dev

RUN --mount=type=cache,target=/root/.cache \
    pip install --upgrade \
    hatch \
    twine \
    sphinx \
    sphinx_rtd_theme \
    readthedocs-sphinx-ext \
    PyGObject \
    cysystemd
