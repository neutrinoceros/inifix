# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "tomli ; python_version < '3.11'",
# ]
# ///
import re
import sys
from difflib import unified_diff
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

REV_REGEXP = re.compile(r"rev:\s+v.*")
STABLE_VER_REGEXP = re.compile(r"^\d\.*\d\.\d$")
ROOT = Path(__file__).parents[1]
README = ROOT / "README.md"
PYPROJECT_TOML = ROOT / "pyproject.toml"


def main() -> int:
    text = README.read_text()

    with open(PYPROJECT_TOML, "rb") as fh:
        current_version = tomllib.load(fh)["project"]["version"]

    if not STABLE_VER_REGEXP.match(current_version):
        print("Nothing to check.")
        return 0

    if text == (expected := REV_REGEXP.sub(f"rev: v{current_version}", text)):
        print("All ok.")
        return 0

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


if __name__ == "__main__":
    sys.exit(main())
