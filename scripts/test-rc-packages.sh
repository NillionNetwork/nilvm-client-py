#!/bin/bash

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null)" && pwd -P)"

cd $SCRIPT_PATH/..

deactivate 2>/dev/null || true

uv venv --no-project --python=python3.10 ./.venv-rc-test
source ./.venv-rc-test/bin/activate
uv pip install --prerelease=allow -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ nillion-client --no-cache-dir
uv pip install pytest
uv pip install pytest-asyncio


./.venv-rc-test/bin/pytest --junit-xml=client-core.junit.xml client-core/tests/tests.py

[[ "$1" == "run-devnet" ]] && ./tests/resources/scripts/run_devnet.sh background
./.venv-rc-test/bin/pytest --junit-xml=client.junit.xml tests
