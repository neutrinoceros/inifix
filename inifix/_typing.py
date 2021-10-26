import os
from typing import Iterable
from typing import Mapping
from typing import TypeVar
from typing import Union

T = TypeVar("T")
Scalar = Union[int, float, bool, str]
IterableOrSingle = Union[Iterable[T], T]
PathLike = Union[str, bytes, os.PathLike]

Section = Mapping[str, IterableOrSingle[Scalar]]
InifixParsable = Mapping[str, Union[Section, Scalar]]
