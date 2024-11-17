"""
============================================================================
Set Version (:file:`set_version.py`)
============================================================================

Get the version number from the VERSION.txt file and pass it to the environment variable.

- This script is shared with :package:`qurrium` and :package:`qurecipe` repositories.
"""

import os
import sys
import argparse
from typing import Literal, Optional
import warnings
import subprocess
from pep440.core import is_canonical

print("| Getting package name ...")
with open(os.path.join("tools", "package_name.txt"), encoding="utf-8") as package_name_file:
    PACKAGE_NAME = package_name_file.read().strip()
print(f"| Get package name: '{PACKAGE_NAME}'")
print("| Ready to get the version number ...")
print("=" * 50)


def read_all_versions_from_git():
    """Read all the versions from the VERSION.txt file.

    Returns:
        list[str]: The raw version numbers.
    """
    get_all_tags = subprocess.check_output(["git", "fetch", "--tags"]).strip()
    get_all_tags = get_all_tags.decode("utf-8")
    print(get_all_tags)

    all_versions_read = subprocess.check_output(["git", "tag", "-l"]).strip()
    all_versions_read = all_versions_read.decode("utf-8")
    all_versions = all_versions_read.split("\n")

    return all_versions


def formatted_version(
    raw_all_versions: list[str],
) -> tuple[list[str], dict[str, str]]:
    """Format the version numbers.

    Args:
        raw_all_versions (list[str]): The raw version numbers.

    Returns:
        tuple[list[str] dict[str, str]]:
            The formatted version numbers and
            the dictionary of formatted and unformatted version numbers.
    """

    formatted_all_versions_dict = {}

    for vers in raw_all_versions:
        if "." not in vers:
            continue

        v_removed = vers[1:] if vers[0] == "v" else vers
        if "-beta0" in v_removed:
            v_removed = v_removed.replace("-beta0", ".dev")
        elif "-beta" in v_removed:
            v_removed = v_removed.replace("-beta", ".dev")
        elif "-dev0" in v_removed:
            v_removed = v_removed.replace("-dev0", ".dev")
        elif ".rc" in v_removed:
            v_removed = v_removed.replace("-rc", ".dev")
        elif ".0b0" in v_removed:
            v_removed = v_removed.replace(".0b0", ".0.dev")
        elif ".0b" in v_removed:
            v_removed = v_removed.replace(".0b", ".0.dev")

        if is_canonical(v_removed):
            formatted_all_versions_dict[v_removed] = vers

    formatted_all_versions = list(formatted_all_versions_dict.keys())

    return formatted_all_versions, formatted_all_versions_dict


def build_version_tree(
    formatted_all_versions: list[str],
) -> dict[str, dict[str, dict[str, list[str]]]]:
    """Build the version tree with fine sorting.

    Args:
        formatted_all_versions (list[str]): The formatted version numbers.

    Returns:
        dict[str, dict[str, dict[str, list[str]]]]: The version tree with fine sorting.
    """

    unsorted_version_tree = {}

    for vers in formatted_all_versions:
        vers_split = vers.split(".")
        assert (
            3 <= len(vers_split) < 5
        ), f"| Expect at 3 or 4 versions split parts, got {vers_split}"
        if vers_split[0] not in unsorted_version_tree:
            unsorted_version_tree[vers_split[0]] = {}
        if vers_split[1] not in unsorted_version_tree[vers_split[0]]:
            unsorted_version_tree[vers_split[0]][vers_split[1]] = {}
        if vers_split[2] not in unsorted_version_tree[vers_split[0]][vers_split[1]]:
            unsorted_version_tree[vers_split[0]][vers_split[1]][vers_split[2]] = []

        unsorted_version_tree[vers_split[0]][vers_split[1]][vers_split[2]].append(
            "0" if len(vers_split) == 3 else vers_split[3]
        )

    def basic_sort_lambda(x: str):
        return int(x)

    def dev_part_sort_lambda(x: str):
        return 1000 + int(x[3:]) if x.startswith("dev") else int(x)

    sorted_version_tree = {}
    for major in sorted(unsorted_version_tree.keys(), key=basic_sort_lambda):
        sorted_version_tree[major] = {}

        for minor in sorted(unsorted_version_tree[major].keys(), key=basic_sort_lambda):
            sorted_version_tree[major][minor] = {}

            for patch in sorted(unsorted_version_tree[major][minor].keys(), key=basic_sort_lambda):
                sorted_version_tree[major][minor][patch] = sorted(
                    unsorted_version_tree[major][minor][patch],
                    key=dev_part_sort_lambda,
                )

    return sorted_version_tree


