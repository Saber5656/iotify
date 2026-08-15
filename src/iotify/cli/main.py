"""Minimal CLI entry point for the initial package scaffold."""

from typing import Annotated

import typer

from iotify import __version__

app = typer.Typer(
    add_completion=False,
    help="Camera-based retrofit IoT kit.",
    invoke_without_command=True,
)


@app.callback()
def main(
    ctx: typer.Context,
    version_flag: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Print the package version and exit.",
        ),
    ] = False,
) -> None:
    """Run the iotify CLI."""
    if version_flag or ctx.invoked_subcommand is None:
        typer.echo(__version__)
        raise typer.Exit()


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)
