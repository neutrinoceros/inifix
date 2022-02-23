# `inifix`

[![PyPI](https://img.shields.io/pypi/v/inifix.svg?logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/inifix/)
[![PyPI](https://img.shields.io/pypi/pyversions/inifix/1.1.0?logo=python&logoColor=white&label=Python)](https://pypi.org/project/inifix/)
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
<details><summary>Unroll !</summary>
- parameter names are strings
- names and values are separated by non-newline white spaces
- values are represented in unicode characters
- all values are considered numbers if possible (e.g., `1e3` is read as `1000`)
- number values are read as integers if no loss of precision ensues, and floats otherwise
- `true` and `false` are cast as booleans (case-insensitive)
- values that can't be read as number or booleans are read as strings.
- string delimiters `"` and `'` can be used to force string type for values that would otherwise be read as numbers and booleans.
- a parameter can be associated to a single value or a list of whitespace-separated values
- sections titles start with `[` and end with `]`
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
x   1 2 u 10    # a comment
y   4 5 l 100
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
The following section-less format doesn't comply to Pluto/Idefix's
specifications, but it is considered valid for inifix. This is the one
intentional differences in specifications, which makes inifix format a superset
of Pluto's inifile format.
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
as `1e5`, but `10` is left unchanged because `1e1` is longer.
In cases where both reprensations are equally compact (e.g. `100` VS `1e2`),
e-notation is prefered in encoding.

While decoding, `e` can be lower or upper case, but they are always encoded as
lower case.
</details>

## Installation

```shell
pip install inifix
```

## Usage

The public API mimicks that of Python's standard library `json`,
and consists in two main functions: `inifix.load` and `inifix.dump`.


### Reading data
`inifix.load` reads from a file and returns a `dict`

```python
import inifix

with open("pluto.ini") as fh:
    conf = inifix.load(fh)

# or equivalently
conf = inifix.load("pluto.ini")
```

### ... and writing back to disk

`inifix.dumps` allows to write back to a file.

This allows to change a value on the fly and create new
configuration files programmatically, for instance.
```python
conf["Time"]["CFL"] = 0.1
inifix.dump(conf, "pluto-mod.ini")
```
Data will be validated against inifix's format specification at write time.

### Schema Validation

`inifix.validate_inifile_schema` can be used to validate an arbitrary
dictionary as writable to an inifile, following Pluto/Idefix's format. This
will raise an exception (`ValueError`) if the dictionnary `data` is invalid.
```python
inifix.validate_inifile_schema(data)
```

### CLI

Command line tool are shipped with the package to validate or format compatible inifiles.

#### Validation

This checks that your inifiles can be loaded with `inifix.load` from the command line
```shell
$ inifix-validate pluto.ini
Validated pluto.ini
```

This simple validator can be used as a hook for `pre-commit`. Simply add the
following to your project's `.pre-commit-config.yaml`
```yaml
  - repo: https://github.com/neutrinoceros/inifix.git
    rev: v0.10.0
    hooks:
      - id: inifix-validate
```

#### Formatting

To format a file in place, use
```shell
$ inifix-format pluto.ini
```


#### Options

Note that comments are preserved in all cases.
* To print a diff patch to stdout instead, pass the `--diff` flag
```shell
$ inifix-format pluto.ini --diff
```
* Use `--name-column-size <n>` to specify the length of the first column (including right padding).
Names longer this value will not be aligned, but whitespace separating them from values will be minimised.

This program also doubles as `pre-commit` hook
```yaml
  - repo: https://github.com/neutrinoceros/inifix.git
    rev: v0.10.0
    hooks:
      - id: inifix-format
```
## Contribution guidelines

We use the [pre-commit](https://pre-commit.com) framework to automatically lint for code
style and common pitfalls.

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
