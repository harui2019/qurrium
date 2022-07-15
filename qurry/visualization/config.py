from typing import Union, Iterable, NamedTuple, Optional
from matplotlib.figure import Figure
from matplotlib.axes import Axes, SubplotBase
from pathlib import Path
from math import pi

import matplotlib.pyplot as plt


class QurryPlotConfig(NamedTuple):
    fontSize = 12
    yLim = (-0.1, 1.1)
    lineStyle = "--"
    fileFormat = "png"
    dpi = 300