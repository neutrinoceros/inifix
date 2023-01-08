# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

- ENH: optimize startup time


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

BUG: fix a bug where string values containing whitespaces would incorrectly be splitted


## [2.1.0] - 2022-04-25

`inifix-format` now won't report noop by default when files are already formatted.
It can be turned on again with the `--report-noop` flag.
This makes the associated pre-commit hook much less verbose.


## [2.0.0] - 2022-04-17

The format enforced by inifix-format was changed to improve compacity and
readability. The new format is designed to be closer to manual formatting that
is actually perfomed by Idefix users and contributors.

This is considered a major version change because the `--name-column-size` CLI
flag and its corresponding keyword argument from `inifix.format.iniformat` were
removed.

The API is otherwize identical to version 1.2.1

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
