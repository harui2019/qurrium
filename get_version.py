"""
Get the version number from the VERSION.txt file and pass it to the environment variable.
"""

import os
import argparse
from typing import Literal
import toml

with open(os.path.join("qurry", "VERSION.txt"), encoding="utf-8") as version_file:
    raw_version_txt = version_file.read().strip()

version_txt_split = raw_version_txt.split(".")
print(f"| Get raw version: {raw_version_txt}")
print(f"| Get version split: {version_txt_split}")


class MyProgramArgs(argparse.Namespace):
    """args"""

    release: Literal["stable", "nightly"]
    test: bool
    bump: Literal["major", "minor", "patch", "dev"]


def toml_rename():
    """Rename the project name in pyproject.toml."""
    with open(os.path.join("pyproject.toml"), "r", encoding="utf8") as f:
        data = toml.load(f)
    data["project"]["name"] = "qurrium"
    with open(os.path.join("pyproject.toml"), "w", encoding="utf8") as f:
        toml.dump(data, f)


def bump_version(
    version_split: list[str],
    bump_type: Literal["major", "minor", "patch", "dev", "skip"],
) -> list[str]:
    """Bump the version number.
    The version number is split by dot, and the release type is either stable or nightly.
    And it can be bumped by major, minor, patch, or dev.
    The input 'version_split' is the version number split by dot,
    and it should be looked like ['0', '8', '1', 'dev2'].

    version_split: list[str]
        The version number split by dot.
    bump_type: Literal["major", "minor", "patch", "dev", "skip"]
        The bump type of the version number.
        "skip" means the version number is not bumped.

    Returns:
        str: The bumped version number
    """
    assert (
        len(version_split) == 4
    ), f"| The version number should be split by dot and have 4 parts: {version_split}."

    if bump_type == "dev":
        version_new_split = version_split[:3] + ["dev" + str(int(version_split[3][3:]) + 1)]

    elif bump_type == "patch":
        version_new_split = version_split[:2] + [str(int(version_split[2]) + 1)] + ["dev1"]

    elif bump_type in ["major", "minor"]:
        raise NotImplementedError(
            "| The major and minor bump are only allowed by bumping manually."
        )
    elif bump_type == "skip":
        version_new_split = version_split
    else:
        raise ValueError(
            "| The bump type should be one of the following: " + "major, minor, patch, dev."
        )

    assert (
        len(version_new_split) == 4
    ), f"| The bumped version number should have 4 parts: {version_new_split}."
    return version_new_split


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="| Get the version number from the VERSION.txt "
        + "file and pass it to the environment variable."
    )
    parser.add_argument(
        "-r",
        "--release",
        type=str,
        default="nightly",
        help="Choose release type: stable, nightly(aka pre-release, default)",
    )
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="Test the get_version.py script.",
    )
    parser.add_argument(
        "-b",
        "--bump",
        type=str,
        default="skip",
        help="Bump the version number.",
    )

    args = parser.parse_args()

    if args.release not in ["stable", "nightly"]:
        raise ValueError(
            "| The release type should be one of the following: "
            + "stable, nightly(aka pre-release, default)."
        )

    print(f"| Version split: {version_txt_split}")
    print("|" + "-" * 30)

    if args.bump in ["patch", "dev"]:
        try:
            version_txt_split = bump_version(version_txt_split, args.bump)
        except NotImplementedError as e:
            print(e)
            print("| Unavailable bump type, please bump manually.")
            print(f"| Version not changed: {'.'.join(version_txt_split)}")
        except ValueError as e:
            print(e)
            print("| The bump type should be one of the following: major, minor, patch, dev.")
            print(f"| Version not changed: {'.'.join(version_txt_split)}")
        else:
            print(f"| Bump '{args.bump}' version: {'.'.join(version_txt_split)}")
        print("|" + "-" * 30)
    elif args.bump in ["major", "minor"]:
        print("| Major and minor bump are only allowed by bumping manually.")
        print(f"| Version not changed: {'.'.join(version_txt_split)}")
        print("|" + "-" * 30)

    if args.release == "stable":
        VERSION = ".".join(version_txt_split[:3])
        if args.test:
            print(f"| Stable print, version: '{VERSION}'")
        else:
            print(f"| Stable print, version: '{VERSION}', rewrite VERSION.txt and pyproject.toml")
            os.system(f'echo "{VERSION}" > ./qurry/VERSION.txt')
            toml_rename()

    else:
        VERSION = ".".join(version_txt_split)
        print(f"| Nightly print, version: '{VERSION}'")

    # 將版本號碼傳遞到環境變數中
    if args.test:
        print(f"| Test print, version: '{VERSION}'")
    else:
        os.system(f'echo "VERSION={VERSION}" >> $GITHUB_ENV')
