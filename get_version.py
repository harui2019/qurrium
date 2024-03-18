"""
Get the version number from the VERSION.txt file and pass it to the environment variable.
"""

import os

with open(os.path.join("qurry", "VERSION.txt"), encoding="utf-8") as version_file:
    VERSION = version_file.read().strip()

    __version__ = VERSION

print(f"| Version: {__version__}")
# 將版本號碼傳遞到環境變數中
os.system(f'echo "VERSION={__version__}" >> $GITHUB_ENV')
