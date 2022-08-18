from typing import Union, Iterable, NamedTuple, Optional
from matplotlib.figure import Figure
from matplotlib.axes import Axes, SubplotBase
from pathlib import Path
from math import pi

import matplotlib.pyplot as plt

from ..qurchart import QurchartConfig

def quenchEntropy(
    entropies: dict[str, Union[list[float], dict[str, float]]],
    beta: float,
    timeEvo: Iterable,
    name: str,
    saveFolder: Optional[Union[Path, str]] = None,
    config: QurchartConfig = QurchartConfig(
        fontSize = 12,
        yLim = (-0.1, 1.1),
        lineStyle = "--",
        filetype = "png",
        dpi = 300,
    ),
    pltObject: bool = False,
) -> tuple[Figure, str]:

    betaPiNum = ((beta/pi) if beta != 0 else 1/4)

    if isinstance(saveFolder, str):
        saveFolder = Path(saveFolder)

    fig = plt.figure()
    ax_main: Union[SubplotBase, Axes] = fig.add_subplot(1, 1, 1)

    ax_main.set_xlabel(
        f'evolution ($\Delta t = {beta} \pi$)', size=config.fontSize)
    ax_main.set_ylabel(f'entropy', size=config.fontSize)

    ax_main.set_xticks(timeEvo)
    ax_main.set_xticklabels([i if (i % 5 == 0) else None for i in timeEvo])

    ax_main.grid(linestyle=config.lineStyle)

    if not isinstance(entropies, dict):
        raise TypeError('entropies must be a dictionary.')
        
    for k, v in entropies.items():
        if isinstance(v, dict):
            v = v.values()
        ax_main.plot(
            timeEvo, v,
            marker='.',
            label="".join([f"{k}"])
        )
    ax_main_legend = ax_main.legend(
        bbox_to_anchor=(1.025, 1.0),
        loc='upper left',
        borderaxespad=0.
    )

    if pltObject:
        return fig
    
    else:
        export_fig = plt.savefig(
            saveFolder/f"{name}.{config.filetype}",
            format=config.filetype,
            dpi=config.dpi,
            bbox_extra_artists=(ax_main_legend,),
            # bbox_extra_artists=(ax_main_legend, ax_main_secxa,),
            bbox_inches='tight'
        )

        return export_fig, saveFolder