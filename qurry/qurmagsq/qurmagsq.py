# from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
# from qiskit.quantum_info import Operator

# import time
# import numpy as np
# from pathlib import Path
# from itertools import permutations
# from typing import Union, Optional, NamedTuple, Hashable, Type, Any

# from ..tools import ParallelManager, workers_distribution, DEFAULT_POOL_SIZE
# from ..qurrium import (
#     ExperimentPrototype,
#     AnalysisPrototype,
# )
# from ..qurrium import (
#     QurryPrototype,
#     ExperimentPrototype,
#     AnalysisPrototype,
# )


# def _magnetsqCell(
#     idx: int,
#     singleCounts: dict[str, int],
#     shots: int,
# ) -> tuple[int, float]:
#     """Calculate the magnitudes square cell

#     Args:
#         idx (int): Index of the cell (counts).
#         singleCounts (dict[str, int]): Counts measured by the single quantum circuit.

#     Returns:
#         tuple[int, float]: Index, one of magnitudes square.
#     """
#     magnetsqCell = np.float64(0)
#     for bits in singleCounts:
#         if (bits == "00") or (bits == "11"):
#             magnetsqCell += np.float64(singleCounts[bits]) / shots
#         else:
#             magnetsqCell -= np.float64(singleCounts[bits]) / shots
#     return idx, magnetsqCell


# def _magnetic_square_core(
#     counts: list[dict[str, int]],
#     shots: int,
#     num_qubits: int,
#     workers_num: Optional[int] = None,
# ) -> dict[str, float]:
#     """Computing specific quantity.
#     Where should be overwritten by each construction of new measurement.

#     Returns:
#         tuple[dict, dict]:
#             Magnitudes square of experiment.
#     """

#     # Determine worker number
#     launch_worker = workers_distribution(workers_num)

#     length = len(counts)
#     Begin = time.time()

#     if launch_worker == 1:
#         magnetsqCellList: list[float] = []
#         print(
#             f"| Without multi-processing to calculate overlap of {length} counts."
#             "It will take a lot of time to complete."
#         )
#         for i, c in enumerate(counts):
#             magnetsqCell = 0
#             checkSum = 0
#             print(
#                 f"| Calculating magnetsq on {i}"
#                 + f" - {i}/{length} - {round(time.time() - Begin, 3)}s.",
#                 end="\r",
#             )

#             magnetsqCell = _magnetsqCell(i, c, shots)
#             magnetsqCellList.append(magnetsqCell)
#             print(
#                 f"| Calculating magnetsq end - {i}/{length}"
#                 + f" - {round(time.time() - Begin, 3)}s."
#                 + " " * 30,
#                 end="\r",
#             )
#             assert (
#                 checkSum != shots
#             ), f"count index:{i} may not be contained by '00', '11', '01', '10'."

#     else:
#         print(
#             f"| With {launch_worker} workers to calculate overlap of {length} counts."
#         )
#         pool = ParallelManager(launch_worker)
#         magnetsqCellList = pool.starmap(
#             _magnetsqCell, [(i, c, shots) for i, c in enumerate(counts)]
#         )
#         print(f"| Calculating overlap end - {round(time.time() - Begin, 3)}s.")

#     magnetsq = (sum(magnetsqCellList) + num_qubits) / (num_qubits**2)

#     quantity = {
#         "magnetsq": magnetsq,
#         "countsNum": len(counts),
#     }
#     return quantity


# class MagnetSquareAnalysis(AnalysisPrototype):
#     """

#     'qurmagsq' may be read as `qurmask`

#     """

#     __name__ = "qurmaqsq.MagsqAnalysis"
#     shortName = "qurmagsq.report"

#     class AnalysisInput(NamedTuple):
#         """To set the analysis."""

#         shots: int
#         num_qubits: int

#     class AnalysisContent(NamedTuple):
#         """The content of the analysis."""

#         magsq: float
#         """The magnitude square."""
#         countsNum: Optional[int] = None

#     @classmethod
#     def quantities(
#         cls,
#         counts: list[dict[str, int]],
#         shots: int,
#         num_qubits: int,
#         workers_num: Optional[int] = None,
#     ) -> dict[str, float]:
#         """Computing specific quantity.
#         Where should be overwritten by each construction of new measurement.

#         Returns:
#             tuple[dict, dict]:
#                 Counts, purity, entropy of experiment.
#         """

#         return _magnetic_square_core(
#             counts=counts,
#             shots=shots,
#             num_qubits=num_qubits,
#             workers_num=workers_num,
#         )


# class MagnetSquareExperiment(ExperimentPrototype):
#     __name__ = "qurmagsq.MagsqExperiment"
#     shortName = "qurmagsq.exp"

#     class Arguments(NamedTuple):
#         """Arguments for the experiment."""

#         exp_name: str = "exps"
#         num_qubits: int = 0
#         workers_num: int = DEFAULT_POOL_SIZE

#     @classmethod
#     @property
#     def analysis_instance(cls) -> Type[MagnetSquareAnalysis]:
#         """The container class responding to this QurryV5 class."""
#         return MagnetSquareAnalysis

#     def analyze(
#         self,
#         workers_num: Optional[int] = None,
#     ) -> MagnetSquareAnalysis:
#         """Calculate entangled entropy with more information combined.

#         Args:
#             workers_num (Optional[int], optional):
#                 Number of multi-processing workers,

#         Returns:
#             dict[str, float]: A dictionary contains magnitudes square and number of counts.
#         """

#         self.args: MagnetSquareExperiment.Arguments
#         shots = self.commons.shots
#         num_qubits = self.args.num_qubits
#         counts = self.afterwards.counts

