from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import json
from pathlib import Path
from typing import Union, Optional
from .general import syncControl


def exportSyncJson(
    savePath: Path,
    syncList: syncControl,
    data: dict
) -> None:
    """A Quick expression to export json files.

    Args:
        savePath (Path): Location to export.
        syncList (syncControl): Let .gitignore file track and sync.
        data (dict): The data will export.
    """

    with open(
        savePath, 'w', encoding='utf-8'
    ) as File:
        syncList.sync(savePath.name)
        json.dump(data, File, indent=2, ensure_ascii=False)


def readJson(
    savePath: Path,
) -> dict:
    """A Quick expression to read json files.

    Args:
        savePath (Path): Location of file.

    Returns:
        dict: The contents of file
    """

    data = {}
    with open(
        savePath, 'r', encoding='utf-8'
    ) as File:
        data = json.load(File)
    return data


def drawCircuit(
    saveName: tuple[Path, str],
    syncList: syncControl,
    expDraw: Union[str, Figure],
    configDraw: dict[str, Optional[str]]
) -> None:
    """A Quick expression to draw circuit.

    Args:
        saveName (Path): Location to export.
        syncList (syncControl): Let .gitignore file track and sync.
        expDraw (Union[str, Figure]): Circuit export.
        configDraw (dict[str, Optional[str]], optional): Configuration. 
            Defaults to { 'figType': None, 'composeMethod': None, 'isSync': False, }.

    """

    configDrawWork = {
        'figType': None,
        'isSync': False,
        **configDraw,
    }

    if configDrawWork['figType'] == 'mpl':
        plt.clf()
        plt.figure(expDraw, title=f"{saveName[1]}")
        plt.savefig(saveName[0] / f"{saveName[1]}.png", format="png")
        plt.close()
        if configDrawWork['isSync']:
            syncList.sync((saveName[0] / f"{saveName[1]}.png").name)

    elif configDrawWork['figType'] == None:
        print(f"'{saveName[1]}' has cancelled to export.")

    else:
        with open(
            saveName[0] / f"{saveName[1]}.txt", 'w', encoding='utf-8'
        ) as circuitDraw:
            print(expDraw, file=circuitDraw)
            if configDrawWork['isSync']:
                syncList.sync(circuitDraw.name)
