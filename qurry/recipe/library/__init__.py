from typing import Union

from .paramagnet import TrivialParamagnet, GHZ, TopologicalParamagnet, Cluster
from .intracell import Singlet, Intracell

from ..recipe import Qurecipe
from ..exceptions import QurecipeCaseNotFoundError

CASE_SET: dict[str, Qurecipe] = {
    "trivialParamagnet": TrivialParamagnet,
    "trivialPM": TrivialParamagnet,
    "cat": GHZ,
    "topParamagnet": TopologicalParamagnet,
    "topPM": TopologicalParamagnet,
    
    "cluster": Cluster,
    "singlet": Singlet,
    "intracell": Intracell,
}


def get_case(
    name: str,
) -> Union[Qurecipe, QurecipeCaseNotFoundError]:
    """Get a case from the library.

    Args:
        name (str): Name of the case in :prop:`CASE_SET`.

    Returns:
        Qurecipe: The case.
    """
    if name in CASE_SET:
        return CASE_SET[name]
    else:
        raise QurecipeCaseNotFoundError(f"Qurecipe '{name}' not found.")