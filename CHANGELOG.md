# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
