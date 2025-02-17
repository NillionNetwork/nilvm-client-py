
sync:
    uv sync --all-extras --dev --prerelease=allow

######### FORMATTING #########
python-format:
    uv run ruff format

python-format-check:
    uv run ruff format --check

rust-format:
    cd client-core && cargo fmt

rust-format-check:
    cd client-core && cargo fmt --check

format: python-format rust-format

###### TYPE CHECKING ######
python-type-check:
    uv run pyright

clippy:
    #!/bin/bash -e
    . ./.venv/bin/activate
    cd client-core
    cargo clippy -- -D warnings

###### TESTS ######
test-client-core:
    #!/bin/bash -e
    uv run pytest --junit-xml=client-core.junit.xml client-core/tests/tests.py



test-client run-devnet="":
    #!/bin/bash -e
    [[ "{{run-devnet}}" == "run-devnet" ]] && ./tests/resources/scripts/run_devnet.sh background
    uv run pytest --junit-xml=client.junit.xml tests

test-rc-packages run-devnet="":
    ./scripts/test-rc-packages.sh "{{run-devnet}}"

###### Package ######
package:
    ./scripts/package.sh

###### Docker ######
docker-build:
    docker build -t python-client-builder -f builder.dockerfile .

docker-publish:
   ./scripts/docker-publish.sh
