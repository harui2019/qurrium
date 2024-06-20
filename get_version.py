"""
Get the version number from the VERSION.txt file and pass it to the environment variable.
"""

import os
import argparse
from typing import Literal

with open(os.path.join("qurry", "VERSION.txt"), encoding="utf-8") as version_file:
    raw_version_txt = version_file.read().strip()

print(f"| Get raw version: {raw_version_txt}")


class MyProgramArgs(argparse.Namespace):
    """args"""

    release: Literal["stable", "nightly"]
    test: bool


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
    args = parser.parse_args()

    if args.release not in ["stable", "nightly"]:
        raise ValueError(
            "| The release type should be one of the following: "
            + "stable, nightly(aka pre-release, default)."
        )
    version_txt_split = raw_version_txt.split(".")
    print(f"| Version split: {version_txt_split}")

    if args.release == "stable":
        VERSION = ".".join(version_txt_split[:3])
        if args.test:
            print(f"| Stable print, version: '{VERSION}'")
        else:
            print(f"| Stable print, version: '{VERSION}', rewrite VERSION.txt")
            os.system(f'echo "{VERSION}" > ./qurry/VERSION.txt')
    else:
        VERSION = raw_version_txt
        print(f"| Nightly print, version: '{VERSION}'")

    # 將版本號碼傳遞到環境變數中
    if args.test:
        print(f"| Test print, version: '{VERSION}'")
    else:
        os.system(f'echo "VERSION={VERSION}" >> $GITHUB_ENV')
