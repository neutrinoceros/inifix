# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] 2026-05-23

- ENH: declare lazy modules, improving CLI responsiveness on Python 3.15+

## [1.0.0] 2026-05-18

`inifix-cli` is now published to PyPI independently. Previous versions of this package were considered private and an implementation detail for how inifix's pre-commit hooks were structured. See `inifix`'s changelog (up to version 6.1.2) for user-visible changes across previous versions.

- ENH: add ability to exclude files by regular expressions after
  pre-commit's own selection via the new `--exclude` and `--extend-exclude` options.
  The default exclude list is `['pytest\\.ini$', 'tox\\.ini$']`
- DEP: Python 3.11 or newer is now required
- DEP: runtime dependencies are reduced to a bare minimum (inifix + click),
  and requirements are expressed as (open) ranges instead of exact versions
