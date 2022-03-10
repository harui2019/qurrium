from qiskit import (
    Aer, execute,
    QuantumRegister, ClassicalRegister, QuantumCircuit)
from qiskit.tools import *
from qiskit.visualization import *

from qiskit.providers import Backend
from qiskit.providers.ibmq import IBMQBackend
from qiskit.providers.ibmq.managed import ManagedResults

from qiskit.quantum_info import random_unitary
from qiskit.result import Result

from matplotlib.figure import Figure
import numpy as np
import gc
import warnings
from typing import Union, Optional, Callable, List
from itertools import combinations
from qiskit.visualization.counts_visualization import hamming_distance

from .qurrent import EntropyMeasureV2
from .qurrentV1 import EntropyMeasureV1
# haarMeasure

RXmatrix = np.array([[0, 1], [1, 0]])
RYmatrix = np.array([[0, -1j], [1j, 0]])
RZmatrix = np.array([[1, 0], [0, -1]])


def makeTwoBitStr(num: int, bits: List[str] = ['']) -> List[str]:
    return ((lambda bits: [
        *['0'+item for item in bits], *['1'+item for item in bits]
    ])(makeTwoBitStr(num-1, bits)) if num > 0 else bits)


makeTwoBitStrOneLiner: Callable[[int, List[str]], List[str]] = (
    lambda num, bits=['']: ((lambda bits: [
        *['0'+item for item in bits], *['1'+item for item in bits]]
    )(makeTwoBitStrOneLiner(num-1, bits)) if num > 0 else bits))


# haarMeasureV1

