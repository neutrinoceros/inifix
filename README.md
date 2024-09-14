# `inifix`

[![PyPI](https://img.shields.io/pypi/v/inifix.svg?logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/inifix/)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/neutrinoceros/inifix/main.svg)](https://results.pre-commit.ci/badge/github/neutrinoceros/inifix/main.svg)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/charliermarsh/ruff)


`inifix` is a small Python library offering a `load/dump` interface similar to
standard library modules `json` or `tomllib` (together with `tomli_w`) for ini
configuration files in the style of [Pluto](http://plutocode.ph.unito.it) and
[Idefix](https://github.com/idefix-code/idefix).

While its primary goal is to follow Idefix's 'ini' format specification, it
supports a small superset of it.

The key differences are:
- `inifix` supports section-free definitions. This means configuration files
  from [FARGO 3D](https://fargo3d.bitbucket.io) are also supported.
- in `inifix`, strings can be escaped using `'` or `"`. This allows to have
  whitespaces in string values and to force string type decoding where numeric
  and boolean types would work.

In rare cases where Idefix's 'ini' format doesn't match Pluto's, `inifix` takes
the path of least resistance to support both.

Known differences are:
- Idefix allows booleans to be written as `yes` and `no`, as so does `inifix`,
  but these are not valid in Pluto (as of version 4.4).
  Note that in contrast to Idefix, which is truly case-insensitive about
  these special strings, `inifix` (from version 5.0.0) only parse a restricted
  set of unescaped strings as booleans, like `true`, `TRUE`, `True`, `yes`,
  `Yes` and `YES`, but `TruE` or `yES` for instance will be parsed as strings.
- Idefix allows integers to be written using decimal notation (e.g. `1.0` or `1e3`).
  This creates some ambiguity when deserializing such strings, as the expected type
  (`int` or `float`) cannot be unambiguously guessed. By default, `inifix` (from
  version 5.0) will parse these as `float`s, allowing for 1-to-1 roundtrips.
  Idefix (as of version 2.1) is also resilient against integers written as decimal,
  so `inifix` will not break any working inifile by a load/patch/dump routine.
  See [Reading Options](#reading-options) for more.

## File format specifications details
<details><summary>Unroll !</summary>
- parameter names are alphanumeric strings
- names and values are separated by non-newline white spaces
- values are represented in unicode characters
- all values are considered numbers if possible (e.g., `1e3` is read as `1000`)
- number values are read as integers if no loss of precision ensues, and floats otherwise
- unescaped strings `true`, `false`, `yes` and `no` are cast to booleans, as well
  as their respective upper-case and "title" variants (e.g. `TRUE` or `True`).
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
specifications, but is also valid in `inifix`
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
decimal is preferred in encoding.

While decoding, `e` can be lower or upper case, but they are always encoded as
lower case.
</details>

## Installation

```shell
python -m pip install inifix
```

## Usage

The public API mimics that of Python's standard library `json`,
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

#### Reading options

`inifix.load` and `inifix.loads` accept an optional boolean flag
`parse_scalars_as_lists` (new in `inifix` v4.0.0), that is useful to simplify
handling unknown data: all values can be safely treated as arrays, and iterated
over, even in the presence of scalar strings. For illustration

```python
>>> import inifix
>>> from pprint import pprint
>>> pprint(inifix.load("example.ini"))
{'Grid': {'x': [1, 2, 'u', 10], 'y': [4, 5, 'l', 100]},
 'Time Integrator': {'CFL': 0.001, 'tstop': 1000.0}}
>>> pprint(inifix.load("example.ini", parse_scalars_as_lists=True))
{'Grid': {'x': [1, 2, 'u', 10], 'y': [4, 5, 'l', 100]},
 'Time Integrator': {'CFL': [0.001], 'tstop': [1000.0]}}
```

`inifix.load` and `inifix.loads` also accept an `integer_casting` argument (new
in `inifix` v5.0.0), which can be set to decide how numbers written in decimal
notation which happen to have integral values (e.g. `1e2` or `30000.`) should be
parsed.
This argument accepts two values:
`'stable'` (default) gives `float`s while `'aggressive'` gives `int`s,
matching the behavior of `inifix` v4.5.0.

The key difference is that the default strategy is roundtrip-stable on types,
while the aggressive mode isn't:
```python
>>> import inifix
>>> data = {'option_a': [0, 1., 2e3, 4.5]}
>>> data
{'option_a': [0, 1.0, 2000.0, 4.5]}
>>> inifix.loads(inifix.dumps(data))
{'option_a': [0, 1.0, 2000.0, 4.5]}
>>> inifix.loads(inifix.dumps(data), integer_casting='aggressive')
{'option_a': [0, 1, 2000, 4.5]}
```

Aggressive casting may also lead to loss of precision beyond a certain range
```python
>>> import inifix
>>> data = {'option_b': 9_007_199_254_740_993}
>>> inifix.loads(inifix.dumps(data))
{'option_b': 9007199254740993}
>>> inifix.loads(inifix.dumps(data), integer_casting='aggressive')
{'option_b': 9007199254740992}
```

By default, `inifix.load` and `inifix.loads` validate input data. This step can
be skipped by specifying `skip_validation=True`.


### Writing to a file or a string

`inifix.dump` writes data to a file.

One typical use case is to combine `inifix.load` and `inifix.dump` to
programmatically update an existing configuration file at runtime via a
load/patch/dump routine.
```python
>>> import inifix
>>> with open("pluto.ini", "rb") as fr:
...    inifix.load(fr)
>>> conf["Time"]["CFL"] = 0.1
>>> with open("pluto-mod.ini", "wb") as fw:
...    inifix.dump(conf, fw)
```
or, equivalently
```python
>>> import inifix
>>> inifix.load("pluto.ini")
>>> conf["Time"]["CFL"] = 0.1
>>> inifix.dump(conf, "pluto-mod.ini")
```
Data will be validated against inifix's format specification at write time.
Files are always encoded as UTF-8.

`inifix.dumps` is the same as `inifix.dump` except that it returns a string
instead of writing to a file.
```python
>>> import inifix
>>> data = {"option_a": 1, "option_b": True}
>>> print(inifix.dumps(data))
option_a 1
option_b True

```

By default, `inifix.dump` and `inifix.dumps` validate input data. This step can
be skipped by specifying `skip_validation=True`.


### Schema Validation

`inifix.validate_inifile_schema` can be used to validate an arbitrary
dictionary as writable to an inifile, following the library's format. This
will raise an exception (`ValueError`) if the dictionary `data` is invalid.
```python
inifix.validate_inifile_schema(data)
```

### Runtime formatting

`inifix.format_string` formats a string representing the contents of an ini file.
See [Formatting CLI](#formatting-cli) for how to use this at scale.

### Writing type-safe applications of `inifix.load(s)`

`inifix.load` has no built-in expectations on the type of any specific parameter;
instead, all types are inferred at runtime, which allows the function to work
seamlessly with arbitrary parameter files.

However, this also means that the output is not (and cannot be) type-safe.
In other words, type checkers (e.g. `mypy`) cannot infer exact types of outputs,
which is a problem in applications relying on type-checking.

A solution to this problem, which is actually not specific to `inifix.load` and
works with any arbitrarily formed `dict`, is to create a pipeline around this data
which implements type-checkable code, where data is *also* validated at runtime.

We'll illustrate this with a real-life example inspired from
[`nonos`](https://pypi.org/project/nonos).
Say, for instance, that we only care about a couple parameters from the `[Output]`
and `[Hydro]` sections of `idefix.ini`. Let's build a type-safe `read_parameter_file`
function around these.

```python
class IdefixIni:
    def __init__(self, *, Hydro, Output, **kwargs):
        self.hydro = IdefixIniHydro(**Hydro)
        self.output = IdefixIniOutput(**Output)

class IdefixIniHydro:
    def __init__(self, **kwargs):
        if "rotation" in kwargs:
            self.frame = "COROT"
            self.rotation = float(kwargs["rotation"])
        else:
            self.frame = "UNSET"
            self.rotation = 0.0

class IdefixIniOutput:
    def __init__(self, *, vtk, **kwargs):
        self.vtk = float(vtk)

def read_parameter_file(file) -> IdefixIni:
    return IdefixIni(**inifix.load(file))

ini = read_parameter_file("idefix.ini")
```

Type checkers can now safely assume that, `ini.hydro.frame`, `ini.hydro.rotation`
and `ini.output.vtk` all exist and are of type `str`, `float` and `float`, respectively.
If this assumption is not verified at runtime, a `TypeError` will be raised.

Note that we've used the catch-all `**kwargs` construct to capture optional
parameters as well as any other parameters present (possibly none) that we do not
care about.

### CLI

Command line tools are shipped with the package to validate or format compatible
inifiles.

#### Validation CLI

This checks that your inifiles can be loaded with `inifix.load` from the command line
```shell
$ inifix-validate pluto.ini
Validated pluto.ini
```
This CLI can also be called as `python -m inifix.validate`.


#### Formatting CLI

To format a file in place, use
```shell
$ inifix-format pluto.ini
```
inifix-format is guaranteed to preserve comments and to *only* edit (add or remove)
whitespace characters.

Files are always encoded as UTF-8.

To print a diff patch to stdout instead of editing the file, use the `--diff` flag
```shell
$ inifix-format pluto.ini --diff
```
This CLI can also be called as `python -m inifix.format`.

By default, `inifix-format` also validates input data. This step can be skipped with the
`--skip-validation` flag

### pre-commit hooks

`inifix-validate` and `inifix-format` can be used as `pre-commit` hooks with the
following configuration (add to `.pre-commit-config.yaml`)

```yaml
  - repo: https://github.com/neutrinoceros/inifix.git
    rev: v5.0.2
    hooks:
      - id: inifix-validate
```
or
```yaml
  - repo: https://github.com/neutrinoceros/inifix.git
    rev: v5.0.2
    hooks:
      - id: inifix-format
```

Note that `inifix-format` also validates data by default, so it is redundant to
utilize both hooks. Validation and formatting may nonetheless be decoupled as
```patch
  - repo: https://github.com/neutrinoceros/inifix.git
    rev: v5.0.2
    hooks:
    - id: inifix-validate
    - id: inifix-format
+     args: [--skip-validation]
```

By default, both hooks target files matching the regular expression `(\.ini)$`.
It is possible to override this expression as, e.g.,
```patch
   hooks:
   - id: inifix-format
+    files: (\.ini|\.par)$
```

## Testing

We use the [pytest](https://docs.pytest.org/en/latest/) framework to test
`inifix`. The test suite can be run from the top level with a simple `pytest`
invocation.
```shell
$ python -m pip install --requirement requirements/tests.txt
$ pytest
```
