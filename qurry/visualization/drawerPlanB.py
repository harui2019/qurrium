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


def quenchEntropy(
    entropies: dict[str, Union[list[float], dict[str, float]]],
    beta: float,
    timeEvo: Iterable,
    name: str,
    saveFolder: Optional[Union[Path, str]] = None,
    config: QurryPlotConfig = QurryPlotConfig(),
) -> tuple[Figure, str]:

    timeEvoNum = len(timeEvo)
    betaPiNum = ((beta/pi) if beta != 0 else 1/4)
    oneForthPoint = int(1/(4*betaPiNum))

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

    # cutToJ: Callable[[float], float] = (
    #     lambda x: x * (beta if beta != 0 else 1/4))
    # JToCut: Callable[[float], float] = (
    #     lambda x: x * 1/(beta if beta != 0 else 1/4))
    # ax_main_secxa = ax_main.secondary_xaxis('top', functions=(cutToJ, JToCut))
    # ax_main_secxa.set_xlabel(f'$Jt$', size=config.fontSize)

    # if beta != 0:
    #     for i in np.linspace(0, timeEvoNum-1, int((timeEvoNum-1)/oneForthPoint+1)):
    #         if (i % oneForthPoint == 0) & (i % (oneForthPoint*2) != 0):
    #             plt.axvline(x=i, color='r', alpha=0.3)

    if not isinstance(entropies, dict):
        raise TypeError('entropies must be a dictionary.')
        
    for k, v in entropies.items():
        ax_main.plot(
            timeEvo, v.values(),
            marker='.',
            label="".join([f"{k}"])
        )
    ax_main_legend = ax_main.legend(
        bbox_to_anchor=(1.025, 1.0),
        loc='upper left',
        borderaxespad=0.
    )

    export_fig = plt.savefig(
        saveFolder/f"{name}.{config.fileFormat}",
        format=config.fileFormat,
        dpi=config.dpi,
        bbox_extra_artists=(ax_main_legend,),
        # bbox_extra_artists=(ax_main_legend, ax_main_secxa,),
        bbox_inches='tight'
    )

    return export_fig, saveFolder