def fine_sorted_tree_to_list(version_tree: dict[str, dict[str, dict[str, list[str]]]]):
    """Convert the version tree to a fine sorted list.

    Args:
        version_tree (dict[str, dict[str, dict[str, list[str]]]]): The version tree.

    Returns:
        list[str]: The fine sorted list.
    """

    fine_sorted_list = []
    for major in version_tree:
        for minor in version_tree[major]:
            for patch in version_tree[major][minor]:
                for dev_part in version_tree[major][minor][patch]:
                    fine_sorted_list.append(
                        f"{major}.{minor}.{patch}" + ("" if dev_part == "0" else f".{dev_part}")
                    )

    return fine_sorted_list


def validate_version_format(raw_read_version_txt: str) -> list[str]:
    """Read the version number from the VERSION.txt file.

    Args:
        raw_read_version_txt (str): The raw version number read from the file.

    Returns:
        list[str]: The version number split by dot.
    """

    # Check whether the version number is canonical for pep440
    if not is_canonical(raw_read_version_txt):
        raise ValueError("| The version number should be canonical: " + f"{raw_read_version_txt}.")

    version_split = raw_read_version_txt.split(".")

    # Check whether the version number is canonical for project requirement
    if any(not part.isdigit() for part in version_split[:3]):
        raise ValueError(
            "| The version number should be all digits in first 3 parts: " + f"{version_split}."
        )

    if len(version_split) == 3:
        return version_split

    if len(version_split) == 4:
        if not version_split[3].startswith("dev"):
            raise ValueError(
                "| The version number should have 'dev' in the last part: " + f"{version_split}."
            )
        return version_split

    raise ValueError(
        "| The version number should be split by dot and have 3 or 4 parts: " + f"{version_split}."
    )


with open(os.path.join(PACKAGE_NAME, "VERSION.txt"), encoding="utf-8") as version_file:
    RAW_VERSION_TXT = version_file.read().strip()

VERSION_SPLIT = validate_version_format(RAW_VERSION_TXT)
"""The version number split by dot"""
PROPOSED_VERSION = ".".join(VERSION_SPLIT[:3])
"""The proposed version number without the dev part"""

print(f"| Get raw version: {RAW_VERSION_TXT}")
print(f"| Get version split: {VERSION_SPLIT}")

RAWREAD_ALL_GIT_VERSIONS = read_all_versions_from_git()
"""The version numbers read from the git tags"""

FORMATTED_ALL_VERSIONS, FORMATTED_ALL_VERSIONS_DICT = formatted_version(RAWREAD_ALL_GIT_VERSIONS)
"""The formatted version numbers and the dictionary of formatted and unformatted version numbers"""

FINE_SORT_VERSION_TREE = build_version_tree(FORMATTED_ALL_VERSIONS)
"""The version tree with fine sorting"""

FINE_SORTED_LIST = fine_sorted_tree_to_list(FINE_SORT_VERSION_TREE)
"""The fine sorted list"""


def is_existing_version(version: str) -> bool:
    """Check whether the version is existing in the git tags.

    Args:
        version (str): The version number.

    Returns:
        bool: Whether the version is existing.
    """
    return version in FORMATTED_ALL_VERSIONS_DICT


def similar_version_by_stable_version(stable_version: str) -> list[str]:
    """Get the similar version numbers by the stable version number.

    Args:
        stable_version (str): The stable version number.

    Returns:
        list[str]: The similar version numbers.
    """
    similars = []

    for version in FORMATTED_ALL_VERSIONS:
        if version.startswith(stable_version):
            similars.append(version)

    return similars


def last_stable_version(
    current_stable_version: str, bump: Literal["major", "minor", "patch"]
) -> str:
    """Get the last stable version number by the current stable version number.

    Args:
        current_stable_version (str): The current stable version number.
        bump (Literal["major", "minor", "patch"]): The bump type.

    Returns:
        str: The last stable version number.

    Raises:
        ValueError: When the bump type is not in ["major", "minor", "patch"].
    """

    stable_version_split = current_stable_version.split(".")
    if bump == "major":
        return f"{int(stable_version_split[0]) - 1}.0.0"
    if bump == "minor":
        return f"{stable_version_split[0]}.{int(stable_version_split[1]) - 1}.0"
    if bump == "patch":
        return (
            f"{stable_version_split[0]}.{stable_version_split[1]}."
            + f"{int(stable_version_split[2]) - 1}"
        )

    raise ValueError("| The bump type should be either 'major', 'minor', or 'patch': " + f"{bump}.")


