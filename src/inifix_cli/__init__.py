import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from difflib import unified_diff
from functools import partial
from typing import TYPE_CHECKING, Annotated, Literal, NewType, Callable
from enum import Enum
import typer
from textwrap import indent
import inifix

# TODO: replace this with except* when support for Python 3.10 is dropped
from exceptiongroup import catch, BaseExceptionGroup

if TYPE_CHECKING:  # pragma: no cover
    from inifix._typing import AnyConfig  # pyright: ignore[reportPrivateImportUsage]


__all__ = ["app"]

app: typer.Typer = typer.Typer()


Message = NewType("Message", str)


@dataclass(frozen=True, slots=True)
class TaskResults:
    status: Literal[0, 1]
    messages: list[Message]


def get_cpu_count() -> int:
    # this function exists primarily to be mocked
    # instead of something we don't own
    base_cpu_count: int | None
    if sys.version_info >= (3, 13):
        base_cpu_count = os.process_cpu_count()
    elif hasattr(os, "sched_getaffinity"):
        # this function isn't available on all platforms
        base_cpu_count = len(os.sched_getaffinity(0))  # pyright: ignore[reportAttributeAccessIssue]
    else:  # pragma: no cover
        # this proxy is good enough in most situations
        base_cpu_count = os.cpu_count()
    return base_cpu_count or 1


def run_as_pool(closure: Callable[[str], TaskResults], files: list[str]) -> None:
    cpu_count = get_cpu_count()
    with ThreadPoolExecutor(max_workers=max(1, int(cpu_count / 2))) as executor:
        futures = [executor.submit(closure, file) for file in files]
        results = [f.result() for f in futures]

    for res in results:
        for message in res.messages:
            print(message)

    if any(res.status for res in results):
        raise typer.Exit(code=1)


class SectionsArg(str, Enum):
    allow = "allow"
    forbid = "forbid"
    require = "require"


@app.command()
def validate(files: list[str], sections: SectionsArg = SectionsArg.allow) -> None:
    """
    Validate files as inifix format-compliant.
    """
    run_as_pool(partial(_validate_single_file, sections=sections), files)


def _validate_single_file(file: str, sections: SectionsArg) -> TaskResults:
    status: Literal[0, 1] = 0
    messages: list[Message] = []
    if not os.path.isfile(file):
        status = 1
        messages.append(Message(f"Error: could not find {file}"))
        return TaskResults(status, messages)

    # TODO: rewrite this section with try/except*/else when support for Python 3.10 is dropped
    def value_error_handler(exc: BaseExceptionGroup[Exception]) -> None:
        nonlocal status
        status = 1
        exc_repr = "\n".join(str(e) for e in exc.exceptions)
        messages.append(
            Message(f"Failed to validate {file}:\n{indent(exc_repr, '  ')}")
        )

    with catch({ValueError: value_error_handler}):
        _ = inifix.load(file, sections=sections.value)
        messages.append(Message(f"Validated {file}"))

    return TaskResults(status, messages)


@app.command()
def format(
    files: list[str],
    *,
    diff: Annotated[
        bool,
        typer.Option(
            "--diff",
            help="Print the unified diff to stdout instead of editing files inplace",
        ),
    ] = False,
    report_noop: Annotated[
        bool,
        typer.Option(
            "--report-noop",
            help="Explicitly log noops for files that are already formatted",
        ),
    ] = False,
    sections: Annotated[
        SectionsArg,
        typer.Option(
            "--sections",
            help=(
                "whether to 'allow' (default), 'forbid' or 'require' sections "
                "during validation ('allow' and has no effect). "
                "This option is without effect when combined with --skip-validataion"
            ),
        ),
    ] = SectionsArg.allow,
    skip_validation: Annotated[
        bool,
        typer.Option(
            "--skip-validation",
            help="Skip validation step (formatting unvalidated data may lead to undefined behaviour)",
        ),
    ] = False,
) -> None:
    """
    Format files.
    """
    run_as_pool(
        partial(
            _format_single_file,
            diff=diff,
            report_noop=report_noop,
            sections=sections,
            skip_validation=skip_validation,
        ),
        files,
    )


def _format_single_file(
    file: str,
    *,
    diff: bool,
    report_noop: bool,
    sections: SectionsArg,
    skip_validation: bool,
) -> TaskResults:
    status: Literal[0, 1] = 0
    messages: list[Message] = []

    if not os.path.isfile(file):
        status = 1
        messages.append(Message(f"Error: could not find {file}"))
        return TaskResults(status, messages)

    validate_baseline: AnyConfig = {}
    if not skip_validation:
        # TODO: rewrite this section with try/except* when support for Python 3.10 is dropped
        def value_error_handler(exc: BaseExceptionGroup[Exception]) -> None:
            nonlocal status
            status = 1
            exc_repr = "\n".join(str(e) for e in exc.exceptions)
            messages.append(
                Message(f"Failed to format {file}:\n{indent(exc_repr, '  ')}")
            )

        with catch({ValueError: value_error_handler}):
            validate_baseline = inifix.load(file, sections=sections.value)
        if status != 0:
            return TaskResults(status, messages)

    with open(file, mode="rb") as fh:
        data = fh.read().decode("utf-8")
        # make sure newlines are always decoded as \n, even on windows
        data = data.replace("\r\n", "\n")

    fmted_data = inifix.format_string(data)

    if fmted_data == data:
        if report_noop:
            # printing to stderr so that we can pipe into cdiff in --diff mode
            messages.append(Message(f"{file} is already formatted"))
        return TaskResults(status, messages)

    if diff:
        diff_ = "\n".join(
            line.removesuffix("\n")
            for line in unified_diff(
                data.splitlines(), fmted_data.splitlines(), fromfile=file
            )
        )
        assert diff_
        status = 1
        messages.append(Message(diff_))
    else:
        status = 1
        messages.append(Message(f"Fixing {file}"))
        if not os.access(file, os.W_OK):
            messages.append(
                Message(f"Error: could not write to {file} (permission denied)")
            )
            return TaskResults(status, messages)

        from tempfile import TemporaryDirectory

        with TemporaryDirectory(dir=os.path.dirname(file)) as tmpdir:
            tmpfile = os.path.join(tmpdir, "ini")
            with open(tmpfile, "wb") as bfh:
                _ = bfh.write(fmted_data.encode("utf-8"))

            if (
                not skip_validation and inifix.load(tmpfile) != validate_baseline
            ):  # pragma: no cover
                messages.append(
                    Message(
                        f"Error: failed to format {file}: "
                        "formatted data compares unequal to unformatted data",
                    )
                )
                return TaskResults(status, messages)

            # this may still raise an error in the unlikely case of a race condition
            # (if permissions are changed between the look and the leap), but we
            # won't try to catch it unless it happens in production, because it is
            # difficult to test systematically.
            os.replace(tmpfile, file)

    return TaskResults(status, messages)
