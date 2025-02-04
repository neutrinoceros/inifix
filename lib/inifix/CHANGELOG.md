# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.0.0] - 2025-02-04

- API: ``inifix``'s command line interfaces (`inifix-validate`
  and `inifix-format`) were removed from the `inifix` package and now exist
  as a separate, private package `inifix-cli`, which is still used under the
  hood by `inifix`'s pre-commit hooks.
- API: all submodules are now explicitly marked as private. The only public
  namespace is `inifix`.
- TST: test against oldest versions of dependencies
- TYP: add basedpyright to type checking test matrix
- TST: check pre-commit hooks' stability continuously

## [5.1.3] - 2024-12-17

- TYP: prefer absolute forward references and avoid `__future__.annotations`
- TYP: ensure type annotations of the IO API are accessible at runtime in Python 3.14

## [5.1.2] - 2024-12-16

TYP: complete partially unknown type information

## [5.1.1] - 2024-12-13

BUG: restore IDEs' ability to obtain IO API docstrings by avoiding dynamic string interpolations

## [5.1.0] - 2024-12-13

- TYP: add missing `__all__` symbol to inifix's root namespace
- TYP: fix errors reported by `pyright`
- ENH: add `inifix.__version_tuple__`
- ENH: add sections-mode selection to `inifix.validate_inifile_schema`
- ENH: expose sections-mode selection in IO API
- TYP: narrow return type of `inifix.load` and `inifix.loads` following
  `parse_scalars_as_lists` and `sections` arguments
- TYP: systematically typecheck with pyright as well as mypy
- DOC: add narrative docs for sections argument and type narrowing

## [5.0.4] - 2024-11-29

- PERF: delay most costly import statements until they are needed
- CLN: cleanup unused future imports
- TST: add support for Python's optimized mode

## [5.0.3] - 2024-10-25

- TST: validate inifix's pre-commit hooks continuously
- TST: test against CPython 3.14-dev
- BLD: include tests dir in source distributions
- DOC: add conda-forge badge to `README.md`

## [5.0.2] - 2024-09-14

BUG: fix CPU counting on Linux + Python <=3.12
- this address an edge case where the main process isn't allowed to utilize all CPUs
- the bug cannot be fixed for platforms other than Linux and on Python <3.13
- it is *completely* fixed on Python >=3.13

## [5.0.1] - 2024-08-12

BUG: fix a crash in inifix-format on single-core machines

## [5.0.0] - 2024-08-09

### API changes

- in version 4.5.0, `inifix.load` and `inifix.loads` used to cast any
  integer-compatible string (e.g. `'1.0'`, `'1.'` or `'1e0'`) as a Python `int`.
  They now read these as Python `float`s by default. The previous behavior is
  still available as an opt-in, using the new argument `integer_parsing='aggressive'`.
  Strings such as `'123'` (without a `'.'`, an `'e'` or an `'E'`) are still
  parsed as Python `int`s in all cases.

- restrict special "bool-like" unescaped strings to lower, upper, or title cases.
  This means that for instance `true`, `TRUE` or `True` are still parsed as
  the Python boolean `True`, but e.g. `TruE` isn't.

- add and document `inifix.format_string`, replacing previously
  undocumented `inifix.iniformat` (still available for backward compatibility,
  but now deprecated)

### Bug fixes

- fix a corner case where data would be lost on dump for empty string values
- fix bugs around decoding supported bool values

### Other changes

- MNT: drop support for CPython 3.9
- TST: test against CPython 3.13 (both GIL flavor and free-threading flavor)
- TST: setup concurrency testing
- PERF: `inifix-format` (and the associated pre-commit hook) now runs on
  multiple threads. The performance gain is modest on stable versions of Python
  (as of 3.12), but expected to get more significant in the future (PEP 703).

## [4.5.0] - 2024-06-27

- DOC: illustate how to write type-safe applications of `inifix.load`
- ENH: `inifix-format` (and pre-commit hook) now validates that formatted data
  compares identical to unformatted data (unless `--skip-validation` is passed)

## [4.4.3] - 2024-03-09

BUG: fix a bug where `inifix-format --diff` would print extraneous trailing newlines

## [4.4.2] - 2023-10-19

BUG: fix a confusing error message in validation routine for invalid iterable data

## [4.4.1] - 2023-09-19

- BLD: drop support for CPython 3.8
- TST: add support for CPython 3.12
- DOC: fix a undesired asymmetry in usage example
- DEP: drop more-itertools as a dependency

## [4.4.0] - 2023-05-31

- DOC: update link to Idefix
- MNT: migrate to src layout

## [4.3.2] - 2023-03-11

BUG: fix type casting bugs affecting integers and strings

## [4.3.1] - 2023-03-10

PERF: speedup parsing (take 3)
This version is overall ~3x faster than inifix 4.1.0, and ~15% faster than inifix 4.3.0

## [4.3.0] - 2023-03-10

- ENH: implement --skip-validation for inifix-format CLI
- DOC: improve documentation for pre-commit hooks and validation-skipping options

## [4.2.2] - 2023-03-09

PERF: optimize parsing speed (reduce reading overhead by an additional 5%)

## [4.2.1] - 2023-03-09

BUG: fix a regression (in 4.2.0) where signed floats were interpreted as strings

## [4.2.0] - 2023-03-08

PERF: optimize parsing speed (reduce reading overhead by 60%)

## [4.1.0] - 2023-02-06

- ENH: allow skipping validation in IO operations
- ENH: allow special character '.' in parameter names


