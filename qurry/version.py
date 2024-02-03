"""
================================================================
Qurry Version (:mod:`qurry.version`)
================================================================

"""
version_main = (0, 7, 0)
version_dev = ("dev", 2)
IS_DEV = True


def _beta(beta_str: str, serial: int) -> str:
    return beta_str + str(serial)


__version__ = version_main + (_beta(*version_dev),) if IS_DEV else version_main
__version_str__ = ".".join(map(str, version_main)) + (
    "." + _beta(*version_dev) if IS_DEV else ""
)
