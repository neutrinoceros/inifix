from io import BytesIO
from typing import assert_type

from inifix import load, loads
from inifix._typing import (
    AnyMutConfig,
    MutConfig_SectionsAllowed_ScalarsForbidden,
    MutConfig_SectionsForbidden_ScalarsAllowed,
    MutConfig_SectionsForbidden_ScalarsForbidden,
    MutConfig_SectionsRequired_ScalarsAllowed,
    MutConfig_SectionsRequired_ScalarsForbidden,
)

bytes_wo_section = b"pi 3.14"
bytes_w_section = b"[Title]\n" + bytes_wo_section

# 1 case with 0 type-narrowing arguments
c0 = load(BytesIO(bytes_wo_section))
_ = assert_type(c0, AnyMutConfig)
c0 = loads(bytes_wo_section.decode())
_ = assert_type(c0, AnyMutConfig)

# 5 cases with 1 type-narrowing argument
c1_0 = load(BytesIO(bytes_wo_section), sections="allow")
_ = assert_type(c1_0, AnyMutConfig)
c1_0 = loads(bytes_wo_section.decode(), sections="allow")
_ = assert_type(c1_0, AnyMutConfig)

c1_1 = load(BytesIO(bytes_wo_section), sections="forbid")
_ = assert_type(c1_1, MutConfig_SectionsForbidden_ScalarsAllowed)
c1_1 = loads(bytes_wo_section.decode(), sections="forbid")
_ = assert_type(c1_1, MutConfig_SectionsForbidden_ScalarsAllowed)

c1_2 = load(BytesIO(bytes_w_section), sections="require")
_ = assert_type(c1_2, MutConfig_SectionsRequired_ScalarsAllowed)
c1_2 = loads(bytes_w_section.decode(), sections="require")
_ = assert_type(c1_2, MutConfig_SectionsRequired_ScalarsAllowed)

c1_3 = load(BytesIO(bytes_wo_section), parse_scalars_as_lists=True)
_ = assert_type(c1_3, MutConfig_SectionsAllowed_ScalarsForbidden)
c1_3 = loads(bytes_wo_section.decode(), parse_scalars_as_lists=True)
_ = assert_type(c1_3, MutConfig_SectionsAllowed_ScalarsForbidden)

c1_4 = load(BytesIO(bytes_wo_section), parse_scalars_as_lists=False)
_ = assert_type(c1_4, AnyMutConfig)
c1_4 = loads(bytes_wo_section.decode(), parse_scalars_as_lists=False)
_ = assert_type(c1_4, AnyMutConfig)

# 6 cases with 2 type-narrowing arguments
c2_0 = load(BytesIO(bytes_wo_section), sections="allow", parse_scalars_as_lists=False)
_ = assert_type(c2_0, AnyMutConfig)
c2_0 = loads(bytes_wo_section.decode(), sections="allow", parse_scalars_as_lists=False)
_ = assert_type(c2_0, AnyMutConfig)

c2_1 = load(BytesIO(bytes_wo_section), sections="allow", parse_scalars_as_lists=True)
_ = assert_type(c2_1, MutConfig_SectionsAllowed_ScalarsForbidden)
c2_1 = loads(bytes_wo_section.decode(), sections="allow", parse_scalars_as_lists=True)
_ = assert_type(c2_1, MutConfig_SectionsAllowed_ScalarsForbidden)

c2_2 = load(BytesIO(bytes_wo_section), sections="forbid", parse_scalars_as_lists=False)
_ = assert_type(c2_2, MutConfig_SectionsForbidden_ScalarsAllowed)
c2_2 = loads(bytes_wo_section.decode(), sections="forbid", parse_scalars_as_lists=False)
_ = assert_type(c2_2, MutConfig_SectionsForbidden_ScalarsAllowed)

c2_3 = load(BytesIO(bytes_wo_section), sections="forbid", parse_scalars_as_lists=True)
_ = assert_type(c2_3, MutConfig_SectionsForbidden_ScalarsForbidden)
c2_3 = loads(bytes_wo_section.decode(), sections="forbid", parse_scalars_as_lists=True)
_ = assert_type(c2_3, MutConfig_SectionsForbidden_ScalarsForbidden)

c2_4 = load(BytesIO(bytes_w_section), sections="require", parse_scalars_as_lists=False)
_ = assert_type(c2_4, MutConfig_SectionsRequired_ScalarsAllowed)
c2_4 = loads(bytes_w_section.decode(), sections="require", parse_scalars_as_lists=False)
_ = assert_type(c2_4, MutConfig_SectionsRequired_ScalarsAllowed)

c2_5 = load(BytesIO(bytes_w_section), sections="require", parse_scalars_as_lists=True)
_ = assert_type(c2_5, MutConfig_SectionsRequired_ScalarsForbidden)
c2_5 = loads(bytes_w_section.decode(), sections="require", parse_scalars_as_lists=True)
_ = assert_type(c2_5, MutConfig_SectionsRequired_ScalarsForbidden)
