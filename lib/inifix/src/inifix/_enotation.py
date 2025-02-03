import re
import sys
from enum import Enum, auto

if sys.version_info >= (3, 11):
    from typing import assert_never
else:
    from typing_extensions import assert_never

__all__ = ["Enotation"]

ENOTATION_REGEXP = re.compile(r"\d+(\.\d*)?e[+-]?\d+?")


class Enotation(Enum):
    ALWAYS = auto()
    ONLY_SHORTER = auto()

    @staticmethod
    def _simplify(s: str, /) -> str:
        """
        Simplify exponents and trailing zeros in decimals.
        """
        s = re.sub(r"\.?0*(e[+-]?)0", r"\1", s)
        s = re.sub(r"(e-0)$", "e0", s)
        return s.replace("+", "")

    def _encode_unconditionally(self, r: float, /) -> str:
        """
        Convert a real number `r` to string, using scientific notation.

        Note that this differs from using format specifiers (e.g. `.6e`)
        in that trailing zeros are removed.
        Precision must be conserved.

        Parameters
        ----------
        r: real number (float or int)

        Returns
        -------
        ret: str
            A string representing r in sci notation

        """
        base = str(r)
        if "e" in base:
            return self._simplify(base)
        if not base.strip(".0"):
            return "0e0"
        max_ndigit = len(base.replace(".", "")) - 1
        return self._simplify(f"{r:.{max_ndigit}e}")

    def encode(self, r: float, /) -> str:
        result = self._encode_unconditionally(r)
        match self:
            case Enotation.ALWAYS:
                return result
            case Enotation.ONLY_SHORTER:
                return min(str(float(r)), result, key=lambda x: len(x))
            case _:  # pragma: no cover
                assert_never(self)
