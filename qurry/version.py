version_main = (0, 6, 3)
version_beta = ('beta', 3)
isBeta = True


def _beta(beta_str: str, serial: int) -> str:
    return beta_str+str(serial).rjust(2, '0')


__version__ = version_main + \
    (_beta(*version_beta), ) if isBeta else version_main
__version_str__ = '.'.join(map(str, version_main)) + (
    '-'+_beta(*version_beta) if isBeta else '')
