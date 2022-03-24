from .qurrent import (
    EntropyMeasureV2 as EntropyMeasure,
    qurrentConfig
)

from .haarMeasure import haarMeasureV2 as haarMeasure
from .hadamardTest import hadamardTestV2 as hadamardTest


measurementList = [
    EntropyMeasure,
    haarMeasure,
    hadamardTest,
]
measurement = {
    who().__name__: who
    for who in measurementList}


def checkMeasurement(
) -> list[str]:
    return list(measurement.keys())


def getMeasurement(
    name: str,
) -> EntropyMeasure:

    if name in measurement:
        return measurement[name]
    else:
        raise KeyError(
            f"No such measurement, " +
            f"the following are available: [{checkMeasurement()}]")