class haarMeasure(EntropyMeasureV1):
    def initialize(self) -> None:
        """Initialize haarMeasure
        """

        self.measurementName = 'haarMeasure'
        self.requiredParaNum = 4
        self.defaultPara = [self.numQubits, 100, 1, self.numQubits]
        self.defaultParaKey = ['degree', 'times', 'purityMethod', 'measure']
        self.requiredParaNote = [
            'degree: degree of freedom of subsystem A',
            'times: number of test to count ensemble average at least 10, default 100',
            'purityMethod: default: ensemble Ave. ; 2: standard deviation; 3: no double count ensemble Ave.',
            'measure: number of the qubits which measure.'
            # (
            #     'useRandom: using of random unitary on lattices: \n' +
            #     '   -2: only qubits would measure operate random unitary.\n' +
            #     '   -1: all qubits do random unitary operation.\n' +
            #     '   larger than 0: do random unitary operation on given specific degree.'
            # ),
        ]

    def circuitMethod(
        self,
        tgtExpId: str,
        aNum: int,
        paramsOther: list,
        runBy: str = "gate",
    ) -> Union[QuantumCircuit, list[QuantumCircuit]]:
        """The method to construct circuit.

        Args:
            tgtExpId (str): The unique id of experiment, by uuid4.
            aNum (int): Degree of freedom.
            paramsOther (list): Parameters of experiment.
            runBy (str, optional): Construct wave function as initial state 
                by 'Operater' or 'gate. Defaults to "gate".

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]: 
                The quantum circuit of experiment.
        """

        qcExpList = []
        for times in range(paramsOther[0]):
            qFunc1 = QuantumRegister(self.numQubits, 'q1')
            cMeas = ClassicalRegister(paramsOther[2], 'c1')
            qcExp = QuantumCircuit(qFunc1, cMeas)

            runByResult = (
                self.waveCircuitGated if runBy ==
                "gate" else self.waveCircuitOperator)
            qcExp.append(
                runByResult, [qFunc1[i] for i in range(self.numQubits)])

            # qcExp.barrier()
            [qcExp.append(random_unitary(2), [i])
             for i in range(self.numQubits)]
            # qcExp.save_density_matrix()
            [qcExp.measure(qFunc1[i], cMeas[i]) for i in range(paramsOther[2])]

            qcExpList.append(qcExp)

        return qcExpList

    def drawCircuit(
        self,
        expId: Optional[str],
        params: Union[List[int], int, None] = None,
        figType: Optional[str] = 'text',
        composeMethod: Optional[str] = None
    ) -> Union[str, Figure]:
        """Drawing the circuit figure of the experiment

        Args:
            expId (str): The unique id of experiment, by uuid4.
            figType (Optional[str], optional): Draw quantum circuit by
                "text", "matplotlib", or "latex". Defaults to 'text'.
            composeMethod (Optional[str], optional): Draw quantum circuit with
                composed construction. Defaults to "none". Defaults to None.

        Raises:
            KeyError: When 'expId' is not given or not existed.

        Returns:
            Union[str, Figure]: The figure of quantum circuit.
        """

        if expId not in self.base:
            raise KeyError(f"Experiment '{expId}' is not existed.")
        aNum, paramsOther, tgtExpId = self.paramsControl(params, expId)

        figList = []
        for times in range(paramsOther[0]):
            if figType != None:
                qcExp = self.base[expId]['circuit'][times]
                fig = (
                    qcExp.decompose().draw(figType) if composeMethod == "decompose"
                    else qcExp.draw(figType)
                )
            figList.append(fig)
        self.base[expId]['fig'] = figList
        return figList

    def runMethod(
        self,
        tgtExpId: str,
        aNum: int,
        paramsOther: list,
        shots: int = 1024,
        backend: Backend = Aer.get_backend('qasm_simulator')
    ) -> Union[dict, list[dict]]:
        """The method deals with jobs .

        Args:
            tgtExpId (str): The unique id of experiment, by uuid4.
            aNum (int): Degree of freedom.
            paramsOther (list): Parameters of experiment.
            shots (int, optional): Shots of the job. Defaults to 1024.
            backend (Backend, optional): The quantum backend. Defaults to 
                Aer.get_backend('qasm_simulator').

        Returns:
            Union[dict, list[dict]]: Result of experiment.
        """

        resultList = []
        for times in range(paramsOther[0]):
            job = execute(
                self.base[tgtExpId]['circuit'][times],
                backend,
                shots=shots
            )
            result = job.result()
            resultList.append(result)

        return resultList
    
    

    def _ensembleCell(
        self,
        sAi: str,
        sAiMeas: int,
        sAj: str,
        sAjMeas: int,
        aNum: int,
        shots: int,
    ) -> float:
        """Calculate the value of two counts from qubits in ensemble average.

        - about `diff = hamming_distance(sAi, sAj)`
        
            It is `hamming_distance` from `qiskit.visualization.count_visualization`.
            Due to frequently update of Qiskit and it's a simple function,
            I decide not to use source code instead of calling from `qiskit`.

        Args:
            sAi (str): First count's qubits arrange.
            sAiMeas (int): First count.
            sAj (str): Second count's qubits arrange.
            sAjMeas (int): Second count.
            aNum (int): Degree of freedom.
            shots (int): Shots of executation.

        Returns:
            float: the value of two counts from qubits in ensemble average.

        """
        diff = sum(s1 != s2 for s1, s2 in zip(sAi, sAj))
        tmp = (
            np.float_power(2, aNum)*np.float_power(-2, -diff)
        )*(
            (sAiMeas/shots)*(sAjMeas/shots)
        )
        return tmp

    def _densityToBloch(
        self,
        rho: np.array
    ) -> List[float]:
        """Convert a density matrix to a Bloch vector.

        Args:
            rho (np.array): The density matrix.

        Returns:
            List[float]: The bloch vector.
        """

        ax = np.trace(np.dot(rho, RXmatrix)).real
        ay = np.trace(np.dot(rho, RYmatrix)).real
        az = np.trace(np.dot(rho, RZmatrix)).real
        return [ax, ay, az]

    def purityOnly(
        self,
        expId: Optional[str] = None,
        params: Union[List[int], int, None] = None,
        runBy: str = "gate",
        figType: Optional[str] = 'text',
        composeMethod: Optional[str] = None,
        resultKeep: bool = False,
        shots: int = 1024,
        backend: Backend = Aer.get_backend('qasm_simulator')
    ) -> float:
        """Export the result which completed calculating purity.

        Args:
            expId (Optional[str]):  The unique id of experiment, by uuid4.
            params (Union[dict[int], List[int], int, None], optional):
                Parameters of experiment. Defaults to None.
            runBy (str, optional): Construct wave function as initial state
                by 'Operater' or 'gate. Defaults to "gate".
            figType (Optional[str], optional): Draw quantum circuit by
                "text", "matplotlib", or "latex". Defaults to 'text'.
            composeMethod (Optional[str], optional): Draw quantum circuit with
                composed construction. Defaults to "none". Defaults to None.
            shots (int, optional): Shots of the job. Defaults to 1024.
            backend (Backend): The quantum backend. Defaults to
                Aer.get_backend('qasm_simulator').

        Returns:
            float: the purity.
        """

        aNum, paramsOther, tgtExpId = self.paramsControl(params, expId)
        self.runOnly(
            expId=tgtExpId,
            params=params,
            runBy=runBy,
            figType=figType,
            composeMethod=composeMethod,
            shots=shots,
            backend=backend
        )

        self.base[tgtExpId]['counts'] = [
            self.base[tgtExpId]['result'][times].get_counts()
            for times in range(paramsOther[0])]

        purity = 0
        purityCellList = []

        for times in range(paramsOther[0]):
            allMeas = self.base[tgtExpId]['counts'][times]
            allCountKey = list(allMeas)
            allMeasUnderDegree = dict.fromkeys(
                [k[:aNum] for k in allCountKey], 0)
            for kMeas in list(allMeas):
                allMeasUnderDegree[kMeas[:aNum]] += allMeas[kMeas]
            # allKeyUnderDegree = makeTwoBitStrOneLiner(self.aNum)
            print(allMeas)
            print(allMeasUnderDegree)
            purityCell = 0

            if paramsOther[1] == 3:
                for (sAi, sAiMeas), (sAj, sAjMeas) in list(
                    combinations(allMeasUnderDegree.items(), 2)
                ):
                    purityCell += self._ensembleCell(
                        sAi, sAiMeas, sAj, sAjMeas, aNum, shots)
                for sAi, sAiMeas in allMeasUnderDegree.items():
                    purityCell += self._ensembleCell(
                        sAi, sAiMeas, sAi, sAiMeas, aNum, shots)
                print("no double count ensemble ave.")

            elif paramsOther[1] == 2:

                purityCell = 0
                isZeroInclude = '0' in allCountKey
                isOneInclude = '1' in allCountKey
                if isZeroInclude and isOneInclude:
                    purityCell = (allMeas['0'] - allMeas['1'])/shots
                elif isZeroInclude:
                    purityCell = allMeas['0']/shots
                elif isOneInclude:
                    purityCell = allMeas['1']/shots
                else:
                    purity = 0
                    raise Warning(
                        "Expected '0' and '1', but there is no such keys")
                print("standard deviation")

            else:
                for sAi, sAiMeas in allMeasUnderDegree.items():
                    for sAj, sAjMeas in allMeasUnderDegree.items():
                        purityCell += self._ensembleCell(
                            sAi, sAiMeas, sAj, sAjMeas, aNum, shots)
                print("double count ensemble ave.")

            purityCellList.append(purityCell)

        if paramsOther[1] == 2:
            tmp = np.sqrt(3)*np.std(purityCellList)
            purity = (1+tmp**2)/2
            print("standard deviation")

        elif paramsOther[1] == 3:
            purity = np.mean(purityCellList)
            print("no double count ensemble ave.")

        else:
            purity = np.mean(purityCellList)
            print("double count ensemble ave.")

        if resultKeep:
            warnings.warn(
                "Result will keep, but it may cause memory overallocated.")
        else:
            print("Entropy and Purity are figured out, result will clear.")
            del self.base[tgtExpId]['result']

        self.base[tgtExpId] = {
            **self.base[tgtExpId],
            'purity': purity,
            'entropy': -np.log2(purity),
        }
        gc.collect()

        return purity

        """
        for sAi, sAiMeas in allMeasUnderDegree.items():
            for sAj, sAjMeas in allMeasUnderDegree.items():

                # diff = hamming_distance(sAi, sAj) # from qiskit.visualization.count_visualization


        for aI in allCountKey:
            for aJ in allCountKey:
                diff = sum([
                    np.abs(int(aI[qLoc]) - int(aJ[qLoc]))
                for qLoc in range(aNum, 0, -1)])


                tmp = (
                    np.float_power(2, aNum)  # no sure
                )*(
                    (np.float_power(-2, -diff))  # ok
                )*(allMeas[aI]/shots)*(allMeas[aJ]/shots)
                ensembleSingle += tmp
                print(ensembleSingle, tmp)
                print(aI, aJ, aNum, diff,
                    #   (allMeas[aI]/shots), (allMeas[aJ]/shots)
                ) #
                # d=2 by dim unitary = 2
        """