## [4.0.0] - 2023-01-30

TST: use requirement files instead of optional dependencies for tests and type checking

Installing with extra targets (`[test]` and `[typecheck]`) isn't supported anymore.


## [3.1.0] - 2023-01-08

- ENH: optimize startup time
- ENH: add option to load scalars as single-element lists


## [3.0.0] - 2022-05-24

This release contains a small, yet breaking change: in previous versions of
inifix, `t` and `f` were read as booleans. This feature was never documented
and was never supported in Idefix. Meanwhile, Idefix (dev) now supports reading
`yes` and `no` as booleans, so inifix will now also automatically parse these
special strings to booleans.


## [2.3.0] - 2022-05-01

ENH: add support for binary IO

All internal IO operations are now performed in binary mode whenever possible, assuming
UTF-8 encoding.

## [2.2.1] - 2022-04-30

BUG: fix a regression (inifix 2.2.0) where inifix.dump was able to write to a file even if
user doesn't have permission to.

## [2.2.0] - 2022-04-29

- BUG: fix a critical bug in parsing lines with interleaved quoted strings and other types
- BUG: fix casting for numeric str
- ENH: file writing operations are now atomic


## [2.1.2] - 2022-04-28

- BUG: fix a bug where formatting would affect spacing within quoted str values
- BUG: fix a bug where strings containing spacing would be dumped without correct quotes,
  making them appear as multiple separate values
- BUG: fix a bug where special strings 'true', 't', 'false' and 'f' would decay to boolean after two parsing cycles
- BUG: fix import * for inifix.io (add loads and dumps)

## [2.1.1] - 2022-04-27

BUG: fix a bug where string values containing whitespaces would incorrectly be split


## [2.1.0] - 2022-04-25

`inifix-format` now won't report noop by default when files are already formatted.
It can be turned on again with the `--report-noop` flag.
This makes the associated pre-commit hook much less verbose.


## [2.0.0] - 2022-04-17

The format enforced by inifix-format was changed to improve compacity and
readability. The new format is designed to be closer to manual formatting that
is actually performed by Idefix users and contributors.

This is considered a major version change because the `--name-column-size` CLI
flag and its corresponding keyword argument from `inifix.format.iniformat` were
removed.

The API is otherwise identical to version 1.2.1

## [1.2.1] - 2022-04-09

BUG: fix section invalidation

## [1.2.0] - 2022-03-18

- ENH: add two functions to the public API to read from and write to strings (`inifix.loads` and `inifix.dumps`)
- BUG: use more conservative rules in int/float casting rules to better match Idefix's reading routines.

## [1.1.0] - 2022-02-23

ENH: inifix-format now produces more compact files, with fewer empty lines.
[PR #98](https://github.com/neutrinoceros/inifix/pull/98)


## [1.0.3] - 2022-02-10

BUG: don't try to be clever with cumulative retcodes to avoid retcode overflow
[PR #97](https://github.com/neutrinoceros/inifix/pull/97)


## [1.0.2] - 2022-01-30

TYP: add py.typed marker file to improve downstream type-checking
[PR #94](https://github.com/neutrinoceros/inifix/pull/94)

## [1.0.1] - 2022-01-30

TYP: improve type-correctness [PR #93](https://github.com/neutrinoceros/inifix/pull/93)

## [1.0.0] - 2022-01-15

The API is now declared stable and any future intentionally breaking change
will follow a deprecation cycle.

- DEPR: drop support for Python 3.6 and 3.7, inifix now requires Python 3.8 or newer
- DEPR: end deprecation cycle for function arguments marked as "future-potisional-only"
- ENH: simplify internal logic (remove a non-user facing class, InifixConf)
- TYP: add mypy conf, add missing type annotations


[PR #91](https://github.com/neutrinoceros/inifix/pull/91)

## [0.11.2] - 2022-01-05

BUG: fix formatting for files with only sections and comments (no parameters)
[PR #90](https://github.com/neutrinoceros/inifix/pull/90)

## [0.11.1] - 2022-01-04

BUG: pretty print warnings from iniformat so they don't look as bad from the CLI
[PR #89](https://github.com/neutrinoceros/inifix/pull/89)

## [0.11.0] - 2022-01-04

ENH: replace `--inplace` option in `inifix-format` with a `--diff` option
[PR #87](https://github.com/neutrinoceros/inifix/pull/87)

## [0.10.0] - 2021-11-23

- ENH: expose name column length parameter to users in inifix-format
[PR #73](https://github.com/neutrinoceros/inifix/pull/73)
- BUG: fix formatter behaviour
[PR #83](https://github.com/neutrinoceros/inifix/pull/83)

## [0.9.1] - 2021-11-21

BUG: fix a bug in str casting
[PR #80](https://github.com/neutrinoceros/inifix/pull/80)

## [0.9.0] - 2021-10-28

ENH: improve schema validation and add a file validation pre-commit hook
[PR #74](https://github.com/neutrinoceros/inifix/pull/74)

## [0.8.0] - 2021-10-26
This version is identical to 0.7.0 except that `FutureWarning`s are now raised for
api calls using future positional-only arguments using the keyword syntax.

## [0.7.0] - 2021-10-26

This version is identical to 0.6.0 except that it's compatibly for Python 3.6 to
3.10. Positional-only arguments are not specified any more because their are not
available for Python versions earlier than 3.8 Warnings may be added in a
following version to discourage usage of keyword syntax for these arguments.
