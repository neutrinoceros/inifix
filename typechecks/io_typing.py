import sys
from io import BytesIO

from inifix import load, loads
from inifix._typing import (
    AnyConfig,
    Config_SectionsAllowed_ScalarsForbidden,
    Config_SectionsForbidden_ScalarsAllowed,
    Config_SectionsForbidden_ScalarsForbidden,
    Config_SectionsRequired_ScalarsAllowed,
    Config_SectionsRequired_ScalarsForbidden,
)

if sys.version_info >= (3, 11):
    from typing import assert_type
else:
    from typing_extensions import assert_type

bytes_wo_section = b"pi 3.14"
bytes_w_section = b"[Title]\n" + bytes_wo_section

# 1 case with 0 type-narrowing arguments
c0 = load(BytesIO(bytes_wo_section))
_ = assert_type(c0, AnyConfig)
c0 = loads(bytes_wo_section.decode())
_ = assert_type(c0, AnyConfig)

# 5 cases with 1 type-narrowing argument
c1_0 = load(BytesIO(bytes_wo_section), sections="allow")
_ = assert_type(c1_0, AnyConfig)
c1_0 = loads(bytes_wo_section.decode(), sections="allow")
_ = assert_type(c1_0, AnyConfig)

c1_1 = load(BytesIO(bytes_wo_section), sections="forbid")
_ = assert_type(c1_1, Config_SectionsForbidden_ScalarsAllowed)
c1_1 = loads(bytes_wo_section.decode(), sections="forbid")
_ = assert_type(c1_1, Config_SectionsForbidden_ScalarsAllowed)

c1_2 = load(BytesIO(bytes_w_section), sections="require")
_ = assert_type(c1_2, Config_SectionsRequired_ScalarsAllowed)
c1_2 = loads(bytes_w_section.decode(), sections="require")
_ = assert_type(c1_2, Config_SectionsRequired_ScalarsAllowed)

c1_3 = load(BytesIO(bytes_wo_section), parse_scalars_as_lists=True)
_ = assert_type(c1_3, Config_SectionsAllowed_ScalarsForbidden)
c1_3 = loads(bytes_wo_section.decode(), parse_scalars_as_lists=True)
_ = assert_type(c1_3, Config_SectionsAllowed_ScalarsForbidden)

c1_4 = load(BytesIO(bytes_wo_section), parse_scalars_as_lists=False)
_ = assert_type(c1_4, AnyConfig)
c1_4 = loads(bytes_wo_section.decode(), parse_scalars_as_lists=False)
_ = assert_type(c1_4, AnyConfig)

# 6 cases with 2 type-narrowing arguments
c2_0 = load(BytesIO(bytes_wo_section), sections="allow", parse_scalars_as_lists=False)
_ = assert_type(c2_0, AnyConfig)
c2_0 = loads(bytes_wo_section.decode(), sections="allow", parse_scalars_as_lists=False)
_ = assert_type(c2_0, AnyConfig)

c2_1 = load(BytesIO(bytes_wo_section), sections="allow", parse_scalars_as_lists=True)
_ = assert_type(c2_1, Config_SectionsAllowed_ScalarsForbidden)
c2_1 = loads(bytes_wo_section.decode(), sections="allow", parse_scalars_as_lists=True)
_ = assert_type(c2_1, Config_SectionsAllowed_ScalarsForbidden)

c2_2 = load(BytesIO(bytes_wo_section), sections="forbid", parse_scalars_as_lists=False)
_ = assert_type(c2_2, Config_SectionsForbidden_ScalarsAllowed)
c2_2 = loads(bytes_wo_section.decode(), sections="forbid", parse_scalars_as_lists=False)
_ = assert_type(c2_2, Config_SectionsForbidden_ScalarsAllowed)

c2_3 = load(BytesIO(bytes_wo_section), sections="forbid", parse_scalars_as_lists=True)
_ = assert_type(c2_3, Config_SectionsForbidden_ScalarsForbidden)
c2_3 = loads(bytes_wo_section.decode(), sections="forbid", parse_scalars_as_lists=True)
_ = assert_type(c2_3, Config_SectionsForbidden_ScalarsForbidden)

c2_4 = load(BytesIO(bytes_w_section), sections="require", parse_scalars_as_lists=False)
_ = assert_type(c2_4, Config_SectionsRequired_ScalarsAllowed)
c2_4 = loads(bytes_w_section.decode(), sections="require", parse_scalars_as_lists=False)
_ = assert_type(c2_4, Config_SectionsRequired_ScalarsAllowed)

c2_5 = load(BytesIO(bytes_w_section), sections="require", parse_scalars_as_lists=True)
_ = assert_type(c2_5, Config_SectionsRequired_ScalarsForbidden)
c2_5 = loads(bytes_w_section.decode(), sections="require", parse_scalars_as_lists=True)
_ = assert_type(c2_5, Config_SectionsRequired_ScalarsForbidden)
