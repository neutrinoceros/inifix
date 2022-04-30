import os
import sys
from typing import AnyStr
from typing import Dict
from typing import Iterable
from typing import TypeVar
from typing import Union

# not quite typing.AnyStr : this is not a constrained type variable
StrLike = Union[str, bytes]

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
