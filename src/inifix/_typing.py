import os
from collections.abc import Iterable
from typing import AnyStr, TypeVar, Union

# not quite typing.AnyStr : this is not a constrained type variable
StrLike = Union[str, bytes]

PathLike = Union[AnyStr, os.PathLike[AnyStr]]

T = TypeVar("T")
Scalar = Union[int, float, bool, str]
IterableOrSingle = Union[Iterable[T], T]

# these types are used to validate schemas internally at type-checking time
SectionT = dict[str, IterableOrSingle[Scalar]]
InifixConfT = Union[dict[str, SectionT], SectionT]
