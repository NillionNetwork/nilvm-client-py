# Python Nillion client core bindings

Python bindings for the client core. Dependency of the Nillion Python client.

This project is using [Maturin](https://github.com/PyO3/maturin) to generate the Python wheel.

There are four main commands:

* `maturin new` creates a new cargo project with Maturin configured.
* `maturin publish` builds the crate into python packages and publishes them to pypi.
* `maturin build` builds the wheel and stores it in a folder (`target/wheels` by default), but doesn't upload it. It's possible to upload it with [twine](https://github.com/pypa/twine) or `maturin upload`.
* `maturin develop` builds the crate and installs it as a python module directly in the current virtualenv. Note that while `maturin develop` is faster, it doesn't support all the feature that running `pip install` after `maturin build` supports.
