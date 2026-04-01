__all__ = ["app"]

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from difflib import unified_diff
from functools import partial
from enum import Enum, auto
from typing import TYPE_CHECKING, Literal, NewType, Callable, Any, IO, final, cast
import click
from textwrap import indent
import inifix

# TODO: replace this with except* when support for Python 3.10 is dropped
from exceptiongroup import catch, BaseExceptionGroup

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from inifix._typing import AnyConfig  # pyright: ignore[reportPrivateImportUsage]


@click.group("inifix")
def app() -> None: ...


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


@final
class Exit(click.ClickException):
    # silently exit with a non-zero exit code
    exit_code = 1

    @override
    def __init__(self) -> None:
        super().__init__("")

    @override
    def show(self, file: IO[Any] | None = None) -> None: ...  # pyright: ignore[reportExplicitAny]


def run_as_pool(closure: Callable[[str], TaskResults], files: list[str]) -> None:
    cpu_count = get_cpu_count()
    with ThreadPoolExecutor(max_workers=max(1, int(cpu_count / 2))) as executor:
        futures = [executor.submit(closure, file) for file in files]
        results = [f.result() for f in futures]

    for res in results:
        for message in res.messages:
            print(message)

    if any(res.status for res in results):
        raise Exit()


class SectionsArg(Enum):
    allow = auto()
    forbid = auto()
    require = auto()


@app.command()
@click.argument("files", nargs=-1, type=click.Path())
@click.option(
    "--sections",
    type=click.Choice(SectionsArg, case_sensitive=True),
    default="allow",
)
def validate(files: list[str], sections: SectionsArg) -> None:
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
        # mypy struggles to infer sections.name
        sections_name = cast("Literal['allow', 'forbid', 'require']", sections.name)  # pyright: ignore[reportUnnecessaryCast] # ty: ignore[redundant-cast]
        _ = inifix.load(file, sections=sections_name)
        messages.append(Message(f"Validated {file}"))

    return TaskResults(status, messages)


@app.command()
@click.argument("files", nargs=-1, type=click.Path())
@click.option(
    "--sections",
    type=click.Choice(SectionsArg, case_sensitive=True),
    default="allow",
)
@click.option(
    "--diff",
    is_flag=True,
    help="Print the unified diff to stdout instead of editing files inplace",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colors in diff outputs (this has no effect if --diff is not passed or running on Python 3.14 or earlier)",
)
@click.option(
    "--report-noop",
    is_flag=True,
    help="Explicitly log noops for files that are already formatted",
)
@click.option(
    "--skip-validation",
    is_flag=True,
    help="Skip validation step (formatting unvalidated data may lead to undefined behaviour)",
)
def format(
    files: list[str],
    sections: SectionsArg,
    diff: bool,
    no_color: bool,
    report_noop: bool,
    skip_validation: bool,
) -> None:
    """
    Format files.
    """
    run_as_pool(
        partial(
            _format_single_file,
            sections=sections,
            diff=diff,
            no_color=no_color,
            report_noop=report_noop,
            skip_validation=skip_validation,
        ),
        files,
    )


def _format_single_file(
    file: str,
    *,
    sections: SectionsArg,
    diff: bool,
    no_color: bool,
    report_noop: bool,
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
            # mypy struggles to infer sections.name
            sections_name = cast("Literal['allow', 'forbid', 'require']", sections.name)  # pyright: ignore[reportUnnecessaryCast] # ty: ignore[redundant-cast]
            validate_baseline = inifix.load(file, sections=sections_name)
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
        if sys.version_info >= (3, 15) and not no_color:
            diff_kwargs = {"color": True}
        else:
            diff_kwargs = {}  # type: ignore[var-annotated]

        diff_ = "\n".join(
            line.removesuffix("\n")
            for line in unified_diff(
                data.splitlines(),
                fmted_data.splitlines(),
                fromfile=file,
                **diff_kwargs,  # pyright: ignore[reportUnknownArgumentType]
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
