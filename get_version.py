from .qurry import __version_str__

print(f'The version number is {__version_str__}')

# 將版本號碼傳遞到環境變數中
print(f'::set-env name=VERSION::{__version_str__}')