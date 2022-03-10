"""
Preparing of environments
"""
from ...process.measureEntropy import (
    configuration, readExport, dataIntegrated, drawTwoObject)
from ...process.general import yLimDetector
import os
from math import pi
from pathlib import Path
from matplotlib.figure import Figure
from IPython.display import clear_output
import gc


def xproc(
    configCollect: list[configuration],
    saveFolderMerge: Path,
) -> tuple[
    dict, dict, dict, dict[list[zip]],
    dict[Figure], dict[Figure], dict[str], dict[str]
]:
    """The main script template with full function on export measurement.

    Args:
        configCollect (list): Collection of configuration.
        saveFolderMerge (Path): Location of export.

    Returns:
        tuple[
            dict, dict, dict, dict[list[zip]],
            dict[Figure], dict[Figure], dict[str], dict[str]
        ]: 
            It's return the following results:
                purityMergeCollect,
                entropyMergeCollect,
                configMergeCollect,
                keyPairCollect,

                purityPlotMergeCollect,
                entropyPlotMergeCollect,
                purityPlotNameMergeCollect,
                entropyPlotNameMergeCollect,
    """

    # Read export
    dataObjectCollect = {}
    purityObjectCollect = {}
    entropyObjectCollect = {}

    for config in configCollect:
        # saveFolder name generate
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

        (
            dataObjectCollect[config['demoNum']],
            _,
            purityObjectCollect[config['demoNum']],
            entropyObjectCollect[config['demoNum']],
        ) = readExport(saveFolder)

        print(config['expNum'], config['demoNum'], "completed")

    # Export comparation of two test
    purityMergeCollect = {}
    entropyMergeCollect = {}
    configMergeCollect = {}
    keyPairCollect = {}

    purityPlotMergeCollect = {}
    entropyPlotMergeCollect = {}
    purityPlotNameMergeCollect = {}
    entropyPlotNameMergeCollect = {}

    None if os.path.exists(saveFolderMerge) else os.mkdir(saveFolderMerge)
    combinedDataObject = {}

    dataKey = list(dataObjectCollect.keys())
    for i in range(0, int(len(configCollect)/2)):
        print(dataKey[2*i], dataKey[2*i+1], 'integrated 1.')
        combinedDataObject[i] = dataIntegrated(
            purityObjectCollect[dataKey[2*i]],
            entropyObjectCollect[dataKey[2*i]],
            configCollect[2*i],
            purityObjectCollect[dataKey[2*i+1]],
            entropyObjectCollect[dataKey[2*i+1]],
            configCollect[2*i+1]
        )
        purityMergeCollect[i] = {}
        entropyMergeCollect[i] = {}
        configMergeCollect[i] = {}
        keyPairCollect[i] = {}

    i = 0
    for data in combinedDataObject:
        keyPair = combinedDataObject[data][3]
        for ki, kj in keyPair:
            combinedDataTmp1 = {}
            combinedDataTmp2 = {}
            for keys in combinedDataObject[data][2]:
                items = combinedDataObject[data][2][keys]
                if type(items) == list:
                    combinedDataTmp1[keys] = items[0]
                    combinedDataTmp2[keys] = items[1]
                else:
                    combinedDataTmp1[keys] = items
                    combinedDataTmp2[keys] = items

            (
                purityMergeCollect[i]["f{ki}-{kj}"],
                entropyMergeCollect[i]["f{ki}-{kj}"],
                configMergeCollect[i]["f{ki}-{kj}"],
                keyPairCollect[i]["f{ki}-{kj}"]
            ) = dataIntegrated(
                {ki: combinedDataObject[data][0][ki]},
                {ki: combinedDataObject[data][1][ki]},
                combinedDataTmp1,
                {kj: combinedDataObject[data][0][kj]},
                {kj: combinedDataObject[data][1][kj]},
                combinedDataTmp2,
            )

            (
                purityPlotMergeCollect[f"{i}-{ki}-{kj}"],
                purityPlotNameMergeCollect[f"{i}-{ki}-{kj}"],
                entropyPlotMergeCollect[f"{i}-{ki}-{kj}"],
                entropyPlotNameMergeCollect[f"{i}-{ki}-{kj}"]
            ) = drawTwoObject(
                purityObject=purityMergeCollect[i]["f{ki}-{kj}"],
                entropyObject=entropyMergeCollect[i]["f{ki}-{kj}"],
                saveFolderName=saveFolderMerge,
                config=configMergeCollect[i]["f{ki}-{kj}"],
                timeEvo=configMergeCollect[i]["f{ki}-{kj}"]['timeEvo'],
                expListKeys=purityMergeCollect[i]["f{ki}-{kj}"].keys(),
                configDraw={
                    "yLim": yLimDetector(
                        entropyObjectCollect[config['demoNum']]),
                },
                # configForEach={},
            )
        i += 1
        clear_output()
        gc.collect()

    return (
        purityMergeCollect,
        entropyMergeCollect,
        configMergeCollect,
        keyPairCollect,

        purityPlotMergeCollect,
        entropyPlotMergeCollect,
        purityPlotNameMergeCollect,
        entropyPlotNameMergeCollect,
    )
