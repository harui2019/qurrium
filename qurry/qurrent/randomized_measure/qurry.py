"""
===========================================================
Second Renyi Entropy - Randomized Measurement 
(:mod:`qurry.qurrent.randomized_measure`)
===========================================================

"""

from pathlib import Path
from typing import Union, Optional, Hashable, Any, Type
import warnings
import tqdm

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Operator

from .experiment import EntropyRandomizedExperiment
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
    unitary_sublist: dict[int, Operator],
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
        qc_exp1.append(unitary_sublist[j].to_instruction(), [j])

    for j in range(*measure):
        qc_exp1.measure(q_func1[j], c_meas1[j - measure[0]])

    return qc_exp1


class EntropyRandomizedMeasure(QurryPrototype):
    """Randomized Measure Experiment.

    - Which entropy:

        The entropy we compute is the Second Order Rényi Entropy.

    - Reference:

        Probing Rényi entanglement entropy via randomized measurements -
        Tiff Brydges, Andreas Elben, Petar Jurcevic, Benoît Vermersch,
        Christine Maier, Ben P. Lanyon, Peter Zoller, Rainer Blatt ,and Christian F. Roos ,
        [doi:10.1126/science.aau4963](
            https://www.science.org/doi/abs/10.1126/science.aau4963)

        Simple mitigation of global depolarizing errors in quantum simulations -
        Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self,
        Christopher and Kim, M. S. and Knolle, Johannes,
        [PhysRevE.104.035309](
            https://link.aps.org/doi/10.1103/PhysRevE.104.035309)

    - `bibtex`:

    ```bibtex
    @article{doi:10.1126/science.aau4963,
        author = {Tiff Brydges  and Andreas Elben  and Petar Jurcevic
        and Benoît Vermersch  and Christine Maier  and Ben P. Lanyon
        and Peter Zoller  and Rainer Blatt  and Christian F. Roos },
        title = {Probing Rényi entanglement entropy via randomized measurements},
        journal = {Science},
        volume = {364},
        number = {6437},
        pages = {260-263},
        year = {2019},
        doi = {10.1126/science.aau4963},
        URL = {https://www.science.org/doi/abs/10.1126/science.aau4963},
        eprint = {https://www.science.org/doi/pdf/10.1126/science.aau4963},
        abstract = {Quantum systems are predicted to be better at information
        processing than their classical counterparts, and quantum entanglement
        is key to this superior performance. But how does one gauge the degree
        of entanglement in a system? Brydges et al. monitored the build-up of
        the so-called Rényi entropy in a chain of up to 10 trapped calcium ions,
        each of which encoded a qubit. As the system evolved,
        interactions caused entanglement between the chain and the rest of
        the system to grow, which was reflected in the growth of
        the Rényi entropy. Science, this issue p. 260 The buildup of entropy
        in an ion chain reflects a growing entanglement between the chain
        and its complement. Entanglement is a key feature of many-body quantum systems.
        Measuring the entropy of different partitions of a quantum system
        provides a way to probe its entanglement structure.
        Here, we present and experimentally demonstrate a protocol
        for measuring the second-order Rényi entropy based on statistical correlations
        between randomized measurements. Our experiments, carried out with a trapped-ion
        quantum simulator with partition sizes of up to 10 qubits,
        prove the overall coherent character of the system dynamics and
        reveal the growth of entanglement between its parts,
        in both the absence and presence of disorder.
        Our protocol represents a universal tool for probing and
        characterizing engineered quantum systems in the laboratory,
        which is applicable to arbitrary quantum states of up to
        several tens of qubits.}}
    ```

    ```bibtex
        @article{PhysRevE.104.035309,
            title = {Simple mitigation of global depolarizing errors in quantum simulations},
            author = {Vovrosh, Joseph and Khosla, Kiran E. and Greenaway, Sean and Self,
            Christopher and Kim, M. S. and Knolle, Johannes},
            journal = {Phys. Rev. E},
            volume = {104},
            issue = {3},
            pages = {035309},
            numpages = {8},
            year = {2021},
            month = {Sep},
            publisher = {American Physical Society},
            doi = {10.1103/PhysRevE.104.035309},
            url = {https://link.aps.org/doi/10.1103/PhysRevE.104.035309}
        }
    ```
    """

    __name__ = "qurrentRandomized"
    shortName = "qurrent_haar"

    @property
    def experiment(self) -> Type[EntropyRandomizedExperiment]:
        """The container class responding to this QurryV5 class."""
        return EntropyRandomizedExperiment

    exps: ExperimentContainer[EntropyRandomizedExperiment]

    def params_control(
        self,
        wave_key: Hashable = None,
        exp_name: Optional[str] = None,
        times: int = 100,
        measure: Optional[Union[tuple[int, int], int]] = None,
        unitary_loc: Optional[Union[tuple[int, int], int]] = None,
        **other_kwargs,
    ) -> tuple[
        EntropyRandomizedExperiment.Arguments,
        EntropyRandomizedExperiment.Commonparams,
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

            other_kwargs (any):
                Other arguments.

        Returns:
            dict: The export will be processed in `.paramsControlCore`
        """

        # times
        if not isinstance(times, int):
            raise ValueError(f"times should be an integer, but got {times}.")

        # measure and unitary location
        num_qubits = self.waves[wave_key].num_qubits
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
            f"w={wave_key}.with{times}random.{self.shortName}" if exp_name is None else exp_name
        )

        return self.experiment.filter(
            exp_name=actual_exp_name,
            wave_key=wave_key,
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
        args = self.exps[exp_id].args
        commons = self.exps[exp_id].commons
        circuit = self.waves[commons.wave_key]
        _num_qubits = circuit.num_qubits

        pool = ParallelManager(args.workers_num)

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
            ],
        )

        if isinstance(_pbar, tqdm.tqdm):
            _pbar.set_description_str(f"Writing 'unitaryOP' with {args.workers_num} workers.")
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
        wave: Union[QuantumCircuit, any],
        times: int = 100,
        measure: Union[int, tuple[int, int], None] = None,
        unitary_loc: Union[int, tuple[int, int], None] = None,
        exp_name: str = "exps",
        *,
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

            other_kwargs (any):
                Other arguments.

        Returns:
            dict: The output.
        """

        id_now = self.result(
            wave=wave,
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
