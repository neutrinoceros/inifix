# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "packaging",
#     "tomli ; python_version < '3.11'",
# ]
# ///
import re
import subprocess
import sys
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path

from packaging.version import Version

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

REV_REGEXP = re.compile(r"rev:\s+v.*")
STABLE_VER_REGEXP = re.compile(r"^\d+\.*\d+\.\d+$")
STABLE_TAG_REGEXP = re.compile(r"^v\d+\.*\d+\.\d+$")
ROOT = Path(__file__).parents[1]
README = ROOT / "README.md"
PYPROJECT_TOML = ROOT / "pyproject.toml"


@dataclass(frozen=True)
class Metadata:
    current_static_version: Version
    latest_git_tag: str

    @property
    def latest_git_version(self) -> Version:
        if not STABLE_TAG_REGEXP.match(self.latest_git_tag):
            print(
                f"Failed to parse git tag (got {self.latest_git_tag})", file=sys.stderr
            )
            raise SystemExit(1)
        return Version(self.latest_git_tag)


def check_static_version(md: Metadata) -> int:
    if not STABLE_VER_REGEXP.match(str(md.current_static_version)):
        print(
            f"Current static version {md.current_static_version} doesn't "
            "conform to expected pattern for a stable sem-ver version.",
            file=sys.stderr,
        )
        return 1
    elif md.current_static_version < md.latest_git_version:
        print(
            f"Current static version {md.current_static_version} appears "
            f"to be older than latest git tag {md.latest_git_tag}",
            file=sys.stderr,
        )
        return 1
    else:
        print("Check static version: ok", file=sys.stderr)
        return 0


def check_readme(md: Metadata) -> int:
    text = README.read_text()
    if md.current_static_version.is_devrelease:
        expected_tag = md.latest_git_tag
    else:
        expected_tag = f"v{md.current_static_version}"
    if text != (expected := REV_REGEXP.sub(f"rev: {expected_tag}", text)):
        diff = "\n".join(
            line.removesuffix("\n")
            for line in unified_diff(
                text.splitlines(),
                expected.splitlines(),
                fromfile=str(PYPROJECT_TOML),
            )
        )
        print(diff, file=sys.stderr)
        return 1
    else:
        print("Check README.md: ok", file=sys.stderr)
        return 0


def main() -> int:
    with open(PYPROJECT_TOML, "rb") as fh:
        current_static_version = Version(tomllib.load(fh)["project"]["version"])

    cp = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        check=True,
        capture_output=True,
    )
    cp_stdout = cp.stdout.decode().strip()

    md = Metadata(current_static_version, cp_stdout)

    return check_static_version(md) or check_readme(md)


if __name__ == "__main__":
    raise SystemExit(main())
