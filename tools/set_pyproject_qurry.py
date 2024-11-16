"""
============================================================================
Set Pyproject Qurry (:file:`set_pyproject_qurry.py`)
============================================================================

Rename the project name in pyproject.toml from "qurry" to "qurrium".
"""

import os
import argparse
from typing import Literal, Optional
import toml


def toml_rename():
    """Rename the project name in pyproject.toml."""
    with open(os.path.join("pyproject.toml"), "r", encoding="utf8") as f:
        data = toml.load(f)
    data["project"]["name"] = "qurrium"
    print(f"| The project name in pyproject.toml is renamed to '{data['project']['name']}'.")
    with open(os.path.join("pyproject.toml"), "w", encoding="utf8") as f:
        toml.dump(data, f)
    print("| Renamed the project name in pyproject.toml.")


def toml_check(proposal_name: Optional[Literal["qurrium", "qurry"]] = None):
    """Check the project name in pyproject.toml.

    Args:
        product_name (Optional[Literal["qurrium", "qurry"]], optional):
            The product name to be checked.
            'qurrium' is the name for stable release.
            'qurry' is the name for nightly release.
            Default to None.

    """
    with open(os.path.join("pyproject.toml"), "r", encoding="utf8") as f:
        data = toml.load(f)
    project_name = data["project"]["name"]

    if proposal_name is not None:
        assert project_name == proposal_name, (
            f"| The project name in pyproject.toml is {project_name}, " + f"not {proposal_name}."
        )

    print(f"| The project name in pyproject.toml is: {project_name}")
    print("| 'qurrium' is the name for stable release.")
    print("| 'qurry' is the name for nightly release.")


class SetPyprojectArgs(argparse.Namespace):
    """The arguments for :file:`set_pyproject_qurry.py`"""

    release: Literal["stable", "nightly", "check"]
    """Choose release type: 

    - stable: the stable release.
    - nightly a.k.a. pre-release: the nightly release.
    - check: check the ptproject.toml file.

    Default to check.
    """


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="| Get the project name in pyproject.toml and rename it to 'qurrium'."
    )

    parser.add_argument(
        "-r",
        "--release",
        type=str,
        default="check",
        help="Choose release type: stable, nightly a.k.a. pre-release, check. Default to check.",
    )

    arguments = parser.parse_args()

    if arguments.release == "check":
        toml_check()
    elif arguments.release == "stable":
        toml_rename()
    elif arguments.release == "nightly":
        toml_check("qurry")
    else:
        raise ValueError(
            "| The release type should be one of the following: "
            + "stable, nightly a.k.a. pre-release, check."
            + f" Not {arguments.release}."
        )
