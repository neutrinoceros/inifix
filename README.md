# `inifix`

[![PyPI](https://img.shields.io/pypi/v/inifix.svg?logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/inifix/)
[![PyPI](https://img.shields.io/badge/requires-Python%20≥%203.8-blue?logo=python&logoColor=white)](https://pypi.org/project/inifix/)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/neutrinoceros/inifix/main.svg)](https://results.pre-commit.ci/badge/github/neutrinoceros/inifix/main.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


`inifix` is a small Python library of I/O functions to read and write 'ini'
configuration files in the style of [Pluto](http://plutocode.ph.unito.it) and
[Idefix](https://gricad-gitlab.univ-grenoble-alpes.fr/lesurg/idefix-public).

While its primary goal is to follow Idefix's 'ini' format specification, it
supports a small superset of it.

The key differences are:
- `inifix` supports section-free definitions. This means confifuration files
  from [FARGO 3D](https://fargo3d.bitbucket.io) are also supported.
- in `inifix`, strings can be escaped using `'` or `"`. This allows to have
  whitespaces in string values and to force string type decoding where numeric
  and boolean types would work.

In rare cases where Idefix's 'ini' format doesn't match Pluto's, `inifix` will
follow the former. Known differences are:
- Idefix allows booleans to be written as `yes` and `no`.
- Idefix allows integers to be written using scientific notation (e.g. `1e3`)

## File format specifications details
<details><summary>Unroll !</summary>
- parameter names are strings
- names and values are separated by non-newline white spaces
- values are represented in unicode characters
- all values are considered numbers if possible (e.g., `1e3` is read as `1000`)
- number values are read as integers if no loss of precision ensues, and floats otherwise
- `true` and `false` (resp. `yes` and `no`) are cast to booleans (case-insensitive)
- values that can't be read as number or booleans are read as strings.
- string delimiters `"` and `'` can be used for strings containing whitespace, or to
  force string type for values that would otherwise be read as numbers and booleans.
- a parameter can be associated to a single value or a list of whitespace-separated values
- sections titles start with `[` and end with `]`
- comments start with `#` and are ignored

A file is considered valid if calling `inifix.load(<filename>)` doesn't raise an
error.

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
        "tstop": 1000.0
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
    "tstop": 1000.0
}
```
Note that strings using e-notation (e.g. `1e-3` or `1E3` here) are decoded as
floats. Reversely, when writing files, floats are re-encoded using e-notation
if it leads to a more compact representation. For instance, `100000.0` is encoded
as `1e5`, but `189.0` is left unchanged because `1.89e2` takes one more character.
In cases where both reprensations are equally compact (e.g. `1.0` VS `1e0`),
decimal is prefered in encoding.

While decoding, `e` can be lower or upper case, but they are always encoded as
lower case.
</details>

## Installation

```shell
pip install inifix
```

## Usage

The public API mimicks that of Python's standard library `json`,
and consists in four main functions:
- `inifix.load` and `inifix.dump` read from and write to files respectively
- `inifix.loads` reads from a `str` and returns a `dict`, while `inifix.dumps`
  does the reverse operation.

### Reading data
`inifix.load` reads from a file and returns a `dict`

```python
import inifix

with open("pluto.ini", "rb") as fh:
    conf = inifix.load(fh)

# or equivalently
conf = inifix.load("pluto.ini")
```
Files are assumed to be encoded as UTF-8.

`inifix.load` and `inifix.loads` accept a optional boolean flag
`parse_scalars_as_list` (new in `inifix` v4.0.0), that is useful to simplify
handling unknown data: all values can be safely treated as arrays, and iterated
over, even in the presence of scalar strings. For illustration

```python
>>> import inifix
>>> from pprint import pprint
>>> pprint(inifix.load("example.ini"))
{'Grid': {'x': [1, 2, 'u', 10], 'y': [4, 5, 'l', 100]},
 'Time Integrator': {'CFL': 0.001, 'tstop': 1000.0}}
>>> pprint(inifix.load("ex.ini", parse_scalars_as_lists=True))
{'Grid': {'x': [1, 2, 'u', 10], 'y': [4, 5, 'l', 100]},
 'Time Integrator': {'CFL': [0.001], 'tstop': [1000.0]}}
```

### ... and writing back to disk

`inifix.dump` allows to write back to a file.

This allows to change a value on the fly and create new
configuration files programmatically, for instance.
```python
conf["Time"]["CFL"] = 0.1

with open("pluto-mod.ini", "wb") as fh:
    inifix.dump(conf, fh)

# or equivalently
inifix.dump(conf, "pluto-mod.ini")
```
Data will be validated against inifix's format specification at write time.
Files are always encoded as UTF-8.

### Schema Validation

`inifix.validate_inifile_schema` can be used to validate an arbitrary
dictionary as writable to an inifile, following Pluto/Idefix's format. This
will raise an exception (`ValueError`) if the dictionnary `data` is invalid.
```python
inifix.validate_inifile_schema(data)
```

### CLI

Command line tools are shipped with the package to validate or format compatible
inifiles.

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
    rev: v2.3.0
    hooks:
      - id: inifix-validate
```

#### Formatting

To format a file in place, use
```shell
$ inifix-format pluto.ini
```
inifix-format is guaranteed to preserve comments and to *only* edit (add or remove)
whitespace characters.

Files are always encoded as UTF-8.

#### Options


* To print a diff patch to stdout instead of editing the file, use the `--diff`
  flag
```shell
$ inifix-format pluto.ini --diff
```

This program also doubles as `pre-commit` hook
```yaml
  - repo: https://github.com/neutrinoceros/inifix.git
    rev: v2.3.0
    hooks:
      - id: inifix-format
```

## Testing

We use the [pytest](https://docs.pytest.org/en/latest/) framework to test
`inifix`. The test suite can be run from the top level with a simple `pytest`
invocation.
```shell
$ pytest
```
