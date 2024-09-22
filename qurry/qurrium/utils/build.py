"""
===========================================================
Build Tools
(:mod:`qurry.qurry.qurrium.utils.build`)
===========================================================
"""

from typing import Union, Optional
from qiskit.transpiler.passmanager import PassManager


def passmanager_processor(
    passmanager: Union[str, PassManager, tuple[str, PassManager], None],
    passmanager_container: dict[str, PassManager],
) -> Optional[tuple[str, PassManager]]:
    """Process the passmanager for Qurrium.

    Args:
        passmanager (Union[str, PassManager, tuple[str, PassManager], None]): The passmanager.
        passmanager_container (dict[str, PassManager]): The container of passmanager.

    Raises:
        KeyError: If the passmanager not found in the container.
        ValueError: If the passmanager is invalid.

    Returns:
        Optional[tuple[str, PassManager]]: The passmanager pair.
    """
    if isinstance(passmanager, str):
        if passmanager not in passmanager_container:
            raise KeyError(f"Passmanager '{passmanager}' not found in {passmanager_container}")
        passmanager_pair = passmanager, passmanager_container[passmanager]
    elif isinstance(passmanager, PassManager):
        passmanager_pair = f"pass_{len(passmanager_container)}", passmanager
        passmanager_container[passmanager_pair[0]] = passmanager_pair[1]
    elif isinstance(passmanager, tuple):
        if not isinstance(passmanager[1], PassManager) or not isinstance(passmanager[0], str):
            raise ValueError(f"Invalid passmanager: {passmanager}")
        passmanager_pair = passmanager
        passmanager_container[passmanager_pair[0]] = passmanager_pair[1]
    elif passmanager is None:
        passmanager_pair = None
    else:
        raise ValueError(f"Invalid passmanager: {passmanager}")
    return passmanager_pair
