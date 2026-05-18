# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "loguru==0.7.3",
#     "packaging==24.2",
# ]
# ///
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path
from typing import Literal

from loguru import logger
from packaging.requirements import Requirement
from packaging.specifiers import Specifier
from packaging.version import Version

logger.remove()
logger.add(sys.stderr, colorize=True, format="<level>{level:<5} {message}</level>")

REV_REGEXP = r"rev:\s+v.*"
STABLE_VER_REGEXP = r"^\d+\.*\d+\.\d+$"
STABLE_TAG_REGEXP = r"v\d+\.*\d+\.\d+$"
ROOT = Path(__file__).parents[1]
CLI_DIR = ROOT / "cli" / "inifix-cli"
README = ROOT / "README.md"
LIB_PYPROJECT_TOML = ROOT / "pyproject.toml"
CLI_PYPROJECT_TOML = CLI_DIR / "pyproject.toml"


@dataclass(frozen=True)
class Metadata:
    current_lib_static_version: Version
    current_cli_static_version: Version
    current_cli_requirement: Requirement
    lib_requires_python: Specifier
    cli_requires_python: Specifier
    latest_lib_git_tag: str
    latest_cli_git_tag: str

    @property
    def latest_lib_git_version(self) -> Version:
        if not re.fullmatch(STABLE_TAG_REGEXP, self.latest_lib_git_tag):
            logger.error(f"Failed to parse git tag (got {self.latest_lib_git_tag})")
            raise SystemExit(1)
        return Version(self.latest_lib_git_tag)

    @property
    def latest_cli_git_version(self) -> Version:
        if not re.fullmatch(f"^cli-{STABLE_TAG_REGEXP}", self.latest_cli_git_tag):
            logger.error(f"Failed to parse git tag (got {self.latest_cli_git_tag})")
            raise SystemExit(1)
        return Version(self.latest_cli_git_tag.removeprefix("cli-"))


def check_static_versions(md: Metadata) -> int:
    if not re.match(STABLE_VER_REGEXP, str(md.current_lib_static_version)):
        logger.error(
            f"Current static version {md.current_lib_static_version} doesn't "
            "conform to expected pattern for a stable sem-ver version.",
        )
        return 1
    elif md.current_lib_static_version < md.latest_lib_git_version:
        logger.error(
            f"Current static lib version {md.current_lib_static_version} appears "
            f"to be older than latest git tag {md.latest_lib_git_tag}",
        )
        return 1
    elif md.current_cli_static_version < md.latest_cli_git_version:
        logger.error(
            f"Current static cli version {md.current_lib_static_version} appears "
            f"to be older than latest git tag {md.latest_lib_git_tag}",
        )
        return 1
    else:
        logger.info("Check static versions: ok", file=sys.stderr)
        return 0


def check_inifix_cli_requirement(md: Metadata) -> int:
    if not md.current_cli_requirement.specifier.contains(md.current_lib_static_version):
        logger.error(
            f"inifix-cli is requiring inifix as {md.current_cli_requirement} "
            f"which excludes inifix's current version ({md.current_lib_static_version})",
        )
        return 1
    else:
        logger.info("Check version ranges: ok", file=sys.stderr)
        return 0


def check_requires_python(md: Metadata) -> int:
    if md.cli_requires_python != md.lib_requires_python:
        logger.error(
            f"inifix-cli's python requirement ({md.cli_requires_python}) "
            f"is out of sync with inifix's ({md.lib_requires_python})",
        )
        return 1
    else:
        logger.info("Check requires-python: ok")
        return 0


def get_latest_git_tag(type: Literal["lib", "cli"]) -> str:
    match type:
        case "lib":
            pattern = "v*"
        case "cli":
            pattern = "cli-v*"
        case _:
            raise ValueError

    cp = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0", f"--match={pattern}"],
        capture_output=True,
    )
    if cp.returncode != 0:
        raise RuntimeError(f"subprocess failed with: {cp.stderr.decode()}")
    tag = cp.stdout.decode().strip()
    logger.debug(f"found latest {type} {tag = !r}")
    return tag


def check_readme(md: Metadata) -> int:
    text = README.read_text(encoding="utf-8")
    if md.current_lib_static_version.is_devrelease:
        expected_tag = md.latest_lib_git_tag
    else:
        expected_tag = f"v{md.current_lib_static_version}"
    if text != (expected := re.sub(REV_REGEXP, f"rev: {expected_tag}", text)):
        diff = "\n".join(
            line.removesuffix("\n")
            for line in unified_diff(
                text.splitlines(),
                expected.splitlines(),
                fromfile=str(LIB_PYPROJECT_TOML),
            )
        )
        logger.error(diff)
        return 1
    else:
        logger.info("Check README.md: ok")
        return 0


def main() -> int:
    with open(LIB_PYPROJECT_TOML, "rb") as fh:
        lib_table = tomllib.load(fh)
        current_lib_static_version = Version(lib_table["project"]["version"])
        current_lib_requires_python = Specifier(lib_table["project"]["requires-python"])
    with open(CLI_PYPROJECT_TOML, "rb") as fh:
        cli_table = tomllib.load(fh)
        current_cli_static_version = Version(lib_table["project"]["version"])
        current_cli_requires_python = Specifier(cli_table["project"]["requires-python"])
        cli_requirements = [
            Requirement(_) for _ in cli_table["project"]["dependencies"]
        ]
    for req in cli_requirements:
        if req.name == "inifix":
            current_cli_requirement = req
            break
    else:
        raise RuntimeError(f"failed to parse {CLI_PYPROJECT_TOML}")

    md = Metadata(
        current_lib_static_version,
        current_cli_static_version,
        current_cli_requirement,
        current_lib_requires_python,
        current_cli_requires_python,
        get_latest_git_tag("lib"),
        get_latest_git_tag("cli"),
    )

    return (
        check_static_versions(md)
        + check_inifix_cli_requirement(md)
        + check_requires_python(md)
        + check_readme(md)
    )


if __name__ == "__main__":
    raise SystemExit(main())
