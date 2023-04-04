version_main = (0, 5, 1)
version_beta = ('beta', 0)
def _beta(beta_str: str, serial: int) -> str:
    return beta_str+str(serial).rjust(2, '0')
isBeta = False

__version__ = version_main + (_beta(*version_beta), ) if isBeta else version_main
__version_str__ = '.'.join(map(str, version_main)) + (
    '-'+_beta(*version_beta) if isBeta else '')
