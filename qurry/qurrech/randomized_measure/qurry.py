"""
===========================================================
Wave Function Overlap - Randomized Measurement 
(:mod:`qurry.qurrech.randomized_measure.qurry`)
===========================================================

"""

from pathlib import Path
from typing import Union, Optional, Hashable, Any, Type
import warnings
import tqdm

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator

from .experiment import EchoRandomizedExperiment
from ...qurrium.qurrium import QurryPrototype
from ...qurrium.container import ExperimentContainer
from ...qurrium.utils.randomized import (
    local_random_unitary_operators,
    local_random_unitary_pauli_coeff,
    random_unitary,
)
from ...process.utils import qubit_selector
from ...tools import ParallelManager
from ...exceptions import QurryArgumentsExpectedNotNone


def circuit_method_core(
    idx: int,
    target_circuit: QuantumCircuit,
    exp_name: str,
    unitary_loc: tuple[int, int],
    unitary_sub_list: dict[int, Operator],
    measure: tuple[int, int],
) -> QuantumCircuit:
    """Build the circuit for the experiment.

    Args:
        idx (int): Index of the randomized unitary.
        target_circuit (QuantumCircuit): Target circuit.
        exp_name (str): Experiment name.
        unitary_loc (tuple[int, int]): Unitary operator location.
        unitary_sublist (dict[int, Operator]): Unitary operator list.
        measure (tuple[int, int]): Measure range.

    Returns:
        QuantumCircuit: The circuit for the experiment.
    """
    num_qubits = target_circuit.num_qubits

    q_func1 = QuantumRegister(num_qubits, "q1")
    c_meas1 = ClassicalRegister(measure[1] - measure[0], "c1")
    qc_exp1 = QuantumCircuit(q_func1, c_meas1)
    qc_exp1.name = f"{exp_name}-{idx}"

    qc_exp1.compose(target_circuit, [q_func1[i] for i in range(num_qubits)], inplace=True)

    qc_exp1.barrier()
    for j in range(*unitary_loc):
        qc_exp1.append(unitary_sub_list[j].to_instruction(), [j])

    for j in range(*measure):
        qc_exp1.measure(q_func1[j], c_meas1[j - measure[0]])

    return qc_exp1


