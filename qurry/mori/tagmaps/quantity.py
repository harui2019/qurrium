import numpy as np
from typing import Union

from ...qurrium.type import Quantity


def quantitiesMean(
    quantities: list[Quantity],
) -> Quantity:
    return {} if len(quantities) == 0 else {k: np.mean([q[k] for q in quantities]) for k in quantities[0]}


def tagMapQuantityMean(
    tagMapQuantities,
) -> dict[str, Quantity]:
    return {k: quantitiesMean(v) for k, v in tagMapQuantities.items()}


def Q(
    quantityComplex: Union[list[Quantity], dict[str, list[Quantity]]]
) -> Union[Quantity, dict[str, Quantity], any]:
    if isinstance(quantityComplex, dict):
        if 'noTags' in quantityComplex:
            return tagMapQuantityMean(quantityComplex)
    elif isinstance(quantityComplex, list):
        if len(quantityComplex) > 0:
            if isinstance(quantityComplex[0], dict):
                return quantitiesMean(quantityComplex)
    else:
        return quantityComplex
    