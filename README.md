[![codecov](https://codecov.io/gh/neutrinoceros/inifix/branch/main/graph/badge.svg)](https://codecov.io/gh/neutrinoceros/inifix)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/neutrinoceros/inifix/dev.svg)](https://results.pre-commit.ci/badge/github/neutrinoceros/inifix/dev.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

# `inifix`

`inifix` in a small Python library with I/O methods to read and write Idefix (or Pluto) inifiles as Python dictionaries.

## Installation

From the top level of the repo, run
```shell
$ python3 -m pip install -u -e .
```

## Usage

```python
import inifix

# read
conf = inifix.load("pluto.ini")

# patch
conf["Time"].update({"CFL": 0.1})

# write back
inifix.dump(conf, "pluto-mod.ini")
```

## Contribution guidelines

We use the [pre-commit](https://pre-commit.com) framework to automatically lint for code
style and common pitfals.

Before you commit to your local copy of the repo, please run this from the top level
```shell
$ python3 -m pip install -u -e .[dev]
$ pre-commit install
```

## Testing

We use the [pytest](https://docs.pytest.org/en/latest/) framework to test `inifix`.
The test suite can be run from the top level with a simple `pytest` invocation.
```shell
$ pytest
```
