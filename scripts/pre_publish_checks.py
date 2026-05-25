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
from itertools import permutations
from pathlib import Path

from loguru import logger
from packaging.requirements import Requirement
from packaging.specifiers import Specifier
from packaging.version import Version

logger.remove()
logger.add(sys.stderr, colorize=True, format="<level>{level:<5} {message}</level>")

REV_REGEXP = r"rev:\s+v.*"
STABLE_VER_REGEXP = r"^\d+\.*\d+\.\d+"
STABLE_TAG_REGEXP = r"v\d+\.*\d+\.\d+"
ROOT = Path(__file__).parents[1]
CLI_DIR = ROOT / "cli" / "inifix-cli"


@dataclass(slots=True, frozen=True, kw_only=True)
class PackageMeta:
    root: Path
    name: str
    version: Version
    python_requires: Specifier
    requirements: list[Requirement]
    tag_prefix: str

    @classmethod
    def from_root(cls, dir_: Path, /) -> "PackageMeta":
        with open(dir_ / "pyproject.toml", "rb") as fh:
            table = tomllib.load(fh)
        name = table["project"]["name"]
        match name:
            case "inifix":
                prefix = ""
            case "inifix-cli":
                prefix = "cli-"
            case _:
                raise AssertionError

        return PackageMeta(
            root=dir_,
            name=name,
            version=Version(table["project"]["version"]),
            python_requires=Specifier(table["project"]["requires-python"]),
            requirements=[Requirement(_) for _ in table["project"]["dependencies"]],
            tag_prefix=prefix,
        )

    @property
    def tag_pattern(self) -> str:
        # shell wildcard, not a regexp !
        return f"{self.tag_prefix}v*"

    @property
    def tag_regexp(self) -> str:
        return f"^{self.tag_prefix}{STABLE_TAG_REGEXP}$"

    @property
    def latest_git_version(self) -> Version:
        cp = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0", f"--match={self.tag_pattern}"],
            capture_output=True,
        )
        if cp.returncode != 0:
            raise RuntimeError(f"subprocess failed with: {cp.stderr.decode()}")
        tag = cp.stdout.decode().strip()
        logger.debug(f"found latest {self.name} {tag = !r}")
        if not re.fullmatch(self.tag_regexp, tag):
            logger.error(f"Failed to parse git tag (got {tag})")
            raise SystemExit(1)
        return Version(tag.removeprefix(self.tag_prefix))

    def check_static_versions(self) -> int:
        if not re.match(STABLE_VER_REGEXP, str(self.version)):
            logger.error(
                f"[{self.name}] static version {self.version} doesn't "
                "conform to expected pattern for a stable sem-ver version.",
            )
            return 1
        elif self.version < self.latest_git_version:
            logger.error(
                f"[{self.name}] version {self.version} appears "
                f"to be older than latest git tag {self.latest_git_version}",
            )
            return 1
        else:
            logger.info(f"[{self.name}] Check static versions: ok", file=sys.stderr)
            return 0

    def check_readme(self) -> int:
        text = self.root.joinpath("README.md").read_text(encoding="utf-8")
        if self.version.is_devrelease:
            expected_tag = str(self.latest_git_version)
        else:
            expected_tag = f"v{self.version}"
        if text != (expected := re.sub(REV_REGEXP, f"rev: {expected_tag}", text)):
            diff = "\n".join(
                line.removesuffix("\n")
                for line in unified_diff(
                    text.splitlines(),
                    expected.splitlines(),
                    fromfile=str(self.root / "pyproject.toml"),
                )
            )
            logger.error(diff)
            return 1
        else:
            logger.info(f"[{self.name}] Check README.md: ok")
            return 0


def check_python_requires(*packages: PackageMeta) -> int:
    p0 = packages[0]
    if any(p.python_requires != p0.python_requires for p in packages):
        logger.error(
            "Inconsistent requirements on Python: \n\n".join(
                [f" * {p.name} requires {str(p.python_requires)!r}" for p in packages]
            )
        )
        return 1
    else:
        logger.info("Check requires-python: ok")
        return 0


def check_workspace_consistency(*packages: PackageMeta) -> int:
    retv = 0
    for p1, p2 in permutations(packages, 2):
        for req in p1.requirements:
            if p2.name != req.name or req.specifier.contains(p2.version):
                continue
            logger.error(
                f"{p1.name} requires {p2.name} {req} "
                f"which excludes {p2.name}'s current version ({p2.version})",
            )
            retv = 1
    if retv == 0:
        logger.info("Check workspace consistency: ok")
    return retv


def main() -> int:
    packages = [
        PackageMeta.from_root(ROOT),
        PackageMeta.from_root(CLI_DIR),
    ]
    retv = 0
    for p in packages:
        retv += p.check_static_versions() + p.check_readme()
    retv += check_python_requires(*packages)
    retv += check_workspace_consistency(*packages)
    return retv


if __name__ == "__main__":
    raise SystemExit(main())
