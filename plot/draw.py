from matplotlib.figure import Figure
from matplotlib.axes import Axes, SubplotBase
import matplotlib.pyplot as plt
import matplotlib

import numpy as np
import warnings
from pathlib import Path
from math import pi
from typing import Callable, Optional, Union

from ..tool.configuration import argdict
from .widget import *


class Qurryplot:
    def __init__(
        self,
        data: dict[list[Union[float, int]]],
        plotName: str = 'Qurryplot',
        saveFolder: Optional[Path] = None,
    ) -> None:
        ...
        self.data = data
        self.plotName = plotName
        self.saveFolder = saveFolder

    @staticmethod
    def drawConfigControls(
        yLim: Union[callable, tuple[float, int]] = yLimDecider,
        fontSize: int = 12,
        lineStyle: str = '--',
        foramt: str = 'png',
        dpi: int = 300,

        plotType: str = '_dummy',
        plotName: str = 'Qurryplot',

        **otherArgs: any,
    ) -> argdict:
        """_summary_

        Args:
            yLim (Union[callable, tuple[float, int]], optional): _description_. Defaults to yLimDecider.
            fontSize (int, optional): _description_. Defaults to 12.
            lineStyle (str, optional): _description_. Defaults to '--'.
            foramt (str, optional): _description_. Defaults to 'png'.
            dpi (int, optional): _description_. Defaults to 300.
            plotType (str, optional): _description_. Defaults to '_dummy'.
            plotName (str, optional): _description_. Defaults to 'Qurryplot'.

        Returns:
            argdict: _description_
        """

        # format
        format = ("png" if format not in ["png", "jpg", "jpeg"] else format)

        figName = f"{plotName}.{format}"

        args = argdict(
            params={
                'yLim': yLim,
                'fontSize': fontSize,
                'lineStyle': lineStyle,
                'foramt': foramt,
                'dpi': dpi,

                'plotType': plotType,
                'plotName': plotName,
                'figName': figName,

                **otherArgs
            },
        )

    def errorBar(
        self,

    ) -> tuple[Figure, Optional[Path]]:
        ...
