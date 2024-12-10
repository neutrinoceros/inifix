from collections.abc import Iterable

# not quite typing.AnyStr : this is not a constrained type variable
StrLike = str | bytes
Scalar = int | float | bool | str

# these types are used to validate schemas internally at type-checking time
SectionT = dict[str, Iterable[Scalar] | Scalar]
InifixConfT = dict[str, SectionT] | SectionT
