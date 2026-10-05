"""Compare the gemspy==X.Y.Z pin in pyproject.toml with the latest stable gemspy release on PyPI.

Writes `current`, `latest` and `update` to $GITHUB_OUTPUT (used by .github/workflows/check-gemspy-update.yml).
Run with: uv run --no-project --python 3.11 --with packaging .github/scripts/check_gemspy_update.py
"""

import json
import os
import tomllib
import urllib.request

from packaging.requirements import Requirement
from packaging.utils import (
    InvalidSdistFilename,
    InvalidWheelFilename,
    canonicalize_name,
    parse_sdist_filename,
    parse_wheel_filename,
)
from packaging.version import InvalidVersion, Version

PYPI_SIMPLE_URL = "https://pypi.org/simple/gemspy/"


def pinned_version() -> Version:
    with open("pyproject.toml", "rb") as f:
        dependencies = tomllib.load(f)["project"]["dependencies"]

    pins = [
        spec.version
        for requirement in map(Requirement, dependencies)
        if canonicalize_name(requirement.name) == "gemspy"
        for spec in requirement.specifier
        if spec.operator == "=="
    ]
    try:
        if len(pins) == 1:
            return Version(pins[0])
    except InvalidVersion:
        pass
    raise SystemExit("ERROR: expected exactly one 'gemspy==X.Y.Z' pin in pyproject.toml")


def latest_stable_version() -> Version:
    request = urllib.request.Request(PYPI_SIMPLE_URL, headers={"Accept": "application/vnd.pypi.simple.v1+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        files = json.load(response)["files"]

    # A release is available if at least one of its files is not yanked
    available = set()
    for file in files:
        if file.get("yanked"):
            continue
        filename = file["filename"]
        try:
            if filename.endswith(".whl"):
                available.add(parse_wheel_filename(filename)[1])
            else:
                available.add(parse_sdist_filename(filename)[1])
        except (InvalidWheelFilename, InvalidSdistFilename, InvalidVersion):
            print(f"Skipping unrecognized file: {filename}")

    stable = [version for version in available if not version.is_prerelease]
    if not stable:
        raise SystemExit("ERROR: no stable GemsPy release found on PyPI")
    return max(stable)


def main() -> None:
    current = pinned_version()
    latest = latest_stable_version()
    update = latest > current

    print(f"Pinned version: {current}  |  Latest version: {latest}")
    print("New version detected." if update else "Already up to date.")
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"current={current}\n")
        output.write(f"latest={latest}\n")
        output.write(f"update={str(update).lower()}\n")


if __name__ == "__main__":
    main()
