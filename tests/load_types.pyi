from inifix import loads
from inifix._typing import (
    AnyMutConfig,
    MutConfig_SectionsAllowed_ScalarsForbidden,
    MutConfig_SectionsForbidden_ScalarsAllowed,
    MutConfig_SectionsForbidden_ScalarsForbidden,
    MutConfig_SectionsRequired_ScalarsAllowed,
    MutConfig_SectionsRequired_ScalarsForbidden,
)

data: bytes = ...

# 1 case with 0 type-narrowing arguments
c0: AnyMutConfig = ...
c0 = loads(data.decode())

# 5 cases with 1 type-narrowing argument
c1_0: AnyMutConfig = ...
c1_0 = loads(data.decode(), sections="allow")

c1_1: MutConfig_SectionsForbidden_ScalarsAllowed = ...
c1_1 = loads(data.decode(), sections="forbid")

c1_2: MutConfig_SectionsRequired_ScalarsAllowed = ...
c1_2 = loads(data.decode(), sections="require")

c1_3: MutConfig_SectionsAllowed_ScalarsForbidden = ...
c1_3 = loads(data.decode(), parse_scalars_as_lists=True)

c1_4: AnyMutConfig = ...
c1_4 = loads(data.decode(), parse_scalars_as_lists=False)

# 6 cases with 2 type-narrowing arguments
c2_0: AnyMutConfig = ...
c2_0 = loads(data.decode(), sections="allow", parse_scalars_as_lists=False)

c2_1: MutConfig_SectionsAllowed_ScalarsForbidden = ...
c2_1 = loads(data.decode(), sections="allow", parse_scalars_as_lists=True)

c2_2: MutConfig_SectionsForbidden_ScalarsAllowed = ...
c2_2 = loads(data.decode(), sections="forbid", parse_scalars_as_lists=False)

c2_3: MutConfig_SectionsForbidden_ScalarsForbidden = ...
c2_3 = loads(data.decode(), sections="forbid", parse_scalars_as_lists=True)

c2_4: MutConfig_SectionsRequired_ScalarsAllowed = ...
c2_4 = loads(data.decode(), sections="require", parse_scalars_as_lists=False)

c2_5: MutConfig_SectionsRequired_ScalarsForbidden = ...
c2_5 = loads(data.decode(), sections="require", parse_scalars_as_lists=True)
