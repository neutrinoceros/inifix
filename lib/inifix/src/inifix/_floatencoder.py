import re
import sys
from enum import Enum, auto

if sys.version_info >= (3, 11):
    from typing import assert_never
else:
    from typing_extensions import assert_never

__all__ = ["FloatEncoder"]


class FloatEncoder(Enum):
    SIMPLE = auto()
    ENOTATION = auto()
    ENOTATION_IFF_SHORTER = auto()

    @staticmethod
    def _simplify(s: str, /) -> str:
        """
        Simplify exponents and trailing zeros in decimals.
        """
        s = re.sub(r"\.?0*(e[+-]?)0", r"\1", s)
        s = re.sub(r"(e-0)$", "e0", s)
        return s.replace("+", "")

    def encode(self, r: float, /) -> str:
        match self:
            case FloatEncoder.SIMPLE:
                return str(float(r))
            case FloatEncoder.ENOTATION:
                base = str(r)
                if "e" in base:
                    return self._simplify(base)
                if not base.strip(".0"):
                    return "0e0"
                max_ndigit = len(base.replace(".", "")) - 1
                return self._simplify(f"{r:.{max_ndigit}e}")
            case FloatEncoder.ENOTATION_IFF_SHORTER:
                return min(
                    FloatEncoder.SIMPLE.encode(r),
                    FloatEncoder.ENOTATION.encode(r),
                    key=lambda x: len(x),
                )
            case _:  # pragma: no cover
                assert_never(self)
