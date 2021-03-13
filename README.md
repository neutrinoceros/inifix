# `inifix`

![PyPI](https://img.shields.io/pypi/v/inifix)
![PyPI](https://img.shields.io/pypi/pyversions/inifix?logo=python&logoColor=white&label=Python)
[![codecov](https://codecov.io/gh/neutrinoceros/inifix/branch/main/graph/badge.svg)](https://codecov.io/gh/neutrinoceros/inifix)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/neutrinoceros/inifix/main.svg)](https://results.pre-commit.ci/badge/github/neutrinoceros/inifix/main.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)


`inifix` in a small Python library with I/O methods to read and write Idefix (or Pluto) inifiles as Python dictionaries.

## Installation

```shell
$ pip install inifix
```

## Usage

The API is similar to that of `toml` and stdlib `json`, though intentionally
simplified, and consists in two main user-facing functions: `inifix.load` and
`inifix.dump`.

```python
import inifix

# read
conf = inifix.load("pluto.ini")

# patch
conf["Time"].update({"CFL": 0.1})

# write back
inifix.dump(conf, "pluto-mod.ini")
```

`inifix.load` supports loading a from an open file
```python
with open("pluto.ini") as fh:
    conf = inifix.load(fh)
```
or from a str/os.Pathlike object representing a file.


### Schema Validation

`inifix.validate_inifile_schema` can be used to validate an aribitrary
dictionnary as writable to an inifile, following Pluto/Idefix's format. This
will raise an exception (`ValueError`) if the dictionnary `data` is invalid.
```python
inifix.validate_inifile_schema(data)
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
