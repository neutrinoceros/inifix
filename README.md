# `inifix`

[![PyPI](https://img.shields.io/pypi/v/inifix)](https://pypi.org/project/inifix/)
![PyPI](https://img.shields.io/pypi/pyversions/inifix/0.6.0?logo=python&logoColor=white&label=Python)
[![codecov](https://codecov.io/gh/neutrinoceros/inifix/branch/main/graph/badge.svg)](https://codecov.io/gh/neutrinoceros/inifix)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/neutrinoceros/inifix/main.svg)](https://results.pre-commit.ci/badge/github/neutrinoceros/inifix/main.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


`inifix` in a small Python library with I/O methods to read and write
Pluto/Idefix inifiles as Python dictionaries.

Its primary goal is to support Idefix's model (which is intended as identical to
Pluto's), though the following file format specification is intended as a
superset of the one used in Pluto and Idefix. Namely, while Pluto and Idefix
require that each and every (key, value) pair be part of a section, `inifix`
supports section-free definitions.


## File format specifications

- parameter names are strings
- parameter names and values are separated by white spaces
- values can be an integers, floats, booleans, or strings
- a parameter can be associated to a single value or a set of space-separated value
- optionally, the file can be separated into sections, whose names match this regexp `"$[\.+]"`
- comments start with `#` and are ignored

Using the following Python's `typing` notations
```python
from typing import Union, Mapping
Scalar = Union[str, float, bool, int]
InifixConf = Mapping[str, Union[Scalar, Mapping[str, Scalar]]
```
A configuration file is considered valid if it can be parsed as an `InifixConf` object.

### Examples
The following content is considered valid
```ini
# My awesome experiment
[Grid]
x   1 2 "u" 10    # a comment
y   4 5 "l" 100
[Time Integrator]
CFL  1e-3
tstop 1E3
```
and maps to
```json
{
    "Grid": {
        "x": [1, 2, "u", 10],
        "y": [4, 5, "l", 100]
    },
    "Time Integrator": {
        "CFL": 0.001,
        "tstop": 1000
    }
}
```
The following is also considered valid
```ini
mode   fargo

# Time integrator
CFL    1e-3
tstop  1e3
```
and maps to
```json
{
    "mode": "fargo",
    "CFL": 0.001,
    "tstop": 1000
}
```
Note that strings using e-notation (e.g. `1e-3` or `1E3` here) are decoded as
numbers. They are cast to `int` if no precision loss ensues, and `float`
otherwise. Reversly, when writing files, numbers are re-encoded using e-notation
if it leads to a more compact representation. For instance, `100000` is encoded
as `1e5`, but `10` is left unchanged because `1e1` also uses one more character.
In case where both reprensations are equally compact (e.g. `100` VS `1e2`),
e-notation is prefered in encoding.

While decoding, `e` can be lower or upper case, but they are also encoded as
lower case.

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
conf["Time"]["CFL"] = 0.1

# write back
inifix.dump(conf, "pluto-mod.ini")
```

`inifix.load` supports loading from an open file
```python
with open("pluto.ini") as fh:
    conf = inifix.load(fh)
```
or from a `str/os.PathLike` object representing a file.


### Schema Validation

`inifix.validate_inifile_schema` can be used to validate an aribitrary
dictionary as writable to an inifile, following Pluto/Idefix's format. This
will raise an exception (`ValueError`) if the dictionnary `data` is invalid.
```python
inifix.validate_inifile_schema(data)
```

### File formatter

A small command line tool is shipped with the package to format compatible inifiles.

This will print a formatted verison of the input file to `stdout`
```shell
$ inifix-format pluto.ini
```
In can be redirected as
```shell
$ inifix-format pluto.ini > pluto-formatted.ini
```
Use the `-i/--inplace` flag to write back to the source file.
Note that comments are preserved in all cases.

This program can also be used as a hook for `pre-commit`. Simply add the following to your
project's `.pre-commit-config.yaml`
```yaml
  - repo: https://github.com/neutrinoceros/inifix.git
    rev: v0.5.1
    hooks:
      - id: inifix-format
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