def bump_version(
    version_split: list[str],
    bump_type: Literal["major", "minor", "patch", "dev"],
) -> tuple[str, str, str, str]:
    """Bump the version number.
    The version number is split by dot, and the release type is either stable or nightly.
    And it can be bumped by major, minor, patch, or dev.
    The input 'version_split' is the version number split by dot,
    and it should be looked like ['0', '3', '0', 'dev1'].

    Args:
        version_split (list[str]): The version number split by dot.
        bump_type (Literal["major", "minor", "patch", "dev"]):
            The bump type of the version number.
            "skip" means the version number is not bumped.

    Returns:
        tuple[str, str, str, str]: The bumped version number
    """
    assert (
        len(version_split) == 3 or len(version_split) == 4
    ), f"| The version number should be split by dot and have 3 or 4 parts: {version_split}."

    if bump_type == "dev":
        version_new_split = (
            (version_split[:2] + [str(int(version_split[2]) + 1)] + ["dev1"])
            if len(version_split) == 3
            else (version_split[:3] + ["dev" + str(int(version_split[3][3:]) + 1)])
        )

    elif bump_type == "patch":
        version_new_split = version_split[:2] + [str(int(version_split[2]) + 1)] + ["dev1"]

    elif bump_type == "minor":
        version_new_split = version_split[:1] + [str(int(version_split[1]) + 1)] + ["0", "dev1"]

    elif bump_type == "major":
        raise NotImplementedError("| The major bump are only allowed by bumping manually.")

    else:
        raise ValueError(
            "| The bump type should be one of the following: "
            + f"major, minor, patch, dev, or skip, but got: '{bump_type}'."
        )

    assert (
        len(version_new_split) == 4
    ), f"| The bumped version number should have 4 parts: {version_new_split}."
    return (version_new_split[0], version_new_split[1], version_new_split[2], version_new_split[3])


class SetVersionArgs(argparse.Namespace):
    """The arguments for :file:`set_version.py`"""

    release: Literal["stable", "nightly", "check"]
    """Choose release type: 

    - stable: the stable release.
    - nightly a.k.a. pre-release: the nightly release.
    - check: check the version number without changing the version.

    Default to check.
    """
    test: bool
    """Test the versioning without changing the version. Default to False."""
    bump: Literal["major", "minor", "patch", "dev", "skip"]
    """Bump the version number. Default to skip."""