#         qs = self.analysis_instance.quantities(
#             shots=shots,
#             counts=counts,
#             num_qubits=num_qubits,
#             workers_num=workers_num,
#         )

#         serial = len(self.reports)
#         analysis = self.analysis_instance(
#             serial=serial,
#             shots=shots,
#             **qs,
#         )

#         self.reports[serial] = analysis
#         return analysis


# def _circuit_method_core(
#     idx: int,
#     tgtCircuit: QuantumCircuit,
#     exp_name: str,
#     i: int,
#     j: int,
# ):
#     """The core method of the circuit method.

#     Returns:
#         QuantumCircuit: The circuit.
#     """
#     num_qubits = tgtCircuit.num_qubits

#     qFunc = QuantumRegister(num_qubits, "q1")
#     cMeas = ClassicalRegister(2, "c1")
#     qcExp = QuantumCircuit(qFunc, cMeas)
#     qcExp.name = f"{exp_name}-{idx}-{i}-{j}"

#     qcExp.append(tgtCircuit, [qFunc[i] for i in range(num_qubits)])
#     qcExp.barrier()
#     qcExp.measure(qFunc[i], cMeas[0])
#     qcExp.measure(qFunc[j], cMeas[1])

#     return qcExp


# class MagnetSquare(QurryV5Prototype):
#     __name__ = "qurmagsq.MagnetSquare"
#     shortName = "qurmagsq"

#     @classmethod
#     @property
#     def experiment(cls) -> Type[MagnetSquareExperiment]:
#         """The container class responding to this QurryV5 class."""
#         return MagnetSquareExperiment

#     def params_control(
#         self, exp_name: str = "exps", wave_key: Hashable = None, **otherArgs: any
#     ) -> tuple[
#         MagnetSquareExperiment.Arguments,
#         MagnetSquareExperiment.Commonparams,
#         dict[str, Any],
#     ]:
#         """Handling all arguments and initializing a single experiment.

#         Args:
#             wave_key (Hashable):
#                 The index of the wave function in `self.waves` or add new one to calaculation,
#                 then choose one of waves as the experiment material.
#                 If input is `QuantumCircuit`, then add and use it.
#                 If input is the key in `.waves`, then use it.
#                 If input is `None` or something illegal, then use `.lastWave'.
#                 Defaults to None.

#             exp_name (str, optional):
#                 Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
#                 This name is also used for creating a folder to store the exports.
#                 Defaults to `'exps'`.

#             otherArgs (any):
#                 Other arguments.

#         Returns:
#             dict: The export will be processed in `.paramsControlCore`
#         """

#         num_qubits = self.waves[wave_key].num_qubits
#         exp_name = f"w={wave_key}-Nq={num_qubits}.{self.shortName}"

#         return self.experiment.filter(
#             exp_name=exp_name,
#             wave_key=wave_key,
#             num_qubits=num_qubits,
#             **otherArgs,
#         )

#     def method(
#         self,
#         exp_id: str,
#     ) -> list[QuantumCircuit]:
#         assert exp_id in self.exps
#         assert self.exps[exp_id].commons.exp_id == exp_id
#         args: MagnetSquareExperiment.Arguments = self.exps[exp_id].args
#         commons: MagnetSquareExperiment.Commonparams = self.exps[exp_id].commons
#         circuit = self.waves[commons.wave_key]
#         assert circuit.num_qubits == args.num_qubits

#         permut = [b for b in permutations([a for a in range(args.num_qubits)], 2)]
#         pool = ParallelManager(args.workers_num)

#         qcList = pool.starmap(
#             _circuit_method_core,
#             [(idx, circuit, args.exp_name, i, j) for idx, (i, j) in enumerate(permut)],
#         )
#         if isinstance(commons.serial, int):
#             print(
#                 f"| Build circuit: {commons.wave_key}, worker={args.workers_num},"
#                 + f" serial={commons.serial}, by={commons.summoner_name} done."
#             )
#         else:
#             print(f"| Build circuit: {commons.wave_key} done.", end="\r")

#         return qcList

#     def measure(
#         self,
#         wave: Union[QuantumCircuit, any, None] = None,
#         exp_name: str = "exps",
#         *args,
#         save_location: Optional[Union[Path, str]] = None,
#         mode: str = "w+",
#         indent: int = 2,
#         encoding: str = "utf-8",
#         jsonablize: bool = False,
#         **otherArgs: any,
#     ) -> str:
#         """

#         Args:
#             wave (Union[QuantumCircuit, int, None], optional):
#                 The index of the wave function in `self.waves` or add new one to calaculation,
#                 then choose one of waves as the experiment material.
#                 If input is `QuantumCircuit`, then add and use it.
#                 If input is the key in `.waves`, then use it.
#                 If input is `None` or something illegal, then use `.lastWave'.
#                 Defaults to None.

#             exp_name (str, optional):
#                 Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
#                 This name is also used for creating a folder to store the exports.
#                 Defaults to `'exps'`.

#             otherArgs (any):
#                 Other arguments.

#         Returns:
#             dict: The output.
#         """

#         IDNow = self.result(
#             wave=wave,
#             exp_name=exp_name,
#             save_location=None,
#             **otherArgs,
#         )
#         assert IDNow in self.exps, f"ID {IDNow} not found."
#         assert self.exps[IDNow].commons.exp_id == IDNow
#         currentExp = self.exps[IDNow]

#         if isinstance(save_location, (Path, str)):
#             currentExp.write(
#                 save_location=save_location,
#                 mode=mode,
#                 indent=indent,
#                 encoding=encoding,
#                 jsonable=jsonablize,
#             )

#         return IDNow
