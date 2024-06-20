# from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
# from qiskit.result import Result
# from qiskit.providers.ibmq.managed import ManagedResults, IBMQManagedResultDataNotAvailable

# import numpy as np
# import warnings
# from typing import Union, Optional, NamedTuple, Literal

# from ..qurrium import QurryV3
# from ..tools import Gajima

# # StringOperator V0.3.0 - Measuring Topological Phase - Qurstrop


# class StringOperatorV3(QurryV3):
#     """StringOperator V0.3.0 of qurstrop

#     - Reference:
#         - Used in:
#             Crossing a topological phase transition with a quantum computer -
#             Smith, Adam and Jobst, Bernhard and Green, Andrew G. and Pollmann, Frank,
#             [PhysRevResearch.4.L022020](
#             https://link.aps.org/doi/10.1103/PhysRevResearch.4.L022020)

#         - `bibtex`:

# ```bibtex
# @article{PhysRevResearch.4.L022020,
#     title = {Crossing a topological phase transition with a quantum computer},
#     author = {Smith, Adam and Jobst, Bernhard and Green, Andrew G. and Pollmann, Frank},
#     journal = {Phys. Rev. Research},
#     volume = {4},
#     issue = {2},
#     pages = {L022020},
#     numpages = {8},
#     year = {2022},
#     month = {Apr},
#     publisher = {American Physical Society},
#     doi = {10.1103/PhysRevResearch.4.L022020},
#     url = {https://link.aps.org/doi/10.1103/PhysRevResearch.4.L022020}
# }
# ```
#     """

#     strOpUnit = Union[tuple[Literal['rx', 'ry', 'rz'], float], str]
#     strOp = dict[strOpUnit]
#     strOpLib: dict[strOp] = {
#         'i': {
#             0: (),
#             'filling': ('ry', -np.pi/2),
#             -1: (),
#         },
#         'zy': {
#             0: ('rz', 0),
#             1: ('rx', np.pi/2),
#             'filling': ('ry', -np.pi/2),
#             -2: ('rx', np.pi/2),
#             -1: ('rz', 0),
#         },
#         # 'i': {s
#         #     0: (),
#         #     'filling': ('rx', np.pi/2),
#         #     -1: (),
#         # },
#         # 'zy': {
#         #     0: (),
#         #     1: ('ry', -np.pi/2),
#         #     'filling': ('rx', np.pi/2),
#         #     -2: ('ry', -np.pi/2),
#         #     -1: (),
#         # },
#     }

#     class argsCore(NamedTuple):
#         _stringLiteral = Literal['i', 'zy']

#         expsName: str = 'exps'
#         wave: Union[QuantumCircuit, any, None] = None,
#         string: _stringLiteral = 'i',
#         # string: Literal[tuple(stringOperatorLib)] = 'i',
#         i: Optional[int] = 1,
#         k: Optional[int] = None,

#     def addStringOperator(
#         self,
#         string: str,
#         operator: strOp,
#     ) -> None:
#         if 'filling' not in operator:
#             raise ValueError('The filling operator unit is required.')

#         self.strOpLib = {
#             string: operator,
#             **self.strOpLib,
#         }
#         self._lastAddstring = string

#         class argsCoreUpdate(NamedTuple):
#             _stringLiteral = Literal['i', 'zy']

#             expsName: str = 'exps'
#             wave: Union[QuantumCircuit, any, None] = None,
#             string: Union[_stringLiteral,
#                           Literal['self._lastAddstring']] = 'i',
#             i: Optional[int] = 1,
#             k: Optional[int] = None,

#         self.argsCore = argsCoreUpdate

#     # Initialize
#     def initialize(self) -> dict[str, any]:
#         """Configuration to Initialize Qurrech.

#         Returns:
#             dict[str, any]: The basic configuration of `Qurrech`.
#         """

#         for k1 in list(self.strOpLib.keys()):
#             if 'filling' not in self.strOpLib[k1]:
#                 raise ValueError(
#                     'The filling operator unit is required ' +
#                     f"but operator {k1} in '.strOpLib' lost this key, " +
#                     "initialization has been canceled.")

