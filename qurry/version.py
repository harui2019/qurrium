"""
================================================================
Qurry Version (:mod:`qurry.version`)
================================================================

"""
version_main = (0, 6, 5)
version_dev = ('dev', 5)
IS_DEV = True


def _beta(beta_str: str, serial: int) -> str:
    return beta_str+str(serial)


__version__ = version_main + \
    (_beta(*version_dev), ) if IS_DEV else version_main
__version_str__ = '.'.join(map(str, version_main)) + (
    '.'+_beta(*version_dev) if IS_DEV else '')
