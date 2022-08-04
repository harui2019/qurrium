from typing import Union, NamedTuple, Optional, Literal, Callable
from matplotlib.figure import Figure
from matplotlib.axes import Axes, SubplotBase
import matplotlib.pyplot as plt

from pathlib import Path
from math import pi
import numpy as np
import warnings
import os

from ..mori.type import TagMapType
from ..qurrium import Quantity

_mplExportFormat = Literal['eps', 'jpg', 'jpeg', 'pdf', 'pgf',
                           'png', 'ps', 'raw', 'rgba', 'svg', 'svgz', 'tif', 'tiff']


class QurchartConfig(NamedTuple):
    # plt
    yLim: Optional[tuple[float, float]] = None
    fontSize: int = 12
    lineStyle: str = '--'
    dpi: int = 300
    exportPltObjects: bool = False

    quantity: str = 'entropy'

    plotName: str = 'Qurchart'
    additionName: Optional[str] = None
    filetype: _mplExportFormat = 'png'

    name: str = 'Qurchart'
    filename: str = 'Qurchart.png'
    saveFolder: Union[Path, str] = './'


def paramsControl(
    data: Union[TagMapType[Quantity], dict[str, dict[str, float]]],

    yLim: Union[callable, tuple[float, float],
                None, Literal['qurchart']] = None,
    fontSize: int = 12,
    lineStyle: str = '--',
    dpi: int = 300,
    exportPltObjects: bool = False,

    quantity: str = 'entropy',

    plotName: str = 'Qurchart',
    additionName: Optional[str] = None,
    filetype: _mplExportFormat = 'png',

    saveFolder: Union[Path, str] = './',
    defaultSettings: QurchartConfig = QurchartConfig(),
    **otherArgs,
) -> QurchartConfig:
    """_summary_

    Args:
        yLim (Union[callable, tuple[float, int], None], optional): _description_. Defaults to None.
        fontSize (int, optional): _description_. Defaults to 12.
        lineStyle (str, optional): _description_. Defaults to '--'.
        format (Literal[&#39;png&#39;], optional): _description_. Defaults to 'png'.
        dpi (int, optional): _description_. Defaults to 300.

        quantity (str, optional): _description_. Defaults to 'entropy'.

        plotType (str, optional): _description_. Defaults to '_dummy'.
        plotName (str, optional): _description_. Defaults to 'Qurchart'.
        additionName (Optional[str], optional): _description_. Defaults to None.
        saveFolder (Optional[Union[Path, str]], optional): _description_. Defaults to None.

        exportPltObjects (bool, optional): _description_. Defaults to False.

    Returns:
        QurchartConfig: _description_
    """

    # yLim
    if isinstance(yLim, Callable):
        yLim = yLim(data, quantity)
    elif yLim == 'qurchart':
        yLim = yLimDecider(data, quantity)

    if isinstance(yLim, tuple):
        yLimResult = yLim
    elif yLim is None:
        yLimResult = None
    else:
        raise TypeError(
            f"Invalid type '{type(yLim)}', 'yLim' needs to be 'callable', 'tuple[float, float]', 'None'.")

    # saveFolder
    if isinstance(saveFolder, str):
        saveFolder = Path(saveFolder)

    if not os.path.exists(saveFolder):
        os.mkdir(saveFolder)

    name = f"{additionName}.{plotName}" if not additionName is None else f"{plotName}"
    filename = name + f".{filetype}"

    if len(otherArgs) > 0:
        print(otherArgs, "dropped")

    return defaultSettings._replace(
        yLim=yLimResult,
        fontSize=fontSize,
        lineStyle=lineStyle,
        dpi=dpi,

        exportPltObjects=exportPltObjects,
        quantity=quantity,

        plotName=plotName,
        additionName=additionName,
        filetype=filetype,

        name=name,
        filename=filename,
        saveFolder=saveFolder,
    )


def yLimDecider(
    data: Union[TagMapType[Quantity], dict[str, dict[str, float]]],
    quantity: str = 'entropy',
) -> tuple[float, float]:
    """Give the `ylim` of the plot.

    Args:
        data (TagMap): Plot data.

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
