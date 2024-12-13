import sys
from inspect import cleandoc, getdoc
from textwrap import dedent

import pytest

import inifix

if sys.flags.optimize >= 2:  # pragma: no cover
    pytest.skip(
        reason="docstrings are not available in optimized mode 2",
        allow_module_level=True,
    )


PARSING_OPTIONS = """
    parse_scalars_as_lists: bool (default: False)
        if set to True, all values will be parses as lists of scalars,
        even for parameters comprised of a single scalar.
        This also has the effect of narrowing down the return type as seen
        by static type checkers.

        .. versionadded: 3.1.0

    integer_casting: 'stable' (default) or 'aggressive'
        casting strategy for numbers written in decimal notations, such as '1.',
        '2.0' or '3e0'. By default, perform roundtrip-stable casting (i.e., cast
        as Python floats). Setting `integer_casting='aggressive'` will instead
        parse these as Python ints, matching the behavior of inifix 4.5

        .. versionadded: 5.0.0"""

VALIDATION_OPTIONS = """
    sections: 'allow' (default), 'forbid' or 'require'
        use sections='forbid' to invalidate any section found,
        or sections='require' to invalidate a sectionless structure.
        Default mode (sections='allow') permits both.
        sections='forbid' and sections='require' both have the effect of
        narrowing down the return type as seen by static type checkers.
        This parameter has no effect at runtime when combined with
        skip_validation=True.

        .. versionadded: 5.1.0

    skip_validation: bool (default: False)
        if set to True, input is not validated. This can be used to speedup
        io operations trusted input or to work around bugs with the validation
        routine. Use with caution.
        This parameter intentionally has no effect on static type checking.

        .. versionadded: 4.1.0"""

DUMP_DOCSTRING = cleandoc(
    f"""
    Write data to a file.

    Parameters
    ----------
    data: dict
        has to be inifix format-compliant

    file: any of the following
        - the name of a file to write to (str, bytes or os.PathLike)
        - a writable handle. Both text and binary file modes are supported,
          though binary is preferred.
          In binary mode, data is encoded as UTF-8.
    {VALIDATION_OPTIONS}

    See Also
    --------
    inifix.dumps
    """
)

DUMPS_DOCSTRING = cleandoc(
    f"""
    Convert data to a string.

    Parameters
    ----------
    data: dict
        has to be inifix format-compliant
    {VALIDATION_OPTIONS}

    Returns
    -------
    string representing the content of a parameter file

    See Also
    --------
    inifix.dump
    """
)


LOAD_DOCSTRING = cleandoc(
    f"""
    Parse data from a file.

    Parameters
    ----------
    source: any of the following
        - the name of a file to read from, (str, bytes or os.PathLike)
        - a readable handle. Both text and binary file modes are supported,
          though binary is preferred.
          In binary mode, we assume UTF-8 encoding.
    {PARSING_OPTIONS}
    {VALIDATION_OPTIONS}

    See Also
    --------
    inifix.loads
    """
)

LOADS_DOCSTRING = cleandoc(
    f"""
    Parse data from a string.

    Parameters
    ----------
    source: str
        The content of a parameter file (has to be inifix format-compliant)
    {PARSING_OPTIONS}
    {VALIDATION_OPTIONS}

    See Also
    --------
    inifix.load
    """
)


@pytest.mark.parametrize(
    "func, expected_docstring",
    [
        (inifix.load, LOAD_DOCSTRING),
        (inifix.loads, LOADS_DOCSTRING),
        (inifix.dump, DUMP_DOCSTRING),
        (inifix.dumps, DUMPS_DOCSTRING),
    ],
)
def test_docstrings(func, expected_docstring):
    assert getdoc(func) == dedent(expected_docstring)
