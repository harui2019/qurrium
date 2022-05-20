from .qurrent import EntropyMeasureV3
from .haarMeasure import haarMeasureV3 as haarMeasure
from .hadamardTest import hadamardTestV3 as hadamardTest

from .qurrentV2.qurrentV2 import EntropyMeasureV2
from .qurrentV2.haarMeasure import haarMeasureV2
from .qurrentV2.hadamardTest import hadamardTestV2
# measurementList = [
#     EntropyMeasure,
#     haarMeasure,
#     hadamardTest,
# ]
# measurement = {
#     who().__name__: who
#     for who in measurementList}


# def checkMeasurement(
# ) -> list[str]:
#     return list(measurement.keys())


# def getMeasurement(
#     name: str,
# ) -> EntropyMeasure:

#     if name in measurement:
#         return measurement[name]
#     else:
#         raise KeyError(
#             f"No such measurement, " +
#             f"the following are available: [{checkMeasurement()}]")
