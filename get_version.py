from pathlib import Path
import os

main_ns = {}
ver_path = Path('./qurry/version.py')
with open(ver_path, encoding='utf-8') as ver_file:
    exec(ver_file.read(), main_ns)

__version_str__ = 'v'+main_ns['__version_str__']
print(f'| Version: {__version_str__}')
# 將版本號碼傳遞到環境變數中
os.system(f'echo "VERSION={__version_str__}" >> $GITHUB_ENV')
