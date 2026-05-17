from typing import TypeAlias

# not quite typing.AnyStr : this is not a constrained type variable
StrLike: TypeAlias = str | bytes
Scalar: TypeAlias = int | float | bool | str

Section_ScalarsAllowed: TypeAlias = dict[str, list[Scalar] | Scalar]
Section_ScalarsForbidden: TypeAlias = dict[str, list[Scalar]]

AnySection = Section_ScalarsAllowed | Section_ScalarsForbidden

Config_SectionsRequired_ScalarsForbidden: TypeAlias = dict[
    str, Section_ScalarsForbidden
]
Config_SectionsRequired_ScalarsAllowed: TypeAlias = dict[str, Section_ScalarsAllowed]
Config_SectionsForbidden_ScalarsForbidden: TypeAlias = Section_ScalarsForbidden
Config_SectionsForbidden_ScalarsAllowed: TypeAlias = Section_ScalarsAllowed
Config_SectionsAllowed_ScalarsAllowed: TypeAlias = (
    dict[str, Section_ScalarsAllowed] | Section_ScalarsAllowed
)
Config_SectionsAllowed_ScalarsForbidden: TypeAlias = (
    dict[str, Section_ScalarsForbidden] | Section_ScalarsForbidden
)

AnyConfig: TypeAlias = (
    Config_SectionsAllowed_ScalarsAllowed
    | Config_SectionsAllowed_ScalarsForbidden
    | Config_SectionsForbidden_ScalarsAllowed
    | Config_SectionsForbidden_ScalarsForbidden
    | Config_SectionsRequired_ScalarsAllowed
    | Config_SectionsRequired_ScalarsForbidden
)
