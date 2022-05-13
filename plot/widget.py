import numpy as np
import warnings
from typing import Union

from ..tool.configuration import Configuration


def yLimDecider(
    data: dict[str: list[Union[float, int]]],
) -> tuple[float, float]:
    """Give the `ylim` of the plot. (The remake of `yLimDetector`)

    Args:
        data (dict[str: list[Union[float, int]]]): Plot data.

    Returns:
        tuple[float, float]: The upper and the lower bounds of plot should be.
    """

    maxSet, minSet = [], []
    upperBound, lowerBound = 1.0, 0.0
    for listSingle in data.values():
        maxSet.append(max(listSingle))
        minSet.append(min(listSingle))
    maxMax, minMin = max(maxSet), min(minSet)
    upperBound, lowerBound = np.ceil(maxMax), np.floor(minMin)
    delta = upperBound - lowerBound
    if delta < 0:
        warnings.warn("Maximum is not larger than minimum.")
        delta = -delta

    boundAdd = np.floor(np.sqrt(delta))/2
    boundAdd = boundAdd if boundAdd > 0.1 else 0.1
    upperBound += boundAdd
    lowerBound -= boundAdd

    return lowerBound, upperBound


drawConfigDefault = Configuration(
    name="drawConfig",
    default={
        "fontSize": 12,
        "yLim": yLimDecider,
        "lineStyle": "--",
        "format": "png",
        "dpi": 300,
    },
)
