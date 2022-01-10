import os
import sys
from typing import AnyStr
from typing import Dict
from typing import Iterable
from typing import Optional
from typing import TypeVar
from typing import Union

T = TypeVar("T")
Scalar = Union[int, float, bool, str]
IterableOrSingle = Union[Iterable[T], T]

if sys.version_info > (3, 9):
    PathLike = Union[AnyStr, os.PathLike[AnyStr]]
else:
    PathLike = Union[AnyStr, os.PathLike]

# these types are used to validate schemas internally at type-checking time
SectionT = Dict[str, IterableOrSingle[Scalar]]
InifixConfT = Dict[Optional[str], SectionT]
