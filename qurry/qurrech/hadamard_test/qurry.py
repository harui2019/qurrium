"""
================================================================
Wave Function Overlap - Hadamard Test
(:mod:`qurry.qurrech.hadamard_test.qurry`)
================================================================

"""

from pathlib import Path
from typing import Union, Optional, Hashable, Any, Type

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

from .experiment import EchoHadamardExperiment
from ...qurrium.qurrium import QurryPrototype
from ...qurrium.container import ExperimentContainer
from ...process.utils import qubit_selector


class EchoHadamardTest(QurryPrototype):
    """The experiment for calculating entangled entropy with more information combined."""

    __name__ = "qurrentHadamard"
    shortName = "qurrech_hadamard"

    @property
    def experiment(self) -> Type[EchoHadamardExperiment]:
        """The container class responding to this QurryV5 class."""
        return EchoHadamardExperiment

    exps: ExperimentContainer[EchoHadamardExperiment]

    def params_control(
        self,
        wave_key: Hashable = None,
        wave_key_2: Union[Hashable, QuantumCircuit] = None,
        exp_name: str = "exps",
        degree: Optional[Union[tuple[int, int], int]] = None,
        **other_kwargs: any,
    ) -> tuple[
        EchoHadamardExperiment.Arguments,
        EchoHadamardExperiment.Commonparams,
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

            wave2 (Hashable):
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
        # wave
        if isinstance(wave_key_2, QuantumCircuit):
            wave_key_2 = self.add(wave_key_2)
        elif isinstance(wave_key_2, Hashable):
            if wave_key_2 is None:
                ...
            elif not self.has(wave_key_2):
                raise KeyError(f"Wave '{wave_key_2}' not found in '.waves'")
        else:
            raise TypeError(
                f"'{wave_key_2}' is a '{type(wave_key_2)}' "
                + "instead of 'QuantumCircuit' or 'Hashable'"
            )

        num_qubits = self.waves[wave_key].num_qubits
        num_qubits_2 = self.waves[wave_key_2].num_qubits
        if num_qubits != num_qubits_2:
            raise ValueError(
                "The number of qubits of two wave functions must be the same, "
                + f"but {wave_key}: {num_qubits} != {wave_key_2}: {num_qubits_2}."
            )

        # measure and unitary location
        degree = qubit_selector(num_qubits, degree=degree)

        if isinstance(wave_key, (list, tuple)):
            wave_key = "-".join([str(i) for i in wave_key])
        if isinstance(wave_key_2, (list, tuple)):
            wave_key_2 = "-".join([str(i) for i in wave_key_2])

        exp_name = (
            f"w={wave_key}+{wave_key_2}.overlap=" + f"from{degree[0]}to{degree[1]}.{self.shortName}"
        )

        return self.experiment.filter(
            exp_name=exp_name,
            wave_key=wave_key,
            wave_key_2=wave_key_2,
            degree=degree,
            **other_kwargs,
        )

    def method(
        self,
        exp_id: str,
        _pbar: Optional[Any] = None,
    ) -> list[QuantumCircuit]:
        assert exp_id in self.exps
        assert self.exps[exp_id].commons.exp_id == exp_id
        args: EchoHadamardExperiment.Arguments = self.exps[exp_id].args
        commons: EchoHadamardExperiment.Commonparams = self.exps[exp_id].commons
        circuit = self.waves[commons.wave_key]
        num_qubits = circuit.num_qubits

        q_anc = QuantumRegister(1, "ancilla")
        q_func1 = QuantumRegister(num_qubits, "q1")
        q_func2 = QuantumRegister(num_qubits, "q2")
        c_meas1 = ClassicalRegister(1, "c1")
        qc_exp1 = QuantumCircuit(q_anc, q_func1, q_func2, c_meas1)

        qc_exp1.compose(
            self.waves.call(wave=commons.wave_key),
            [q_func1[i] for i in range(num_qubits)],
            inplace=True,
        )

        qc_exp1.compose(
            self.waves.call(wave=args.wave_key_2),
            [q_func2[i] for i in range(num_qubits)],
            inplace=True,
        )

        qc_exp1.barrier()
        qc_exp1.h(q_anc)
        for i in range(*args.degree):
            qc_exp1.cswap(q_anc[0], q_func1[i], q_func2[i])
        qc_exp1.h(q_anc)
        qc_exp1.measure(q_anc, c_meas1)

        return [qc_exp1]

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
        degree: Union[int, tuple[int, int], None] = None,
        exp_name: str = "exps",
        save_location: Optional[Union[Path, str]] = None,
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
            wave=wave,  # First wave will be taken by _paramsControlMain
            wave_key_2=wave2,  # Second wave will be taken by paramsControl
            exp_name=exp_name,
            degree=degree,
            save_location=None,
            **otherArgs,
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
