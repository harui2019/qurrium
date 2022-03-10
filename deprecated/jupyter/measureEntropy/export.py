"""
Preparing of environments
"""
from ...process.measureEntropy import main, configuration
from ...type import rawCircuitTwoSiteSOC
from ....qurrent import getMeasurement, EntropyMeasureV1
from qiskit import Aer
from qiskit.providers import Backend
from matplotlib.figure import Figure
from math import pi
from pathlib import Path
from IPython.display import clear_output
import gc


backend = {
    'qasm': Aer.get_backend('qasm_simulator'),
}


def xproc(
    configCollect: list[configuration],
    backend: Backend = backend['qasm']
) -> tuple[dict, dict, dict, dict[Figure], dict[Figure]]:
    """The main script template with full function on export measurement.

    Args:
        configCollect (list): Collection of configuration.
        backend (Backend): Qiskit backend of experiment. Defaults to backend['qasm'].

    Returns:
        tuple[dict, dict, dict, dict, dict]: 
            It's return the following results:
                dataObjectCollect,
                purityObjectCollect,
                entropyObjectCollect,
                purityPlotFigCollect,
                entropyPlotFigCollect
    """

    dataObjectCollect = {}
    purityObjectCollect = {}
    entropyObjectCollect = {}
    purityPlotFigCollect = {}
    entropyPlotFigCollect = {}

    for config in configCollect:
        testList = {
            t: getMeasurement(
                EntropyMeasureV1
            )(rawCircuitTwoSiteSOC(
                qPairNum=config['qPairNum'],
                boundaryCond=config['boundaryCond'],
                hamiltonianNum=t,
                alpha=config['alpha'],
                beta=config['beta'],
                runBy=config['circuitRunBy'],
                initSet=config['initSet'],
                hamiltonianIndex=config['hamiltonianIndex']
            )) for t in config['timeEvo']
        }

        saveFolder = Path(
            f"exp{str(config['expNum']).zfill(3)}_" +
            f"demo{str(config['demoNum']).zfill(3)}_" +
            f"{config['measure']}" +
            (
                f"num{config['qNum']}-" if 'qNum' in config
                else f"pair{config['qPairNum']}-"
            ) +
            f"{config['boundaryCond']}-" +
            f"{str(config['alpha']/pi)}-" +
            f"{str(config['beta']/pi)}"
        )
        print(saveFolder)

        dataObject = {
            a: {t: {} for t in config['timeEvo']} for a in range(
                int(config['qNum']) if 'qNum' in config else int(
                    config['qPairNum']*2)+1
            )
        }

        (
            dataObject,
            purityObject,
            purityPlotFig,
            entropyObject,
            entropyPlotFig
        ) = main(
            testList,
            saveFolder,
            config,
            backend
        )

        dataObjectCollect[config['demoNum']] = dataObject
        purityObjectCollect[config['demoNum']] = purityObject
        entropyObjectCollect[config['demoNum']] = entropyObject
        purityPlotFigCollect[config['demoNum']] = purityPlotFig
        entropyPlotFigCollect[config['demoNum']] = entropyPlotFig

        print(config['expNum'], config['demoNum'], "completed")

        clear_output()
        del testList, saveFolder, dataObject, purityPlotFig, entropyPlotFig
        gc.collect()

    return (
        dataObjectCollect,
        purityObjectCollect,
        entropyObjectCollect,
        purityPlotFigCollect,
        entropyPlotFigCollect
    )
