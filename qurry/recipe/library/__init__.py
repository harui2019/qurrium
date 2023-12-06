from typing import Union

from .paramagnet import TrivialParamagnet, GHZ, TopologicalParamagnet, Cluster
from .intracell import Singlet, Intracell

from ..recipe import Qurecipe
from ..exceptions import QurecipeCaseNotFoundError

CaseDictionary: dict[str, Qurecipe] = {
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
        name (str): Name of the case in :prop:`CaseDictionary`.

    Returns:
        Qurecipe: The case.
    """
    if name in CaseDictionary:
        return CaseDictionary[name]
    else:
        raise QurecipeCaseNotFoundError(f"Qurecipe '{name}' not found.")
