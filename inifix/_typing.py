import os
from typing import Iterable, Mapping, TypeVar, Union

T = TypeVar("T")
Scalar = Union[int, float, bool, str]
IterableOrSingle = Union[Iterable[T], T]
PathLike = Union[str, bytes, os.PathLike]

Section = Mapping[str, IterableOrSingle[Scalar]]
InifixParsable = Mapping[str, Union[Section, Scalar]]
