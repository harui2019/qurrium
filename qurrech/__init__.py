from .qurrech import EchoListening
from .haarMeasure import haarMeasure
# from .hadamardTest import hadamardTest


measurementList = [
    EchoListening,
    haarMeasure,
    # hadamardTest,
]
measurement = {
    who().__name__: who
    for who in measurementList}


def checkMeasurement(
) -> list[str]:
    return list(measurement.keys())


def getMeasurement(
    name: str,
) -> EchoListening:

    if name in measurement:
        return measurement[name]
    else:
        raise KeyError(
            f"No such measurement, " +
            f"the following are available: [{checkMeasurement()}]")
