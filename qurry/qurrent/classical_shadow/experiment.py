"""
===========================================================
ShadowUnveil - Experiment
(:mod:`qurry.qurrent.classical_shadow.experiment`)
===========================================================

"""

from typing import Union, Optional, Type, Any, Literal
from collections.abc import Iterable, Hashable
import tqdm
import numpy as np
from numpy.random import default_rng

from qiskit import QuantumCircuit

from .analysis import ShadowUnveilAnalysis
from .arguments import ShadowUnveilArguments, SHORT_NAME
from .utils import circuit_method_core
from ...qurrium.experiment import ExperimentPrototype, Commonparams
from ...qurrium.utils.random_unitary import check_input_for_experiment
from ...process.utils import qubit_mapper
from ...process.classical_shadow.classical_shadow import (
    classical_shadow_complex,
    ClassicalShadowComplex,
    PostProcessingBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)
from ...tools import qurry_progressbar, ParallelManager, set_pbar_description
from ...exceptions import RandomizedMeasureUnitaryOperatorNotFullCovering


class ShadowUnveilExperiment(ExperimentPrototype):
    """The instance of experiment."""

    __name__ = "ShadowUnveilExperiment"

    @property
    def arguments_instance(self) -> Type[ShadowUnveilArguments]:
        """The arguments instance for this experiment."""
        return ShadowUnveilArguments

    args: ShadowUnveilArguments

    @property
    def analysis_instance(self) -> Type[ShadowUnveilAnalysis]:
        """The analysis instance for this experiment."""
        return ShadowUnveilAnalysis

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
    ) -> tuple[ShadowUnveilArguments, Commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'exps'`.
            times (int, optional):
                The number of random unitary operator. Defaults to 100.
                It will denote as `N_U` in the experiment name.
            measure (Optional[Union[list[int], tuple[int, int], int]], optional):
                The measure range. Defaults to None.
            unitary_loc (Optional[Union[list[int], tuple[int, int], int]], optional):
                The range of the unitary operator. Defaults to None.
            unitary_loc_not_cover_measure (bool, optional):
                Confirm that not all unitary operator are covered by the measure.
                If True, then close the warning.
                Defaults to False.
            random_unitary_seeds (Optional[dict[int, dict[int, int]]], optional):
                The seeds for all random unitary operator.
                This argument only takes input as type of `dict[int, dict[int, int]]`.
                The first key is the index for the random unitary operator.
                The second key is the index for the qubit.

                .. code-block:: python
                    {
                        0: {0: 1234, 1: 5678},
                        1: {0: 2345, 1: 6789},
                        2: {0: 3456, 1: 7890},
                    }

                If you want to generate the seeds for all random unitary operator,
                you can use the function `generate_random_unitary_seeds`
                in `qurry.qurrium.utils.random_unitary`.

                .. code-block:: python
                    from qurry.qurrium.utils.random_unitary import generate_random_unitary_seeds
                    random_unitary_seeds = generate_random_unitary_seeds(100, 2)

            custom_kwargs (Any):
                The custom parameters.

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
            raise RandomizedMeasureUnitaryOperatorNotFullCovering(
                f"Some qubits {measured_but_not_unitary_located} are measured "
                + "but not random unitary located. "
                + f"unitary_loc: {unitary_loc}, measure: {measure} "
                + "If you are sure about this, you can set `unitary_loc_not_cover_measure=True` "
                + "to close this warning."
            )

        exp_name = f"{exp_name}.N_U_{times}.{SHORT_NAME}"

        check_input_for_experiment(times, len(unitary_located), random_unitary_seeds)

        # pylint: disable=protected-access
        return ShadowUnveilArguments._filter(
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
        arguments: ShadowUnveilArguments,
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

        pool = ParallelManager()
        set_pbar_description(pbar, f"Preparing {arguments.times} random unitary.")

        target_key, target_circuit = targets[0]
        target_key = "" if isinstance(target_key, int) else str(target_key)

        assert arguments.unitary_located is not None, "unitary_located should be specified."
        random_unitary_ids_array = np.random.randint(
            0, 3, size=(arguments.times, len(arguments.unitary_located))
        )
        random_unitary_ids = {
            n_u_i: {
                n_u_qi: (
                    random_unitary_ids_array[n_u_i][seed_i]
                    if arguments.random_unitary_seeds is None
                    else default_rng(arguments.random_unitary_seeds[n_u_i][seed_i]).integers(0, 3)
                )
                for seed_i, n_u_qi in enumerate(arguments.unitary_located)
            }
            for n_u_i in range(arguments.times)
        }

        set_pbar_description(pbar, f"Building {arguments.times} circuits.")
        circ_list = []
        circ_list = pool.starmap(
            circuit_method_core,
            [
                (
                    n_u_i,
                    target_circuit,
                    target_key,
                    arguments.exp_name,
                    arguments.registers_mapping,
                    random_unitary_ids[n_u_i],
                )
                for n_u_i in range(arguments.times)
            ],
        )

        set_pbar_description(pbar, "Writing 'random_unitary_ids'.")
        side_product["random_unitary_ids"] = random_unitary_ids

        return circ_list, side_product

    def analyze(
        self,
        selected_qubits: Optional[Iterable[int]] = None,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        counts_used: Optional[Iterable[int]] = None,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> ShadowUnveilAnalysis:
        """Calculate entangled entropy with more information combined.

        Args:
            selected_qubits (Optional[Iterable[int]], optional):
                The selected qubits. Defaults to None.
            backend (PostProcessingBackendLabel, optional):
                The backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
            counts_used (Optional[Iterable[int]], optional):
                The index of the counts used. Defaults to None.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar. Defaults to None.

        Returns:
            EntropyMeasureRandomizedAnalysis: The result of the analysis.
        """

        if selected_qubits is None:
            raise ValueError("selected_qubits should be specified.")

        self.args: ShadowUnveilArguments
        self.reports: dict[int, ShadowUnveilAnalysis]
        assert (
            "random_unitary_ids" in self.beforewards.side_product
        ), "The side product 'random_unitary_ids' should be in the side product of the beforewards."
        random_unitary_ids = self.beforewards.side_product["random_unitary_ids"]
        assert isinstance(
            self.args.registers_mapping, dict
        ), f"registers_mapping {self.args.registers_mapping} is not dict."

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

        selected_qubits = [qi % self.args.actual_num_qubits for qi in selected_qubits]
        assert len(set(selected_qubits)) == len(
            selected_qubits
        ), f"selected_qubits should not have duplicated elements, but got {selected_qubits}."
        selected_classical_registers = [self.args.registers_mapping[qi] for qi in selected_qubits]
        random_unitary_ids_classical_registers = {
            n_u_i: {
                ci: random_unitary_id[n_u_qi] for n_u_qi, ci in self.args.registers_mapping.items()
            }
            for n_u_i, random_unitary_id in random_unitary_ids.items()
        }

        if isinstance(pbar, tqdm.tqdm):
            qs = self.quantities(
                shots=self.commons.shots,
                counts=counts,
                random_unitary_ids=random_unitary_ids_classical_registers,
                selected_classical_registers=selected_classical_registers,
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
                    random_unitary_ids=random_unitary_ids,
                    selected_classical_registers=selected_classical_registers,
                    backend=backend,
                    pbar=pbar,
                )
                pb_self.update()

        serial = len(self.reports)
        analysis = self.analysis_instance(
            serial=serial,
            num_qubits=self.args.actual_num_qubits,
            selected_qubits=selected_qubits,
            registers_mapping=self.args.registers_mapping,
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
        random_unitary_ids: Optional[dict[int, dict[int, Union[Literal[0, 1, 2], int]]]] = None,
        selected_classical_registers: Optional[Iterable[int]] = None,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> ClassicalShadowComplex:
        """Randomized entangled entropy with complex.

        Args:
            shots (int):
                The number of shots.
            counts (list[dict[str, int]]):
                The counts of the experiment.
            selected_classical_registers (Optional[Iterable[int]], optional):
                The selected classical registers. Defaults to None.
            all_system_source (Optional[EntropyRandomizedAnalysis], optional):
                The source of all system. Defaults to None.
            backend (PostProcessingBackendLabel, optional):
                The backend label. Defaults to DEFAULT_PROCESS_BACKEND.
            pbar (Optional[tqdm.tqdm], optional):
                The progress bar. Defaults to None.

        Returns:
            ClassicalShadowComplex: The result of the classical shadow.
        """

        if shots is None or counts is None:
            raise ValueError("shots and counts should be specified.")
        if random_unitary_ids is None:
            raise ValueError("random_unitary_ids should be specified.")
        if selected_classical_registers is None:
            raise ValueError("selected_classical_registers should be specified.")

        return classical_shadow_complex(
            shots=shots,
            counts=counts,
            random_unitary_um=random_unitary_ids,
            selected_classical_registers=selected_classical_registers,
            backend=backend,
            pbar=pbar,
        )
