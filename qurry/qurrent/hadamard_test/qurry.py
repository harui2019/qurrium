"""
================================================================
Second Renyi Entropy - Hadamard Test
(:mod:`qurry.qurrent.hadamard_test.qurry`)
================================================================

"""

from pathlib import Path
from typing import Union, Optional, Hashable, Any, Type
import tqdm

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

from .experiment import EntropyHadamardExperiment
from ...qurrium.qurrium import QurryPrototype
from ...qurrium.container import ExperimentContainer
from ...process.utils import qubit_selector


class EntropyHadamardTest(QurryPrototype):
    """Hadamard test for entanglement entropy.

    - Which entropy:

        The entropy we compute is the Second Order Rényi Entropy.

    """

    __name__ = "qurrentHadamard"
    shortName = "qurrent_hadamard"

    @property
    def experiment(self) -> Type[EntropyHadamardExperiment]:
        """The container class responding to this QurryV5 class."""
        return EntropyHadamardExperiment

    exps: ExperimentContainer[EntropyHadamardExperiment]

    def params_control(
        self,
        wave_key: Hashable = None,
        exp_name: str = "exps",
        degree: Optional[Union[tuple[int, int], int]] = None,
        **other_kwargs: any,
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

            exp_name (str, optional):
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.

            otherArgs (any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """

        # measure and unitary location
        num_qubits = self.waves[wave_key].num_qubits
        degree = qubit_selector(num_qubits, degree=degree)

        if isinstance(wave_key, (list, tuple)):
            wave_key = "-".join([str(i) for i in wave_key])

        exp_name = f"w={wave_key}.subsys=from{degree[0]}to{degree[1]}.{self.shortName}"

        return self.experiment.filter(
            exp_name=exp_name,
            wave_key=wave_key,
            degree=degree,
            **other_kwargs,
        )

    def method(
        self,
        exp_id: Hashable,
        _pbar: Optional[tqdm.tqdm] = None,
    ) -> list[QuantumCircuit]:
        """Returns a list of quantum circuits.

        Args:
            exp_id (str): The ID of the experiment.

        Returns:
            list[QuantumCircuit]: The quantum circuits.
        """

        assert exp_id in self.exps
        assert self.exps[exp_id].commons.exp_id == exp_id
        args: EntropyHadamardExperiment.Arguments = self.exps[exp_id].args
        commons: EntropyHadamardExperiment.Commonparams = self.exps[exp_id].commons
        circuit = self.waves[commons.wave_key]
        num_qubits = circuit.num_qubits

        q_ancilla = QuantumRegister(1, "ancilla")
        q_func1 = QuantumRegister(num_qubits, "q1")
        q_func2 = QuantumRegister(num_qubits, "q2")
        c_meas1 = ClassicalRegister(1, "c1")
        qc_exp1 = QuantumCircuit(q_ancilla, q_func1, q_func2, c_meas1)

        qc_exp1.compose(
            self.waves.call(wave=commons.wave_key),
            [q_func1[i] for i in range(num_qubits)],
            inplace=True,
        )

        qc_exp1.compose(
            self.waves.call(wave=commons.wave_key),
            [q_func2[i] for i in range(num_qubits)],
            inplace=True,
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
        exp_name: str = "exps",
        *,
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonablize: bool = False,
        **other_kwargs: any,
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

            exp_name (str, optional):
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
            exp_name=exp_name,
            degree=degree,
            save_location=None,
            **other_kwargs,
        )
        assert id_now in self.exps, f"ID {id_now} not found."
        assert self.exps[id_now].commons.exp_id == id_now
        current_exp = self.exps[id_now]

        if isinstance(save_location, (Path, str)):
            current_exp.write(
                save_location=save_location,
                mode=mode,
                indent=indent,
                encoding=encoding,
                jsonable=jsonablize,
            )

        return id_now