def finished(
    exists: bool,
    version: str,
    version_txt_path: Optional[str],
    exit_code: int = 0,
    test: bool = False,
):
    """Finish the versioning process.

    Args:
        exists (bool): Whether the version is existing.
        version (str): The version number.
        version_txt_path (str): The path to the VERSION.txt file.
        exit_code (int, optional): The exit code. Defaults to 0.

    """

    output_exists = "true" if exists else "false"
    if test:
        print(f"exists={output_exists}")
        print(f"VERSION={version}")
    else:
        os.system(f'echo "exists={output_exists}" >> $GITHUB_OUTPUT')
        os.system(f'echo "VERSION={version}" >> $GITHUB_OUTPUT')

    if version_txt_path is not None and not test:
        with open(version_txt_path, "w", encoding="utf-8") as version_file_output:
            version_file_output.write(version)

    sys.exit(exit_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="| Get the version number from the VERSION.txt "
        + "file and pass it to the environment variable."
    )

    parser.add_argument(
        "-r",
        "--release",
        type=str,
        default="check",
        help="Choose release type: stable, nightly a.k.a. pre-release, check. Default to check.",
    )
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Test the versioning without changing the version. Default to False.",
    )
    parser.add_argument(
        "-b",
        "--bump",
        type=str,
        default="skip",
        help="Bump the version number. Default to skip.",
    )

    arguments = parser.parse_args()

    if arguments.bump not in ["major", "minor", "patch", "dev", "skip"]:
        raise ValueError(
            "| The bump type should be one of the following: "
            + "major, minor, patch, dev, or skip, but got: "
            + f"'{arguments.bump}'."
        )

    if arguments.release == "stable":
        print("=" * 50)
        print("| The stable release.")
        print("=" * 50)
        print("| The stable release is used for the final release.")

        if arguments.bump != "skip":
            raise ValueError(
                "| The stable release should not bump the version number. "
                + f"bump type: {arguments.bump}, release type: {arguments.release}"
            )

        similar_versions = similar_version_by_stable_version(PROPOSED_VERSION)
        if len(similar_versions) == 0:
            print(f"| The proposed version: {PROPOSED_VERSION} has no any dev versions.")
            print(f"| Similar versions: {similar_versions}")
            raise ValueError(
                "| Any stable release should have the dev version, "
                + f"but not found any dev versions of '{PROPOSED_VERSION}', "
                + f"bump type: {arguments.bump}, release type: {arguments.release}"
            )

        if is_existing_version(PROPOSED_VERSION):
            print(f"| The proposed version: {PROPOSED_VERSION} is existing.")
            print(f"| Similar versions: {similar_versions}")
            print("| So we do not create the tag and release for the existing version.")
            print("| Just merging in this pull request closed.")
            print(
                "| You need to bump the version number "
                + "when merge from branch 'dev' to 'pre-release'."
            )

            finished(
                exists=True,
                version=PROPOSED_VERSION,
                version_txt_path=os.path.join(PACKAGE_NAME, "VERSION.txt"),
                test=arguments.test,
            )

        print(f"| The proposed version: {PROPOSED_VERSION} is not existing.")
        print(f"| Similar versions: {similar_versions}")
        print("| So we create the tag and release for the new version.")

        finished(
            exists=False,
            version=PROPOSED_VERSION,
            version_txt_path=os.path.join(PACKAGE_NAME, "VERSION.txt"),
            test=arguments.test,
        )

    if arguments.release == "check":
        print("=" * 50)
        print("| The versioning check.")
        print("=" * 50)
        print("| The versioning checking is used for testing before the pull request.")
        print("| Confirm that the version number is still the last version in git version.")
        print("| Wait for the bumping version after the pull request.")

        VERSION = ".".join(VERSION_SPLIT)
        if arguments.bump != "skip":
            warnings.warn(
                "| The versioning check should not bump the version number."
                + f"bump type: {arguments.bump}, release type: {arguments.release}"
            )

        if len(VERSION_SPLIT) == 3:
            if not is_existing_version(PROPOSED_VERSION):
                raise ValueError(
                    f"| The version from the VERSION.txt is stable version {VERSION}. "
                    + "This means that it should be existing in the git tags "
                    + "and waiting for for the version bumping after the pull request. "
                    + f"all versions: {RAWREAD_ALL_GIT_VERSIONS}"
                )
        elif len(VERSION_SPLIT) == 4:
            if not is_existing_version(VERSION):
                raise ValueError(
                    "| The version from the VERSION.txt is "
                    + f"nightly version {VERSION} for proposed {PROPOSED_VERSION}. "
                    + f"This means the version {VERSION} should be existing in the git tags "
                    + "for it has added last pull request. "
                    + f"If this version {VERSION} is made by you, "
                    + "you should recover to last version to make the workflow bump the version. "
                    + f"all versions: {RAWREAD_ALL_GIT_VERSIONS}"
                )
        else:
            raise ValueError(
                f"| The version number should have 3 or 4 parts, but got: {VERSION_SPLIT}."
            )

        print("| The versioning check is done.")
        finished(
            exists=False,
            version=VERSION,
            version_txt_path=os.path.join(PACKAGE_NAME, "VERSION.txt"),
            exit_code=0,
            test=arguments.test,
        )

    if arguments.release != "nightly":
        raise ValueError(
            "| The release type should be one of the following: "
            + "stable, nightly, or check, but got: "
            + f"'{arguments.release}'."
        )

    print("=" * 50)
    print("| The nightly release.")
    print("=" * 50)

    if arguments.bump == "skip":
        print("| The version number is not bumped.")
        print("| The version number is not changed.")
        finished(
            exists=False,
            version=".".join(VERSION_SPLIT),
            version_txt_path=os.path.join(PACKAGE_NAME, "VERSION.txt"),
            test=arguments.test,
        )
    assert arguments.bump != "skip", "| The bump type should not be 'skip' when not stable release."

    VERSION_SPLIT = bump_version(VERSION_SPLIT, arguments.bump)
    print(f"| Bump '{arguments.bump}' version: {'.'.join(VERSION_SPLIT)}")
    VERSION = ".".join(VERSION_SPLIT)
    if is_existing_version(VERSION):
        raise ValueError(f"| The version {VERSION} is already existing in the git tags.")

    finished(
        exists=False,
        version=VERSION,
        version_txt_path=os.path.join(PACKAGE_NAME, "VERSION.txt"),
        test=arguments.test,
    )
