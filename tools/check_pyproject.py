"""Set Pyproject Qurrium (:file:`set_pyproject_qurry.py`)

Check the project name in pyproject.toml.
Since the version 1.0.0, the project name is unify as "qurrium" for both stable and nightly release.
This function is used to check the project name in pyproject.toml.
"""

import os
import argparse
import toml


def toml_check():
    """Check the project name in pyproject.toml.
    Since the version 1.0.0, the project name is unify as "qurrium"
    for both stable and nightly release.

    This function is used to check the project name in pyproject.toml.
    """
    with open(os.path.join("pyproject.toml"), "r", encoding="utf8") as f:
        data = toml.load(f)
    project_name = data["project"]["name"]

    assert project_name == "qurrium", (
        f"| The project name in pyproject.toml is {project_name}, not 'qurrium'."
    )

    print(f"| The project name in pyproject.toml is: {project_name}")
    print("| 'qurrium' is the name for both stable and nightly releases.")


class SetPyprojectArgs(argparse.Namespace):
    """Arguments for check_pyproject.py"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="| Get the project name in pyproject.toml and rename it to 'qurrium'."
    )

    toml_check()
