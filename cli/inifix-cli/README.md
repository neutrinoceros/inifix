# `inifix-cli`

[![PyPI](https://img.shields.io/pypi/v/inifix-cli.svg?logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/inifix-cli/)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/inifix-cli)](https://pypi.org/project/inifix/)

This is a small Command Line Interface (CLI) companion to the `inifix` library.

It offers two commands:
- `inifix validate`
- `inifix format`


## Installation

It is recommended to install or run this application with `pipx` or `uv tool`.
It is also possible to install it in an arbitrary Python environment with

```shell
python -m pip install inifix-cli
```

## Usage

Invoke `inifix <cmd> --help` for details.


### `inifix-pre-commit`

pre-commit hooks backed by this CLI are served from
https://github.com/la-niche/inifix-pre-commit