class EchoRandomizedListen(QurryPrototype):
    """Randomized measure experiment."""

    __name__ = "qurrechRandomized"
    shortName = "qurrech_haar"

    tqdm_handleable = True
    """The handleable of tqdm."""

    @property
    def experiment(self) -> Type[EchoRandomizedExperiment]:
        """The container class responding to this QurryV5 class."""
        return EchoRandomizedExperiment

    exps: ExperimentContainer[EchoRandomizedExperiment]

    def params_control(
        self,
        wave_key: Hashable = None,
        wave_key_2: Union[Hashable, QuantumCircuit] = None,
        exp_name: Optional[str] = None,
        times: int = 100,
        measure: Union[tuple[int, int], int, None] = None,
        unitary_loc: Union[tuple[int, int], int, None] = None,
        **other_kwargs: any,
    ) -> tuple[
        EchoRandomizedExperiment.Arguments,
        EchoRandomizedExperiment.Commonparams,
        dict[str, Any],
    ]:
        """Handling all arguments and initializing a single experiment.

        Args:
            wave_key (Hashable):
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
        num_qubits2 = self.waves[wave_key_2].num_qubits
        if num_qubits != num_qubits2:
            raise ValueError(
                "The number of qubits of two wave functions must be the same, "
                + f"but {wave_key}: {num_qubits} != {wave_key_2}: {num_qubits2}."
            )

        # times
        if not isinstance(times, int):
            raise ValueError(f"times should be an integer, but got {times}.")

        # measure and unitary location
        num_qubits = self.waves[wave_key].num_qubits
        num_qubits2 = self.waves[wave_key_2].num_qubits
        if num_qubits != num_qubits2:
            raise ValueError(
                "The number of qubits of two wave functions must be the same, "
                + f"but {wave_key}: {num_qubits} != {wave_key_2}: {num_qubits2}."
            )

        if measure is None:
            measure = num_qubits
        measure = qubit_selector(num_qubits, degree=measure)

        if unitary_loc is None:
            unitary_loc = num_qubits
        unitary_loc = qubit_selector(num_qubits, degree=unitary_loc)

        if (min(measure) < min(unitary_loc)) or (max(measure) > max(unitary_loc)):
            raise ValueError(
                f"unitary_loc range '{unitary_loc}' does not contain measure range '{measure}'."
            )

        actual_exp_name = (
            f"w={wave_key}+{wave_key_2}.with{times}random.{self.shortName}"
            if exp_name is None
            else exp_name
        )

        return self.experiment.filter(
            exp_name=actual_exp_name,
            wave_key=wave_key,
            wave_key_2=wave_key_2,
            times=times,
            measure=measure,
            unitary_loc=unitary_loc,
            **other_kwargs,
        )

    def method(
        self,
        exp_id: str,
        _pbar: Optional[tqdm.tqdm] = None,
    ) -> list[QuantumCircuit]:
        assert exp_id in self.exps
        assert self.exps[exp_id].commons.exp_id == exp_id
        current_exp = self.exps[exp_id]
        args: EchoRandomizedExperiment.Arguments = self.exps[exp_id].args
        commons: EchoRandomizedExperiment.Commonparams = self.exps[exp_id].commons
        circuit = self.waves[commons.wave_key]
        circuit2 = self.waves[args.wave_key_2]

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Preparing {args.times} random unitary with {args.workers_num} workers."
            )

        # !Warning: DO NOT USE MULTI-PROCESSING HERE !!!!!
        # See https://github.com/numpy/numpy/issues/9650
        # And https://github.com/harui2019/qurry/issues/78
        # The random seed will be duplicated in each process,
        # and it will make duplicated result.
        # unitaryList = pool.starmap(
        #     local_random_unitary, [(args.unitary_loc, None) for _ in range(args.times)])

        if args.unitary_loc is None:
            actual_unitary_loc = (0, circuit.num_qubits)
            warnings.warn(
                f"| unitary_loc is not specified, using the whole qubits {actual_unitary_loc},"
                + " but it should be not None anymore here.",
                QurryArgumentsExpectedNotNone,
            )
        else:
            actual_unitary_loc = args.unitary_loc

        unitary_dict = {
            i: {j: random_unitary(2) for j in range(*actual_unitary_loc)} for i in range(args.times)
        }

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(
                f"Building {args.times} circuits with {args.workers_num} workers."
            )

        pool = ParallelManager(args.workers_num)
        qc_list = pool.starmap(
            circuit_method_core,
            [
                (
                    i,
                    circuit,
                    args.exp_name,
                    args.unitary_loc,
                    unitary_dict[i],
                    args.measure,
                )
                for i in range(args.times)
            ]
            + [
                (
                    i + args.times,
                    circuit2,
                    args.exp_name,
                    args.unitary_loc,
                    unitary_dict[i],
                    args.measure,
                )
                for i in range(args.times)
            ],
        )
        if args.unitary_loc is None:
            actual_unitary_loc = (0, circuit.num_qubits)
            warnings.warn(
                f"| unitary_loc is not specified, using the whole qubits {actual_unitary_loc},"
                + " but it should be not None anymore here.",
                QurryArgumentsExpectedNotNone,
            )
        unitary_operator_list = pool.starmap(
            local_random_unitary_operators,
            [(args.unitary_loc, unitary_dict[i]) for i in range(args.times)],
        )
        current_exp.beforewards.side_product["unitaryOP"] = dict(enumerate(unitary_operator_list))

        # currentExp.beforewards.side_product['unitaryOP'] = {
        #     k: {i: np.array(v[i]).tolist() for i in range(*args.unitary_loc)}
        #     for k, v in unitaryList.items()}

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(f"Writing 'randomized' with {args.workers_num} workers.")
        randomized_list = pool.starmap(
            local_random_unitary_pauli_coeff,
            [(args.unitary_loc, unitary_operator_list[i]) for i in range(args.times)],
        )
        current_exp.beforewards.side_product["randomized"] = dict(enumerate(randomized_list))

        # currentExp.beforewards.side_product['randomized'] = {i: {
        #     j: qubitOpToPauliCoeff(
        #         unitaryList[i][j])
        #     for j in range(*args.unitary_loc)
        # } for i in range(args.times)}

        return qc_list

    def measure(
        self,
        wave: Union[QuantumCircuit, any, None] = None,
        wave2: Union[QuantumCircuit, any, None] = None,
        times: int = 100,
        measure: Union[int, tuple[int, int], None] = None,
        unitary_loc: Union[int, tuple[int, int], None] = None,
        exp_name: str = "exps",
        save_location: Optional[Union[Path, str]] = None,
        mode: str = "w+",
        indent: int = 2,
        encoding: str = "utf-8",
        jsonablize: bool = False,
        **other_kwargs: any,
    ) -> str:
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
            times=times,
            measure=measure,
            unitary_loc=unitary_loc,
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