#         self._exps_config = self.exps_config(
#             name="qurstropConfig",
#         )
#         self._expsBase = self.expsBase(
#             name="qurstropBase",
#             defaultArg={
#                 # Reault of experiment.
#                 'order': -100,
#             },
#         )
#         self._expsHint = self.expsHint(
#             name='qurstropBaseHint',
#             hintContext={
#                 'order': 'The String Order Parameters.',
#             },
#         )
#         self._expsMultiConfig = self.exps_configMulti(
#             name="qurstropConfigMulti",
#         )
#         self.shortName = 'qurstrop'
#         self.__name__ = 'StringOperator'

#         return self._exps_config, self._expsBase

#     """Arguments and Parameters control"""

#     def paramsControlCore(
#         self,
#         expsName: str = 'exps',
#         wave: Union[QuantumCircuit, any, None] = None,
#         string: Literal['i', 'zy'] = 'i',
#         # string: Literal[tuple(stringOperatorLib)] = 'i',
#         i: Optional[int] = 1,
#         k: Optional[int] = None,
#         **otherArgs: any,
#     ) -> dict:
#         """Handling all arguments and initializing a single experiment.

#         Args:
#             wave (Union[QuantumCircuit, int, None], optional):
#                 The index of the wave function in `self.waves` or add new one to calaculation,
#                 then choose one of waves as the experiment material.
#                 If input is `QuantumCircuit`, then add and use it.
#                 If input is the key in `.waves`, then use it.
#                 If input is `None` or something illegal, then use `.lastWave'.
#                 Defaults to None.

#             expsName (str, optional):
#                 Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
#                 This name is also used for creating a folder to store the exports.
#                 Defaults to `'exps'`.

#             string (Literal['i', 'zy'], optional):
#                 The string operator.

#             i (Optional[int], optional):
#                 The index of beginning qubits in the quantum circuit.

#             k (Optional[int], optional):
#                 The index of ending qubits in the quantum circuit.

#             otherArgs (any):
#                 Other arguments.

#         Raises:
#             KeyError: Given `exp_id` does not exist.
#             TypeError: When parameters are not all to be `int`.
#             KeyError: The given parameters lost degree of freedom.".

#         Returns:
#             tuple[str, dict[str, any]]: Current `exp_id` and arguments.
#         """

#         # wave
#         if isinstance(wave, QuantumCircuit):
#             wave = self.addWave(wave)
#             print(f"| Add new wave with key: {wave}")
#         elif wave == None:
#             wave = self.lastWave
#             print(f"| Autofill will use '.lastWave' as key")
#         else:
#             try:
#                 self.waves[wave]
#             except KeyError as e:
#                 warnings.warn(f"'{e}', use '.lastWave' as key")
#                 wave = self.lastWave

#         numQubits = self.waves[wave].num_qubits

#         # i, k
#         if k == None:
#             k = numQubits - 2
#         if i == None:
#             i = 1
#         if i >= k:
#             raise KeyError(f"'i ({i}) >= k ({k})' which is not allowed")
#         length = k-i+1

#         # string order
#         if string not in self.strOpLib:
#             raise ValueError(
#                 "The given string is not in the library, " +
#                 "use '.stringOperatorLib' to check available string.")
#         if numQubits < len(self.strOpLib[string]):
#             raise ValueError(
#                 f"The given wave function '{wave}' only has {numQubits} qubits less than " +
#                 f"min length {len(self.strOpLib[string])} of string operator {string}.")
#         if length < len(self.strOpLib[string]):
#             raise ValueError(
#                 f"The given qubit range i={i} to k={k} only has length={length} less than " +
#                 f"min length={len(self.strOpLib[string])} of string operator '{string}'.")

#         return {
#             'wave': wave,
#             'numQubit': numQubits,
#             'string': string,
#             'i': i,
#             'k': k,
#             'length': length,
#             'expsName': f"w={wave}-str={string}-i={i}-k={k}.{self.shortName}",
#             **otherArgs,
#         }

#     """ Main Process: Circuit"""

#     def circuitMethod(
#         self,
#     ) -> Union[QuantumCircuit, list[QuantumCircuit]]:
#         """The method to construct circuit.
#         Where should be overwritten by each construction of new measurement.

#         Returns:
#             Union[QuantumCircuit, list[QuantumCircuit]]:
#                 The quantum circuit of experiment.
#         """
#         argsNow: self.argsCore = self.now
#         numQubits = self.waves[argsNow.wave].num_qubits

#         qFunc = QuantumRegister(numQubits, 'q1')
#         cMeas = ClassicalRegister(argsNow.length, 'c1')
#         qcExp = QuantumCircuit(qFunc, cMeas)

