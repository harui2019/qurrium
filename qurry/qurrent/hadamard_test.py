"""
================================================================
Second Renyi Entropy - Hadamard Test
(:mod:`qurry.qurrent.Hadamard`)
================================================================

"""
from pathlib import Path
from typing import Union, Optional, NamedTuple, Hashable, Iterable, Type, Any
import tqdm

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

from ..qurrium import (
    QurryV5Prototype,
    ExperimentPrototype,
    AnalysisPrototype,
    qubit_selector,
)
from .postprocess import hadamard_entangled_entropy


class EntropyHadamardAnalysis(AnalysisPrototype):
    """The instance for the analysis of :cls:`EntropyHadamardExperiment`."""

    __name__ = "qurrentHadamard.Analysis"
    shortName = "qurrent_hadamard.report"

    class AnalysisInput(NamedTuple):
        """To set the analysis."""

    class AnalysisContent(NamedTuple):
        """The content of the analysis."""

        purity: float
        """The purity of the system."""
        entropy: float
        """The entanglement entropy of the system."""

        def __repr__(self):
            return f"AnalysisContent(purity={self.purity}, entropy={self.entropy}, and others)"

    @property
    def default_side_product_fields(self) -> Iterable[str]:
        """The fields that will be stored as side product."""
        return []

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[dict[str, int]],
    ) -> dict[str, float]:
        """Calculate entangled entropy with more information combined.

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy.
        """

        result = hadamard_entangled_entropy(
            shots=shots,
            counts=counts,
        )
        return result


class EntropyHadamardExperiment(ExperimentPrototype):
    """Hadamard test for entanglement entropy."""

    __name__ = "qurrentHadamard.Experiment"
    shortName = "qurrent_hadamard.exp"

    class Arguments(NamedTuple):
        """Arguments for the experiment."""

        expName: str = "exps"
        degree: tuple[int, int] = None

    @classmethod
    @property
    def analysis_container(cls) -> Type[EntropyHadamardAnalysis]:
        """The container class responding to this QurryV5 class."""
        return EntropyHadamardAnalysis

    def analyze(self) -> AnalysisPrototype:
        """Calculate entangled entropy with more information combined.

        Args:
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            workers_num (Optional[int], optional):
                Number of multi-processing workers,
                if sets to 1, then disable to using multi-processing;
                if not specified, the use 3/4 of cpu counts by `round(cpu_count*3/4)`.
                Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy, a list of each overlap, puritySD,
                purity of all system, entropy of all system,
                a list of each overlap in all system, puritySD of all system,
                degree, actual measure range,
                actual measure range in all system, bitstring range.
        """

        shots = self.commons.shots
        counts = self.afterwards.counts

        qs = self.quantities(
            shots=shots,
            counts=counts,
        )

        serial = len(self.reports)
        analysis = self.analysis_container(
            serial=serial,
            shots=shots,
            **qs,
        )

        self.reports[serial] = analysis
        return analysis

    @classmethod
    def quantities(
        cls,
        shots: int = None,
        counts: list[dict[str, int]] = None,
    ) -> dict[str, float]:
        """Calculate entangled entropy with more information combined.

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy.
        """

        if shots is None or counts is None:
            raise ValueError("shots and counts should be specified.")

        return hadamard_entangled_entropy(
            shots=shots,
            counts=counts,
        )


class EntropyHadamardTest(QurryV5Prototype):
    """Hadamard test for entanglement entropy.

    - Which entropy:

        The entropy we compute is the Second Order Rényi Entropy.

    """

    __name__ = "qurrentHadamard"
    shortName = "qurrent_hadamard"

    @classmethod
    @property
    def experiment(cls) -> Type[EntropyHadamardExperiment]:
        """The container class responding to this QurryV5 class."""
        return EntropyHadamardExperiment

    def params_control(
        self,
        waveKey: Hashable = None,
        expName: str = "exps",
        degree: Union[tuple[int, int], int] = None,
        **otherArgs: any,
    ) -> tuple[
        EntropyHadamardExperiment.Arguments,
        EntropyHadamardExperiment.Commonparams,
        dict[str, Any],
    ]:
        """Handling all arguments and initializing a single experiment.

        Args:
            wave (Hashable):
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            expName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """

        # measure and unitary location
        num_qubits = self.waves[waveKey].num_qubits
        degree = qubit_selector(num_qubits, degree=degree)

        if isinstance(waveKey, (list, tuple)):
            waveKey = "-".join([str(i) for i in waveKey])

        expName = f"w={waveKey}.subsys=from{degree[0]}to{degree[1]}.{self.shortName}"

        return self.experiment.filter(
            expName=expName,
            waveKey=waveKey,
            degree=degree,
            **otherArgs,
        )

    def method(
        self,
        expID: Hashable,
        _pbar: Optional[tqdm.tqdm] = None,
    ) -> list[QuantumCircuit]:
        """Returns a list of quantum circuits.

        Args:
            expID (str): The ID of the experiment.

        Returns:
            list[QuantumCircuit]: The quantum circuits.
        """

        assert expID in self.exps
        assert self.exps[expID].commons.expID == expID
        args: EntropyHadamardExperiment.Arguments = self.exps[expID].args
        commons: EntropyHadamardExperiment.Commonparams = self.exps[expID].commons
        circuit = self.waves[commons.waveKey]
        num_qubits = circuit.num_qubits

        q_ancilla = QuantumRegister(1, "ancilla")
        q_func1 = QuantumRegister(num_qubits, "q1")
        q_func2 = QuantumRegister(num_qubits, "q2")
        c_meas1 = ClassicalRegister(1, "c1")
        qc_exp1 = QuantumCircuit(q_ancilla, q_func1, q_func2, c_meas1)

        qc_exp1.append(
            self.waves.call(
                wave=commons.waveKey,
            ),
            [q_func1[i] for i in range(num_qubits)],
        )

        qc_exp1.append(
            self.waves.call(
                wave=commons.waveKey,
            ),
            [q_func2[i] for i in range(num_qubits)],
        )

        qc_exp1.barrier()
        qc_exp1.h(q_ancilla)
        for i in range(*args.degree):
            qc_exp1.cswap(q_ancilla[0], q_func1[i], q_func2[i])
        qc_exp1.h(q_ancilla)
        qc_exp1.measure(q_ancilla, c_meas1)

        return [qc_exp1]

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        degree: Union[int, tuple[int, int], None] = None,
        expName: str = "exps",
        *,
        saveLocation: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonablize: bool = False,
        **otherArgs: any,
    ):
        """

        Args:
            wave (Union[QuantumCircuit, int, None], optional):
                The index of the wave function in `self.waves` or add new one to calaculation,
                then choose one of waves as the experiment material.
                If input is `QuantumCircuit`, then add and use it.
                If input is the key in `.waves`, then use it.
                If input is `None` or something illegal, then use `.lastWave'.
                Defaults to None.

            expName (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The output.
        """

        id_now = self.result(
            wave=wave,
            expName=expName,
            degree=degree,
            saveLocation=None,
            **otherArgs,
        )
        assert id_now in self.exps, f"ID {id_now} not found."
        assert self.exps[id_now].commons.expID == id_now
        current_exp = self.exps[id_now]

        if isinstance(saveLocation, (Path, str)):
            current_exp.write(
                save_location=saveLocation,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonable=jsonablize,
            )

        return id_now
