"""
============================================================================
Is canonical version
============================================================================

"""

from pep440.core import is_canonical
from qurry import __version__


def test_version():
    """Test whether the versioning is canonical."""
    assert is_canonical(__version__), f"Versioning: '{__version__}' is not canonical"