#         qcExp.append(self.waveInstruction(
#             wave=argsNow.wave,
#             runBy=argsNow.runBy,
#             backend=argsNow.backend,
#         ), [qFunc[i] for i in range(numQubits)])
#         qcExp.barrier()

#         def handleStrOp(qi: int, ci: int, move: self.strOpUnit):
#             if len(move) != 0:
#                 if move[0] == 'rx':
#                     qcExp.rx(move[1], qi)
#                 elif move[0] == 'ry':
#                     qcExp.ry(move[1], qi)
#                 qcExp.measure(qFunc[qi], cMeas[ci])

#         strOp = self.strOpLib[argsNow.string]
#         boundMapping = {
#             (argsNow.k+1+op if op < 0 else argsNow.i+op): op
#             for op in strOp if isinstance(op, int)}

#         for ci, qi in enumerate(range(argsNow.i, argsNow.k+1)):
#             if qi in boundMapping:
#                 handleStrOp(qi, ci, strOp[boundMapping[qi]])
#             else:
#                 handleStrOp(qi, ci, strOp['filling'])

#         return [qcExp]

#     """ Main Process: Data Import and Export"""

#     """ Main Process: Job Create"""

#     """ Main Process: Calculation and Result"""

#     """ Main Process: Purity and Entropy"""

#     @classmethod
#     def quantity(
#         cls,
#         shots: int,
#         result: Union[Result, ManagedResults],
#         resultIdxList: Optional[list[int]] = None,
#         numQubit: int = None,
#         **otherArgs,
#     ) -> tuple[dict, dict]:
#         """Computing specific quantity.
#         Where should be overwritten by each construction of new measurement.

#         Returns:
#             tuple[dict, dict]:
#                 Counts, purity, entropy of experiment.
#         """

#         if resultIdxList == None:
#             resultIdxList = [0]
#         elif isinstance(resultIdxList, list):
#             if len(resultIdxList) == 1:
#                 ...
#             else:
#                 raise ValueError(
#                     f"The element number of 'resultIdxList': {len(resultIdxList)} "
#                     "needs to be 1 for 'StringOperator'.")
#         else:
#             raise ValueError("'resultIdxList' needs to be 'list'.")

#         counts = []
#         order = -100
#         onlyCount = None

#         try:
#             counts = [result.get_counts(i) for i in resultIdxList]
#             onlyCount = counts[0]
#         except IBMQManagedResultDataNotAvailable as err:
#             print("| Failed Job result skip, index:", resultIdxList, err)
#             return {}

#         order = 0
#         for s, m in Gajima(
#             onlyCount.items(),
#             carousel=[('dots', 15, 6), 'basic'],
#             prefix="| ",
#             desc="Counting order",
#             finish_desc="Counting completed",
#         ):
#             add_or_reduce = 1 if sum([int(b) for b in s]) % 2 == 0 else -1
#             cell = add_or_reduce*(m/shots)
#             order += cell

#         quantity = {
#             'order': order,
#         }
#         return counts, quantity

#     """ Main Process: Main Control"""

#     def measure(
#         self,
#         wave: Union[QuantumCircuit, any, None] = None,
#         string: Literal['i', 'zy'] = 'i',
#         i: Optional[int] = 1,
#         k: Optional[int] = None,
#         expsName: str = 'exps',
#         **otherArgs: any
#     ) -> dict:
#         """

#         Args:
#             wave (Union[QuantumCircuit, int, None], optional):
#                 The index of the wave function in `self.waves` or add new one to calaculation,
#                 then choose one of waves as the experiment material.
#                 If input is `QuantumCircuit`, then add and use it.
#                 If input is the key in `.waves`, then use it.
#                 If input is `None` or something illegal, then use `.lastWave'.
#                 Defaults to None.

#             expsName (str, optional):
#                 Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
#                 This name is also used for creating a folder to store the exports.
#                 Defaults to `'exps'`.

#             string (Literal['i', 'zy'], optional):
#                 The string operator.

#             i (Optional[int], optional):
#                 The index of beginning qubits in the quantum circuit.

#             k (Optional[int], optional):
#                 The index of ending qubits in the quantum circuit.

#             otherArgs (any):
#                 Other arguments.

#         Returns:
#             dict: The output.
#         """
#         return self.output(
#             wave=wave,
#             string=string,
#             i=i,
#             k=k,
#             expsName=expsName,
#             **otherArgs,
#         )
