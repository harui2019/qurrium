from distutils.util import convert_path

main_ns = {}
ver_path = convert_path('./qurry/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

__version_str__ = main_ns['__version_str__']
print(f'| Version: v{__version_str__}')
# 將版本號碼傳遞到環境變數中
print(f'"name=VERSION::v{__version_str__}" >> $GITHUB_ENV')
