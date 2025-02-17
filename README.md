# Python Nillion client

Nillion-client is a Python client for building on top of the Nillion Network.
It can be used to manage Nada programs, store and retrieve values, and run
computations.

See the official Nillion documentation site for more about [Nillion
Clients][clients], [Python Client Examples][examples] and the [Python Client
Reference][reference].

[clients]: https://docs.nillion.com/nillion-client

[examples]: https://docs.nillion.com/python-client-examples

[reference]: https://docs.nillion.com/python-client-reference

## How to develop

This project uses [uv](https://docs.astral.sh/uv/) to manage itself.
Be sure that you have it installed. 


To install dependencies and setup project
```shell
uv sync
```

### Run tests
First ensure that you have the nillion-devnet running
```shell
./tests/resources/scripts/run_devnet.sh
```

Then in a new terminal
```
uv run pytest
```

### Format code and Linting
This project uses [ruff](https://docs.astral.sh/ruff/) as linter and formatter, it gets installed as a dependency. 

To format code:
```shell
uv run ruff format
```

To lint:
```shell
uv run ruff check
```

## Generating docs

In order to generate the documentation first install the dependencies and set up the project:


```shell
uv sync
```

Then activate the virtual environment:

```shell
source .venv/bin/activate

# Use .venv/bin/activate.fish if you're using fish shell
```

And finally run:

```shell
./docs/generate.sh output_directory
```

The docs will be generated in `output_directory`.


## Release Process

### Release Candidates
Release candidates are published on every merge to the `main` branch

### Stable Releases

To release a new version of the client non rc, follow these steps:

run:

```shell
just release
```

and bump the version in the `pyproject.toml` file for the new rc.