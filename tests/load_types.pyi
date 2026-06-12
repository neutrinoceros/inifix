from io import BytesIO

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
c0: AnyMutConfig = load(BytesIO(bytes_wo_section))
c0 = loads(bytes_wo_section.decode())

# 5 cases with 1 type-narrowing argument
c1_0: AnyMutConfig = load(BytesIO(bytes_wo_section), sections="allow")
c1_0 = loads(bytes_wo_section.decode(), sections="allow")

c1_1: MutConfig_SectionsForbidden_ScalarsAllowed = load(
    BytesIO(bytes_wo_section), sections="forbid"
)
c1_1 = loads(bytes_wo_section.decode(), sections="forbid")

c1_2: MutConfig_SectionsRequired_ScalarsAllowed = load(
    BytesIO(bytes_w_section), sections="require"
)
c1_2 = loads(bytes_w_section.decode(), sections="require")

c1_3: MutConfig_SectionsAllowed_ScalarsForbidden = load(
    BytesIO(bytes_wo_section), parse_scalars_as_lists=True
)
c1_3 = loads(bytes_wo_section.decode(), parse_scalars_as_lists=True)

c1_4: AnyMutConfig = load(BytesIO(bytes_wo_section), parse_scalars_as_lists=False)
c1_4 = loads(bytes_wo_section.decode(), parse_scalars_as_lists=False)

# 6 cases with 2 type-narrowing arguments
c2_0: AnyMutConfig = load(
    BytesIO(bytes_wo_section), sections="allow", parse_scalars_as_lists=False
)
c2_0 = loads(bytes_wo_section.decode(), sections="allow", parse_scalars_as_lists=False)

c2_1: MutConfig_SectionsAllowed_ScalarsForbidden = load(
    BytesIO(bytes_wo_section), sections="allow", parse_scalars_as_lists=True
)
c2_1 = loads(bytes_wo_section.decode(), sections="allow", parse_scalars_as_lists=True)

c2_2: MutConfig_SectionsForbidden_ScalarsAllowed = load(
    BytesIO(bytes_wo_section), sections="forbid", parse_scalars_as_lists=False
)
c2_2 = loads(bytes_wo_section.decode(), sections="forbid", parse_scalars_as_lists=False)

c2_3: MutConfig_SectionsForbidden_ScalarsForbidden = load(
    BytesIO(bytes_wo_section), sections="forbid", parse_scalars_as_lists=True
)
c2_3 = loads(bytes_wo_section.decode(), sections="forbid", parse_scalars_as_lists=True)

c2_4: MutConfig_SectionsRequired_ScalarsAllowed = load(
    BytesIO(bytes_w_section), sections="require", parse_scalars_as_lists=False
)
c2_4 = loads(bytes_w_section.decode(), sections="require", parse_scalars_as_lists=False)

c2_5: MutConfig_SectionsRequired_ScalarsForbidden = load(
    BytesIO(bytes_w_section), sections="require", parse_scalars_as_lists=True
)
c2_5 = loads(bytes_w_section.decode(), sections="require", parse_scalars_as_lists=True)
