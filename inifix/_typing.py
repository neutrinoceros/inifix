import os
import sys
from typing import AnyStr
from typing import Dict
from typing import Iterable
from typing import TypeVar
from typing import Union

if sys.version_info >= (3, 9):
    PathLike = Union[AnyStr, os.PathLike[AnyStr]]
else:
    PathLike = Union[AnyStr, os.PathLike]

T = TypeVar("T")
Scalar = Union[int, float, bool, str]
IterableOrSingle = Union[Iterable[T], T]

# these types are used to validate schemas internally at type-checking time
SectionT = Dict[str, IterableOrSingle[Scalar]]
InifixConfT = Union[Dict[str, SectionT], SectionT]
