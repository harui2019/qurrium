"""
===========================================================
EntropyMeasureRandomized - Experiment
(:mod:`qurry.qurrent.randomized_measure.experiment`)
===========================================================

"""

from typing import Union, Optional, Type, Any
from collections.abc import Iterable, Hashable
import warnings
import tqdm

from qiskit import QuantumCircuit

from .analysis import EntropyMeasureRandomizedAnalysis
from .arguments import EntropyMeasureRandomizedArguments, SHORT_NAME
from .utils import circuit_method_core, randomized_entangled_entropy_complex
from ...qurrium.experiment import ExperimentPrototype, Commonparams
from ...qurrium.utils.randomized import (
    random_unitary,
    local_unitary_op_to_list,
    local_unitary_op_to_pauli_coeff,
)
from ...qurrium.utils.random_unitary import check_input_for_experiment
from ...process.utils import qubit_mapper
from ...process.randomized_measure.entangled_entropy import (
    EntangledEntropyResultMitigated,
    PostProcessingBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)
from ...tools import qurry_progressbar, ParallelManager


class EntropyMeasureRandomizedExperiment(ExperimentPrototype):
    """The instance of experiment."""

    __name__ = "EntropyMeasureRandomizedExperiment"

    @property
    def arguments_instance(self) -> Type[EntropyMeasureRandomizedArguments]:
        """The arguments instance for this experiment."""
        return EntropyMeasureRandomizedArguments

    args: EntropyMeasureRandomizedArguments

    @property
    def analysis_instance(self) -> Type[EntropyMeasureRandomizedAnalysis]:
        """The analysis instance for this experiment."""
        return EntropyMeasureRandomizedAnalysis

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        exp_name: str = "exps",
        times: int = 100,
        measure: Optional[Union[list[int], tuple[int, int], int]] = None,
        unitary_loc: Optional[Union[list[int], tuple[int, int], int]] = None,
        unitary_loc_not_cover_measure: bool = False,
        random_unitary_seeds: Optional[dict[int, dict[int, int]]] = None,
        **custom_kwargs: Any,
    ) -> tuple[EntropyMeasureRandomizedArguments, Commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            times (int, optional):
                The number of random unitary operator. Defaults to 100.
                It will denote as `N_U` in the experiment name.
            measure (Optional[Union[list[int], tuple[int, int], int]], optional):
                The measure range. Defaults to None.
            unitary_loc (Optional[Union[list[int], tuple[int, int], int]], optional):
                The range of the unitary operator. Defaults to None.
            random_unitary_seeds (Optional[dict[int, dict[int, int]]], optional):
                The seeds for all random unitary operator.
                This argument only takes input as type of `dict[int, dict[int, int]]`.
                The first key is the index for the random unitary operator.
                The second key is the index for the qubit.
                If you want to generate the seeds for all random unitary operator,
                you can use the function `generate_random_unitary_seeds`
                in `qurry.qurrium.utils.random_unitary`.
            custom_kwargs (Any):
                The custom parameters.

        Example:
            random_unitary_seeds (Optional[dict[int, dict[int, int]]]):
                ```python
                {
                    0: {0: 1234, 1: 5678},
                    1: {0: 2345, 1: 6789},
                    2: {0: 3456, 1: 7890},
                }
                ```

        Raises:
            ValueError: If the number of targets is not one.
            TypeError: If times is not an integer.
            ValueError: If the range of measure is not in the range of unitary_loc.

        Returns:
            tuple[EntropyMeasureRandomizedArguments, Commonparams, dict[str, Any]]:
                The arguments of the experiment, the common parameters, and the custom parameters.
        """
        if len(targets) > 1:
            raise ValueError("The number of target circuits should be only one.")
        if not isinstance(times, int):
            raise TypeError(f"times should be an integer, but got {times}.")

        target_key, target_circuit = targets[0]
        actual_qubits = target_circuit.num_qubits

        registers_mapping = qubit_mapper(actual_qubits, measure)
        qubits_measured = list(registers_mapping)

        unitary_located = list(qubit_mapper(actual_qubits, unitary_loc))
        measured_but_not_unitary_located = [
            qi for qi in qubits_measured if qi not in unitary_located
        ]
        if len(measured_but_not_unitary_located) > 0 and not unitary_loc_not_cover_measure:
            warnings.warn(
                f"Some qubits {measured_but_not_unitary_located} are measured "
                + "but not random unitary located. "
                + f"unitary_loc: {unitary_loc}, measure: {measure} "
                + "If you are sure about this, you can set `unitary_loc_not_cover_measure=True` "
                + "to close this warning.",
            )

        exp_name = f"{exp_name}.N_U_{times}.{SHORT_NAME}"

        check_input_for_experiment(times, actual_qubits, random_unitary_seeds)

        # pylint: disable=protected-access
        return EntropyMeasureRandomizedArguments._filter(
            exp_name=exp_name,
            target_keys=[target_key],
            times=times,
            qubits_measured=qubits_measured,
            registers_mapping=registers_mapping,
            actual_num_qubits=actual_qubits,
            unitary_located=unitary_located,
            random_unitary_seeds=random_unitary_seeds,
            **custom_kwargs,
        )
        # pylint: enable=protected-access

    @classmethod
    def method(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        arguments: EntropyMeasureRandomizedArguments,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> tuple[list[QuantumCircuit], dict[str, Any]]:
        """The method to construct circuit.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
                The circuits of the experiment.
            arguments (EntropyMeasureRandomizedArguments):
                The arguments of the experiment.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar for showing the progress of the experiment.
                Defaults to None.

        Returns:
            tuple[list[QuantumCircuit], dict[str, Any]]:
                The circuits of the experiment and the side products.
        """
        side_product = {}

        pool = ParallelManager(arguments.workers_num)
        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(
                f"Preparing {arguments.times} random unitary with {arguments.workers_num} workers."
            )

        target_key, target_circuit = targets[0]
        target_key = "" if isinstance(target_key, int) else str(target_key)
        num_qubits = target_circuit.num_qubits

        actual_unitary_loc = (
            range(num_qubits) if arguments.unitary_located is None else arguments.unitary_located
        )
        unitary_dicts = {
            i: {
                j: (
                    random_unitary(2)
                    if arguments.random_unitary_seeds is None
                    else random_unitary(2, arguments.random_unitary_seeds[i][j])
                )
                for j in actual_unitary_loc
            }
            for i in range(arguments.times)
        }

        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(
                f"Building {arguments.times} circuits with {arguments.workers_num} workers."
            )
        circ_list = pool.starmap(
            circuit_method_core,
            [
                (
                    i,
                    target_circuit,
                    target_key,
                    arguments.exp_name,
                    arguments.registers_mapping,
                    unitary_dicts[i],
                )
                for i in range(arguments.times)
            ],
        )

        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(f"Writing 'unitaryOP' with {arguments.workers_num} workers.")
        # side_product["unitaryOP"] = {
        #     k: {i: np.array(v[i]).tolist() for i in range(*arguments.unitary_loc)}
        #     for k, v in unitary_dict.items()
        # }
        unitary_operator_list = pool.starmap(
            local_unitary_op_to_list,
            [(unitary_dicts[i],) for i in range(arguments.times)],
        )
        side_product["unitaryOP"] = dict(enumerate(unitary_operator_list))

        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(f"Writing 'randomized' with {arguments.workers_num} workers.")
        # side_product["randomized"] = {
        #     i: {j: qubitOpToPauliCoeff(unitary_dict[i][j]) for j in range(*arguments.unitary_loc)}
        #     for i in range(arguments.times)
        # }
        randomized_list = pool.starmap(
            local_unitary_op_to_pauli_coeff,
            [(unitary_operator_list[i],) for i in range(arguments.times)],
        )
        side_product["randomized"] = dict(enumerate(randomized_list))

        return circ_list, side_product

    def analyze(
        self,
        selected_qubits: Optional[list[int]] = None,
        independent_all_system: bool = False,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        counts_used: Optional[Iterable[int]] = None,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> EntropyMeasureRandomizedAnalysis:
        """Calculate entangled entropy with more information combined.

        Args:
            degree (Union[tuple[int, int], int]): Degree of the subsystem.
            counts_used (Optional[Iterable[int]], optional):
                The index of the counts used.
                If not specified, then use all counts.
                Defaults to None.
            workers_num (Optional[int], optional):
                Number of multi-processing workers,
                if sets to 1, then disable to using multi-processing;
                if not specified, then use the number of all cpu counts - 2 by `cpu_count() - 2`.
                Defaults to None.
            independent_all_system (bool, optional):
                If True, then calculate the all system independently.
                Otherwise, use the existed all system source with same `count_used`.
            backend (PostProcessingBackendLabel, optional):
                Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
            pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy, a list of each overlap, puritySD,
                purity of all system, entropy of all system,
                a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """
        if selected_qubits is None:
            raise ValueError("selected_qubits should be specified.")

        self.args: EntropyMeasureRandomizedArguments
        self.reports: dict[int, EntropyMeasureRandomizedAnalysis]
        registers_mapping = self.args.registers_mapping
        assert isinstance(
            registers_mapping, dict
        ), f"registers_mapping {registers_mapping} is not dict."

        if isinstance(counts_used, Iterable):
            if max(counts_used) >= len(self.afterwards.counts):
                raise ValueError(
                    "counts_used should be less than "
                    f"{len(self.afterwards.counts)}, but get {max(counts_used)}."
                )
            counts = [self.afterwards.counts[i] for i in counts_used]
        elif counts_used is not None:
            raise ValueError(f"counts_used should be Iterable, but get {type(counts_used)}.")
        else:
            counts = self.afterwards.counts

        available_all_system_source = [
            k
            for k, v in self.reports.items()
            if (
                v.content.all_system_source == "independent"
                and v.content.counts_used == counts_used
            )
        ]
        if len(available_all_system_source) > 0 and not independent_all_system:
            all_system_source = self.reports[available_all_system_source[-1]]
        else:
            all_system_source = None

        selected_classical_registers = [registers_mapping[qi] for qi in selected_qubits]

        if isinstance(pbar, tqdm.tqdm):
            qs = self.quantities(
                shots=self.commons.shots,
                counts=counts,
                selected_classical_registers=selected_classical_registers,
                all_system_source=all_system_source,
                backend=backend,
                pbar=pbar,
            )

        else:
            pbar_selfhost = qurry_progressbar(
                range(1),
                bar_format="simple",
            )

            with pbar_selfhost as pb_self:
                qs = self.quantities(
                    shots=self.commons.shots,
                    counts=counts,
                    selected_classical_registers=selected_classical_registers,
                    all_system_source=all_system_source,
                    backend=backend,
                    pbar=pb_self,
                )
                pb_self.update()

        serial = len(self.reports)
        analysis = self.analysis_instance(
            serial=serial,
            num_qubits=self.args.actual_num_qubits,
            selected_qubits=selected_qubits,
            registers_mapping=registers_mapping,
            shots=self.commons.shots,
            unitary_located=self.args.unitary_located,
            counts_used=counts_used,
            **qs,
        )

        self.reports[serial] = analysis
        return analysis

    @classmethod
    def quantities(
        cls,
        shots: Optional[int] = None,
        counts: Optional[list[dict[str, int]]] = None,
        selected_classical_registers: Optional[list[int]] = None,
        all_system_source: Optional[EntropyMeasureRandomizedAnalysis] = None,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> EntangledEntropyResultMitigated:
        """Randomized entangled entropy with complex.

        Args:
            shots (int):
                The number of shots.
            counts (list[dict[str, int]]):
                The counts of the experiment.
            selected_classical_registers (Optional[list[int]], optional):
                The selected classical registers. Defaults to None.
            all_system_source (Optional[EntropyRandomizedAnalysis], optional):
                The source of all system. Defaults to None.
            backend (PostProcessingBackendLabel, optional):
                The backend label. Defaults to DEFAULT_PROCESS_BACKEND.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar. Defaults to None.

        Returns:
            EntangledEntropyResultMitigated: The result of the entangled entropy.
        """

        if shots is None or counts is None:
            raise ValueError("shots and counts should be specified.")

        return randomized_entangled_entropy_complex(
            shots=shots,
            counts=counts,
            selected_classical_registers=selected_classical_registers,
            all_system_source=all_system_source,
            backend=backend,
            pbar=pbar,
        )
