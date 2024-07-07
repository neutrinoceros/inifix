from collections.abc import Iterable
from typing import TypeAlias, TypeVar

# not quite typing.AnyStr : this is not a constrained type variable
StrLike = str | bytes

T = TypeVar("T")
Scalar = int | float | bool | str
IterableOrSingle: TypeAlias = Iterable[T] | T

# these types are used to validate schemas internally at type-checking time
SectionT = dict[str, IterableOrSingle[Scalar]]
InifixConfT = dict[str, SectionT] | SectionT
