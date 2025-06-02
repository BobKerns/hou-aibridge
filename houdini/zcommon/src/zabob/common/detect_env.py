'''
Detect the environment in which the Zabob application is running.
'''

from enum import StrEnum
import os
from pathlib import Path
from dataclasses import dataclass, fields
from functools import cache

import click

from zabob.common import ZABOB_ROOT, VERBOSE
from zabob.common.common_paths import ZABOB_COMMON_DIR


class EnvironmentType(StrEnum):
    """
    Type for environment detection results.
    """
    PACKAGED = 'packaged'
    DEVELOPMENT = 'development'
    UNKNOWN = 'unknown'

@dataclass
class Signals:
    """
    Type for signals used in environment detection.
    """
    IN_SITE_PACKAGES: bool = False
    ENV_VAR: bool = False
    INSTALLED_PACKAGE: bool|Exception = False
    INSTALL_LOCATION:  Path| None = None
    GIT_DIRECTORY: bool = False
    PYPROJECT_TOML: bool = False
    VSCODE_CONFIG: bool = False
    WORKSPACE_FILE: bool = False
    environment_type: EnvironmentType = EnvironmentType.UNKNOWN

@cache
def detect_environment() -> Signals:
    """
    Detect if running in a packaged or development environment.

    Returns:
        - "packaged": Definitely a packaged environment
        - "development": Definitely a development environment
        - "unknown": Couldn't determine with confidence
    """
    signals = Signals()

    # Check 1: Site-packages path
    module_path = Path(__file__)
    signals.IN_SITE_PACKAGES = "site-packages" in str(module_path)

    signals.GIT_DIRECTORY = (ZABOB_ROOT / ".git").exists()
    signals.PYPROJECT_TOML = (ZABOB_COMMON_DIR / "pyproject.toml").exists()
    signals.VSCODE_CONFIG = (ZABOB_ROOT / ".vscode").exists()
    signals.WORKSPACE_FILE = (ZABOB_ROOT / "zabob.code-workspace").exists()

    # Check 3: Environment variable hint
    env_mode = os.environ.get("ZABOB_DEVELOPMENT_MODE", False)
    signals.ENV_VAR = bool(env_mode)

    # Check 4: Importlib metadata (Python 3.8+)
    try:
        import importlib.metadata
        try:
            dist = importlib.metadata.distribution("zabob")
            signals.INSTALLED_PACKAGE= True
            signals.INSTALL_LOCATION = Path(str(dist.locate_file("")))
        except importlib.metadata.PackageNotFoundError:
            signals.INSTALLED_PACKAGE = False
    except ImportError as e:
        signals.INSTALLED_PACKAGE = e

    # Decision logic
    is_packaged = (
        signals.IN_SITE_PACKAGES and
        not (signals.GIT_DIRECTORY or
              signals.PYPROJECT_TOML or
              signals.VSCODE_CONFIG or
              signals.WORKSPACE_FILE) and
        signals.INSTALLED_PACKAGE
    )

    is_development = (
        not signals.IN_SITE_PACKAGES and
        sum(1 if v else 0
            for v in (
                signals.GIT_DIRECTORY,
                signals.PYPROJECT_TOML,
                signals.VSCODE_CONFIG,
                signals.WORKSPACE_FILE
            )) >= 2
    )

    # Override with environment variable if set
    if env_mode in ("packaged", "development"):
        signals.environment_type = EnvironmentType(env_mode)
    elif is_packaged:
        signals.environment_type = EnvironmentType.PACKAGED
    elif is_development:
        signals.environment_type = EnvironmentType.DEVELOPMENT
    else:
        signals.environment_type = EnvironmentType.UNKNOWN
    return signals

def is_packaged() -> bool:
    """
    Check if Zabob is running in a packaged environment.
    """
    return detect_environment().environment_type == EnvironmentType.PACKAGED

def is_development() -> bool:
    """
    Check if Zabob is running in a development environment.
    """
    return detect_environment().environment_type == EnvironmentType.DEVELOPMENT

@click.command('environment')
@click.option("--verbose", "-v", is_flag=True,
              default = VERBOSE.enabled,
              help="Show detailed detection signals")
def check_environment(verbose):
    """Check if running in development or packaged environment."""
    signals = detect_environment()
    click.echo(f"Environment: {signals.environment_type}")
    if verbose:
        click.echo("\nDetection signals:")
        for key in fields(signals):
            click.echo(f"  {key.name}: {getattr(signals, key.name)}")

if __name__ == "__main__":
    check_environment()
