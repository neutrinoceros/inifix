from importlib.util import find_spec

import pytest


def has(module_name: str) -> bool:
    return find_spec(module_name) is not None


HAS_CLI_DEPS = (has("typer") or has("typer-slim")) and has("rich")


@pytest.mark.skipif(HAS_CLI_DEPS, reason="optional dependencies are installed")
def test_cli_startup_missing_deps():
    with pytest.raises(ImportError):
        import inifix.__main__  # noqa
