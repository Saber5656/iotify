from typer.testing import CliRunner

from iotify import __version__
from iotify.cli.main import app

runner = CliRunner()


def test_package_version() -> None:
    assert __version__ == "0.1.0.dev0"


def test_cli_version_command() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.output == "0.1.0.dev0\n"


def test_cli_default_prints_version() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert result.output == "0.1.0.dev0\n"
