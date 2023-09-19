version_main = (0, 6, 4)
version_dev = ('dev', 6)
isDev = True


def _beta(beta_str: str, serial: int) -> str:
    return beta_str+str(serial)


__version__ = version_main + \
    (_beta(*version_dev), ) if isDev else version_main
__version_str__ = '.'.join(map(str, version_main)) + (
    '.'+_beta(*version_dev) if isDev else '')
