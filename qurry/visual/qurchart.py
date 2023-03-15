from typing import Union, NamedTuple, Optional, Literal, Callable, Tuple, Any
# from matplotlib.figure import Figure
# from matplotlib.axes import Axes, SubplotBase
# import matplotlib.pyplot as plt

from pathlib import Path
from math import pi
import numpy as np
import warnings
import os

from ..mori import TagList
from ..qurrium import Quantity

_mplExportFormat = Literal['eps', 'jpg', 'jpeg', 'pdf', 'pgf',
                           'png', 'ps', 'raw', 'rgba', 'svg', 'svgz', 'tif', 'tiff']


class QurchartConfig(NamedTuple):
    """
    Congfiguration for Qurry chart module.
    """

    # plt
    yLim: Optional[tuple[float, float]] = None
    """The y-axis limit of the plot."""
    fontSize: int = 12
    """The font size of the plot."""
    lineStyle: str = '--'
    """The line style of the plot."""
    dpi: int = 300
    """The resolution of the plot."""
    exportPltObjects: bool = False
    """Whether to export the matplotlib objects."""

    quantity: str = 'entropy'
    """The quantity to be plotted."""
    title: str = 'Qurchart'
    """The title of the plot."""

    filetype: _mplExportFormat = 'png'
    """The file type will be exported."""
    name: str = 'Qurchart'
    """The name of the plot."""
    filename: str = 'Qurchart.png'
    """The filename of the plot."""
    saveLocation: Union[Path, str] = Path('./')
    """The save location of the plot."""

    outfields: dict[str, any] = {}
    """The unused argument of the configuration."""


def paramsControl(
    data: Union[TagList[Quantity], dict[str, dict[str, float]]],

    yLim: Union[Tuple[float, float], None, Literal['qurchart']] = None,
    fontSize: int = 12,
    lineStyle: str = '--',
    dpi: int = 300,
    exportPltObjects: bool = False,

    quantity: str = 'entropy',
    name: Optional[str] = None,
    title: str = 'Qurchart',
    filetype: _mplExportFormat = 'png',

    saveLocation: Union[Path, str] = './',
    **otherArgs,
) -> QurchartConfig:
    """Control the parameters of the plot.

    Args:
        data (Union[TagList[Quantity], dict[str, dict[str, float]]]): 
            Data to be plotted.
        yLim (Union[callable, tuple[float, int], None], optional): 
            The y-axis limit of the plot. Defaults to None.
        fontSize (int, optional): 
            The font size of the plot. Defaults to 12.
        lineStyle (str, optional): 
            The line style of the plot. Defaults to '--'.
        dpi (int, optional): 
            Resolution of the plot. Defaults to 300.
        exportPltObjects (bool, optional): 
            Whether to export the matplotlib objects. Defaults to False.
        quantity (str, optional): 
            Quantity to be plotted. Defaults to 'entropy'.
        title (str, optional): 
            The title of the plot. Defaults to 'Qurchart'.
        filetype (_mplExportFormat, optional): 
            The file type will be exported. Defaults to 'png'.
        saveLocation (Union[Path, str], optional): 
            The save location of the plot. Defaults to './'.

    Raises:
        TypeError: yLim needs to be 'Callable', 'tuple[float, float]', 'None'.

    Returns:
        QurchartConfig: The configuration of the plot.
    """
    # yLim
    if yLim == 'qurchart':
        yLimResult = yLimDecider(data, quantity)
    elif isinstance(yLim, tuple):
        yLimResult = yLim
    elif yLim is None:
        yLimResult = None
    else:
        yLimResult = None
        raise TypeError(
            f"Invalid type '{type(yLim)}', 'yLim' needs to be 'tuple[float, float]', 'None'.")

    # saveLocation
    if isinstance(saveLocation, str):
        saveLocation = Path(saveLocation)
    if not os.path.exists(saveLocation):
        os.mkdir(saveLocation)

    name = f"{title}" if name is None else name
    filename = name + f".{filetype}"

    if len(otherArgs) > 0:
        print(otherArgs, "dropped")

    return QurchartConfig(
        yLim=yLimResult,
        fontSize=fontSize,
        lineStyle=lineStyle,
        dpi=dpi,
        exportPltObjects=exportPltObjects,
        
        quantity=quantity,
        title=title,
        filetype=filetype,
        name=name,
        filename=filename,
        saveLocation=saveLocation,
        
        outfields=otherArgs,
    )


def yLimDecider(
    data: Union[TagList[Quantity], dict[str, dict[str, float]]],
    quantity: str = 'entropy',
) -> tuple[float, float]:
    """Give the `ylim` of the plot.

    Args:
        data (TagList): Plot data.

    Returns:
        tuple[float, float]: The upper and the lower bounds of plot should be.
    """

    maxSet: list[Union[float, int]] = []
    minSet: list[Union[float, int]] = []
    for vs in data.values():
        if isinstance(vs, list):
            ...
        elif isinstance(vs, dict):
            vs = list(vs.values())
        else:
            raise TypeError(
                f"Invalid type '{type(vs)}', it needs to be 'dict' or 'list'.")

        if len(vs) == 0:
            continue

        vsp = []
        for v in vs:
            if isinstance(v, dict):
                if quantity in v:
                    vsp.append(v[quantity])
            elif isinstance(v, (int, float)):
                vsp.append(v)
            else:
                raise TypeError(
                    f"Invalid type '{type(v)}' for value in '{type(vs)}', it needs to be `Quantity`, 'int', or 'float'.")

        maxSet.append(max(vsp))
        minSet.append(min(vsp))
    maxMax, minMin = max(maxSet), min(minSet)
    upperBound, lowerBound = np.ceil(maxMax), np.floor(minMin)
    delta = upperBound - lowerBound

    if delta < 0:
        warnings.warn("Maximum is not larger than minimum.")
        upperBound, lowerBound = lowerBound, upperBound
        delta = -delta

    boundAdd = np.floor(np.sqrt(delta))/2 if delta > 1 else 0.1
    boundAdd = boundAdd if boundAdd > 0.1 else 0.1
    upperBound += boundAdd
    lowerBound -= boundAdd

    return lowerBound, upperBound


def valueGetter(v: Union[float, dict[float]], quantity) -> Optional[float]:
    if isinstance(v, dict):
        return v[quantity] if quantity in v else None
    elif isinstance(v, float):
        return v
    else:
        raise ValueError(f"Unavailable type '{type(v)}'")


def stickLabelGiver(l: Union[int, str]):
    if isinstance(l, int):
        return l
    elif isinstance(l, str):
        return l if len(l) < 4 else None
    else:
        raise ValueError(f"Unavailable type '{type(l)}'")
