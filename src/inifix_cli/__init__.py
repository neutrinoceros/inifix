import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from difflib import unified_diff
from functools import partial
from typing import TYPE_CHECKING, Annotated, Literal
import typer
from rich.console import Console

import inifix

if TYPE_CHECKING:  # pragma: no cover
    from inifix._typing import AnyConfig

out_console: Console = Console(soft_wrap=True)
err_console: Console = Console(soft_wrap=True, stderr=True)
app: typer.Typer = typer.Typer()


@dataclass(frozen=True, slots=True)
class Message:
    content: str
    dest: Console


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
        base_cpu_count = len(os.sched_getaffinity(0))
    else:  # pragma: no cover
        # this proxy is good enough in most situations
        base_cpu_count = os.cpu_count()
    return base_cpu_count or 1


@app.command()
def validate(files: list[str]) -> None:
    """
    Validate files as inifix format-compliant.
    """
    retv = 0
    for file in files:
        if not os.path.isfile(file):
            err_console.print(f"Error: could not find {file}")
            retv = 1
            continue
        try:
            _ = inifix.load(file)
        except ValueError as exc:
            err_console.print(f"Failed to validate {file}:\n  {exc}")
            retv = 1
        else:
            out_console.print(f"Validated {file}")

    raise typer.Exit(code=retv)


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
    closure = partial(
        _format_single_file,
        diff=diff,
        report_noop=report_noop,
        skip_validation=skip_validation,
    )
    cpu_count = get_cpu_count()
    with ThreadPoolExecutor(max_workers=max(1, int(cpu_count / 2))) as executor:
        futures = [executor.submit(closure, file) for file in files]
        results = [f.result() for f in futures]

    for res in results:
        for message in res.messages:
            message.dest.print(message.content)

    if any(res.status for res in results):
        raise typer.Exit(code=1)


def _format_single_file(
    file: str, *, diff: bool, report_noop: bool, skip_validation: bool
) -> TaskResults:
    status: Literal[0, 1] = 0
    messages: list[Message] = []

    if not os.path.isfile(file):
        status = 1
        messages.append(Message(f"Error: could not find {file}", err_console))
        return TaskResults(status, messages)

    validate_baseline: AnyConfig = {}
    if not skip_validation:
        try:
            validate_baseline = inifix.load(file)
        except ValueError as exc:
            status = 1
            messages.append(Message(f"Error: {exc}", err_console))
            return TaskResults(status, messages)

    with open(file, mode="rb") as fh:
        data = fh.read().decode("utf-8")
        # make sure newlines are always decoded as \n, even on windows
        data = data.replace("\r\n", "\n")

    fmted_data = inifix.format_string(data)

    if fmted_data == data:
        if report_noop:
            # printing to stderr so that we can pipe into cdiff in --diff mode
            messages.append(Message(f"{file} is already formatted", err_console))
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
        messages.append(Message(diff_, out_console))
    else:
        status = 1
        messages.append(Message(f"Fixing {file}", err_console))
        if not os.access(file, os.W_OK):
            messages.append(
                Message(
                    f"Error: could not write to {file} (permission denied)", err_console
                )
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
                        err_console,
                    )
                )
                return TaskResults(status, messages)

            # this may still raise an error in the unlikely case of a race condition
            # (if permissions are changed between the look and the leap), but we
            # won't try to catch it unless it happens in production, because it is
            # difficult to test systematically.
            os.replace(tmpfile, file)

    return TaskResults(status, messages)


if __name__ == "__main__":  # pragma: no cover
    app()