# haarMeasureV2

class haarMeasureV2(EntropyMeasureV2):
    def initialize(self) -> dict[str: any]:
        """Configuration to Initialize 'haarMeasure'.
        - 
        ```
        self.measureConfig = {
            'name': 'haarMeasure',
            'paramsNum': 3,
            'default': {
                'degree': (
                    self.waves[-1].num_qubits/2 if (self.waves[-1].num_qubits % 2 == 0)
                    else int((self.waves[-1].num_qubits-1)/2+1)),
                'times': 100,
                'purityMethod': 1,
            },
            'hint': {
                'degree': 'degree of freedom of subsystem A.',
                'times': 'number of test to count ensemble average at least 10, default 100.',
                'purityMethod': [
                    '1: ensemble Ave. (default)'
                    '2: standard deviation',
                    '3: no double count ensemble Ave.'],
                'measure': 'number of the qubits which measure.',
            },
            'otherHint': """ """,
        }
        ```

        Returns:
            dict[str: any]: The basic configuration of `haarMeasure`.
        """

        self.measureConfig = {
            'name': 'haarMeasure',
            'paramsNum': 3,
            'default': {
                'degree': (
                    self.waves[self.lastWave].num_qubits/2 if (self.waves[self.lastWave].num_qubits % 2 == 0)
                    else int((self.waves[self.lastWave].num_qubits-1)/2+1)),
                'times': 100,
                'purityMethod': 1,
            },
            'hint': {
                'degree': 'degree of freedom of subsystem A.',
                'times': 'number of test to count ensemble average at least 10, default 100.',
                'purityMethod': [
                    '1: ensemble Ave. (default)'
                    '2: standard deviation',
                    '3: no double count ensemble Ave.'],
                'measure': 'number of the qubits which measure.',
            },
            'otherHint': """ """,
        }

        self.paramsKey = []

        return self.measureConfig

    def circuitMethod(
        self,
    ) -> Union[QuantumCircuit, list[QuantumCircuit]]:
        """The method to construct circuit.

        Returns:
            Union[QuantumCircuit, list[QuantumCircuit]]: 
                The quantum circuit of experiment.
        """
        args = self.now
        numQubits = self.waves[args.wave].num_qubits

        qcExpList = []
        for times in range(args.paramsOther['times']):
            qFunc1 = QuantumRegister(numQubits, 'q1')
            cMeas = ClassicalRegister(numQubits, 'c1')
            qcExp = QuantumCircuit(qFunc1, cMeas)

            qcExp.append(self.waveInstruction(
                wave=args.wave,
                runBy=args.runBy,
                backend=args.backend,
            ), [qFunc1[i] for i in range(numQubits)])

            if not isinstance(args.backend, IBMQBackend):
                qcExp.barrier()

            [qcExp.append(random_unitary(2), [i])
                for i in range(numQubits)]

            if not isinstance(args.backend, IBMQBackend):
                qcExp.save_density_matrix()

            [qcExp.measure(qFunc1[i], cMeas[i]) for i in range(numQubits)]

            qcExpList.append(qcExp)

        return qcExpList
    
    @staticmethod
    def hamming_distance(str1, str2):
        """Calculate the Hamming distance between two bit strings

        From `qiskit.visualization.count_visualization`.

        Args:
            str1 (str): First string.
            str2 (str): Second string.
        Returns:    
            int: Distance between strings.
        Raises:
            VisualizationError: Strings not same length
        """
        if len(str1) != len(str2):
            raise VisualizationError("Strings not same length.")
        return sum(s1 != s2 for s1, s2 in zip(str1, str2))

    @staticmethod
    def ensembleCell(
        sAi: str,
        sAiMeas: int,
        sAj: str,
        sAjMeas: int,
        aNum: int,
        shots: int,
    ) -> float:
        """Calculate the value of two counts from qubits in ensemble average.

        - about `diff = hamming_distance(sAi, sAj)`:
        
            It is `hamming_distance` from `qiskit.visualization.count_visualization`.
            Due to frequently update of Qiskit and it's a simple function,
            I decide not to use source code instead of calling from `qiskit`.

        Args:
            sAi (str): First count's qubits arrange.
            sAiMeas (int): First count.
            sAj (str): Second count's qubits arrange.
            sAjMeas (int): Second count.
            aNum (int): Degree of freedom.
            shots (int): Shots of executation.

        Returns:
            float: the value of two counts from qubits in ensemble average.

        """
        diff = sum(s1 != s2 for s1, s2 in zip(sAi, sAj))
        tmp = (
            np.float_power(2, aNum)*np.float_power(-2, -diff)
        )*(
            (sAiMeas/shots)*(sAjMeas/shots)
        )
        return tmp

    @staticmethod
    def densityToBloch(
        rho: np.array
    ) -> List[float]:
        """Convert a density matrix to a Bloch vector.

        Args:
            rho (np.array): The density matrix.

        Returns:
            List[float]: The bloch vector.
        """

        ax = np.trace(np.dot(rho, RXmatrix)).real
        ay = np.trace(np.dot(rho, RYmatrix)).real
        az = np.trace(np.dot(rho, RZmatrix)).real
        return [ax, ay, az]

    @classmethod
    def purityMethod(
        cls,
        aNum: int,
        paramsOther: dict[str: int],
        shots: int,
        result: Union[Result, ManagedResults],
        resultIdxList: Optional[list[int]] = None,
    ) -> tuple[dict[str, float], float, float]:
        """Computing Purity.

        ```
        paramsOther: {
            'times': 100,
            'purityMethod': 1,
        }
        ```

        Returns:
            tuple[dict[str, float], float, float]: 
                Counts, purity, entropy of experiment.
        """

        if resultIdxList == None:
            resultIdxList = [i for i in range(paramsOther['times'])]
        elif isinstance(resultIdxList, list):
            if len(resultIdxList) > 1:
                ...
            else:
                raise ValueError(
                    "The element number of 'resultIdxList' needs to be more than 1 for 'haarMeasure'.")
        else:
            raise ValueError("'resultIdxList' needs to be 'list'.")

        counts = [result.get_counts(i) for i in resultIdxList]
        purity = -100
        entropy = -100
        purityCellList = []

        for t in resultIdxList:
            allMeas = result.get_counts(t)
            allMeasUnderDegree = dict.fromkeys(
                [k[:aNum] for k in allMeas], 0)
            for kMeas in list(allMeas):
                allMeasUnderDegree[kMeas[:aNum]] += allMeas[kMeas]
            # print("before: ", allMeas)
            # print("after : ", allMeasUnderDegree)
            purityCell = 0

            if paramsOther['purityMethod'] == 3:

                for (sAi, sAiMeas), (sAj, sAjMeas) in list(
                    combinations(allMeasUnderDegree.items(), 2)
                ):
                    purityCell += cls.ensembleCell(
                        sAi, sAiMeas, sAj, sAjMeas, aNum, shots)
                for sAi, sAiMeas in allMeasUnderDegree.items():
                    purityCell += cls.ensembleCell(
                        sAi, sAiMeas, sAi, sAiMeas, aNum, shots)

            elif paramsOther['purityMethod'] == 2:

                purityCell = 0
                isZeroInclude = '0' in allMeas
                isOneInclude = '1' in allMeas
                if isZeroInclude and isOneInclude:
                    purityCell = (allMeas['0'] - allMeas['1'])/shots
                elif isZeroInclude:
                    purityCell = allMeas['0']/shots
                elif isOneInclude:
                    purityCell = allMeas['1']/shots
                else:
                    purity = 0
                    raise Warning(
                        "Expected '0' and '1', but there is no such keys")

            else:
                for sAi, sAiMeas in allMeasUnderDegree.items():
                    for sAj, sAjMeas in allMeasUnderDegree.items():
                        purityCell += cls.ensembleCell(
                            sAi, sAiMeas, sAj, sAjMeas, aNum, shots)

            purityCellList.append(purityCell)

        if paramsOther['purityMethod'] == 2:
            tmp = np.sqrt(3)*np.std(purityCellList)
            purity = (1+tmp**2)/2
            print("method:", "standard deviation")

        elif paramsOther['purityMethod'] == 3:
            purity = np.mean(purityCellList)
            print("method:", "no double count ensemble ave.")

        else:
            purity = np.mean(purityCellList)
            print("method:", "double count ensemble ave.")

        entropy = -np.log2(purity)

        return counts, purity, entropy
