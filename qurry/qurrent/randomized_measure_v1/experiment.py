"""
===========================================================
EntropyMeasureRandomizedV1 - Experiment
(:mod:`qurry.qurrent.randomized_measure.experiment`)
===========================================================

This is a deprecated version of the randomized measure module.

"""

from typing import Union, Optional, Type, Any
from collections.abc import Iterable, Hashable
import warnings
import tqdm

from qiskit import QuantumCircuit

from .analysis import EntropyMeasureRandomizedV1Analysis
from .arguments import EntropyMeasureRandomizedV1Arguments, SHORT_NAME
from .utils import circuit_method_core, randomized_entangled_entropy_complex
from ...qurrium.experiment import ExperimentPrototype, Commonparams
from ...qurrium.utils.randomized import (
    local_random_unitary_operators,
    local_random_unitary_pauli_coeff,
    random_unitary,
)
from ...qurrium.utils.random_unitary import check_input_for_experiment
from ...process.utils import qubit_selector
from ...process.randomized_measure.entangled_entropy_v1 import (
    RandomizedEntangledEntropyMitigatedComplex,
    PostProcessingBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)
from ...tools import qurry_progressbar, ParallelManager
from ...exceptions import QurryArgumentsExpectedNotNone, QurryDeprecatedWarning


class EntropyMeasureRandomizedV1Experiment(ExperimentPrototype):
    """The instance of experiment."""

    __name__ = "EntropyMeasureRandomizedExperiment"

    @property
    def arguments_instance(self) -> Type[EntropyMeasureRandomizedV1Arguments]:
        """The arguments instance for this experiment."""
        return EntropyMeasureRandomizedV1Arguments

    args: EntropyMeasureRandomizedV1Arguments

    @property
    def analysis_instance(self) -> Type[EntropyMeasureRandomizedV1Analysis]:
        """The analysis instance for this experiment."""
        return EntropyMeasureRandomizedV1Analysis

    @classmethod
    def params_control(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        exp_name: str = "exps",
        times: int = 100,
        measure: Optional[Union[tuple[int, int], int]] = None,
        unitary_loc: Optional[Union[tuple[int, int], int]] = None,
        random_unitary_seeds: Optional[dict[int, dict[int, int]]] = None,
        **custom_kwargs: Any,
    ) -> tuple[EntropyMeasureRandomizedV1Arguments, Commonparams, dict[str, Any]]:
        """Handling all arguments and initializing a single experiment.

        Args:
            targets (list[tuple[Hashable, QuantumCircuit]]):
                The circuits of the experiment.
            exp_name (str, optional):
                The name of the experiment.
                Naming this experiment to recognize it when the jobs are pending to IBMQ Service.
                This name is also used for creating a folder to store the exports.
                Defaults to `'experiment'`.
            times (int):
                The number of random unitary operator. Defaults to 100.
                It will denote as `N_U` in the experiment name.
            measure (Optional[Union[tuple[int, int], int]]):
                The measure range. Defaults to None.
            unitary_loc (Optional[Union[tuple[int, int], int]]):
                The range of the unitary operator. Defaults to None.
            random_unitary_seeds (Optional[dict[int, dict[int, int]]]):
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
        num_qubits = target_circuit.num_qubits

        if measure is not None:
            warnings.warn(
                "The measure range is not available anymore, "
                + "it will be set to the whole qubits range.",
                QurryDeprecatedWarning,
            )
        measure = qubit_selector(num_qubits, degree=None)
        if unitary_loc is None:
            unitary_loc = num_qubits
        unitary_loc = qubit_selector(num_qubits, degree=unitary_loc)

        if (min(measure) < min(unitary_loc)) or (max(measure) > max(unitary_loc)):
            raise ValueError(
                f"unitary_loc range '{unitary_loc}' does not contain measure range '{measure}'."
            )

        exp_name = f"{exp_name}.N_U_{times}.{SHORT_NAME}"

        check_input_for_experiment(times, num_qubits, random_unitary_seeds)

        # pylint: disable=protected-access
        return EntropyMeasureRandomizedV1Arguments._filter(
            exp_name=exp_name,
            target_keys=[target_key],
            times=times,
            measure=measure,
            unitary_loc=unitary_loc,
            random_unitary_seeds=random_unitary_seeds,
            **custom_kwargs,
        )
        # pylint: enable=protected-access

    @classmethod
    def method(
        cls,
        targets: list[tuple[Hashable, QuantumCircuit]],
        arguments: EntropyMeasureRandomizedV1Arguments,
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

        if arguments.unitary_loc is None:
            actual_unitary_loc = (0, num_qubits)
            warnings.warn(
                f"| unitary_loc is not specified, using the whole qubits {actual_unitary_loc},"
                + " but it should be not None anymore here.",
                QurryArgumentsExpectedNotNone,
            )
        else:
            actual_unitary_loc = arguments.unitary_loc
        unitary_dict = {
            i: {
                j: (
                    random_unitary(2)
                    if arguments.random_unitary_seeds is None
                    else random_unitary(2, arguments.random_unitary_seeds[i][j])
                )
                for j in range(*actual_unitary_loc)
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
                    arguments.unitary_loc,
                    unitary_dict[i],
                    arguments.measure,
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
            local_random_unitary_operators,
            [(arguments.unitary_loc, unitary_dict[i]) for i in range(arguments.times)],
        )
        side_product["unitaryOP"] = dict(enumerate(unitary_operator_list))

        if isinstance(pbar, tqdm.tqdm):
            pbar.set_description_str(f"Writing 'randomized' with {arguments.workers_num} workers.")
        # side_product["randomized"] = {
        #     i: {j: qubitOpToPauliCoeff(unitary_dict[i][j]) for j in range(*arguments.unitary_loc)}
        #     for i in range(arguments.times)
        # }
        randomized_list = pool.starmap(
            local_random_unitary_pauli_coeff,
            [(arguments.unitary_loc, unitary_operator_list[i]) for i in range(arguments.times)],
        )
        side_product["randomized"] = dict(enumerate(randomized_list))

        return circ_list, side_product

    def analyze(
        self,
        degree: Optional[Union[tuple[int, int], int]] = None,
        counts_used: Optional[Iterable[int]] = None,
        workers_num: Optional[int] = None,
        independent_all_system: bool = False,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> EntropyMeasureRandomizedV1Analysis:
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
        if degree is None:
            raise ValueError("degree should be specified.")

        self.args: EntropyMeasureRandomizedV1Arguments
        self.reports: dict[int, EntropyMeasureRandomizedV1Analysis]
        shots = self.commons.shots
        measure = self.args.measure
        unitary_loc = self.args.unitary_loc
        if isinstance(counts_used, Iterable):
            if max(counts_used) >= len(self.afterwards.counts):
                raise ValueError(
                    "counts_used should be less than "
                    f"{len(self.afterwards.counts)}, but get {max(counts_used)}."
                )
            counts = [self.afterwards.counts[i] for i in counts_used]
        else:
            if counts_used is not None:
                raise ValueError(f"counts_used should be Iterable, but get {type(counts_used)}.")
            counts = self.afterwards.counts

        available_all_system_source = [
            k
            for k, v in self.reports.items()
            if (v.content.allSystemSource == "independent" and v.content.counts_used == counts_used)
        ]

        if len(available_all_system_source) > 0 and not independent_all_system:
            all_system_source = self.reports[available_all_system_source[-1]]
        else:
            all_system_source = None

        if isinstance(pbar, tqdm.tqdm):
            qs = self.quantities(
                shots=shots,
                counts=counts,
                degree=degree,
                measure=measure,
                all_system_source=all_system_source,
                backend=backend,
                workers_num=workers_num,
                pbar=pbar,
            )

        else:
            pbar_selfhost = qurry_progressbar(
                range(1),
                bar_format="simple",
            )

            with pbar_selfhost as pb_self:
                qs = self.quantities(
                    shots=shots,
                    counts=counts,
                    degree=degree,
                    measure=measure,
                    all_system_source=all_system_source,
                    backend=backend,
                    workers_num=workers_num,
                    pbar=pb_self,
                )
                pb_self.update()

        serial = len(self.reports)
        analysis = self.analysis_instance(
            serial=serial,
            shots=shots,
            unitary_loc=unitary_loc,
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
        degree: Optional[Union[tuple[int, int], int]] = None,
        measure: Optional[tuple[int, int]] = None,
        all_system_source: Optional["EntropyMeasureRandomizedV1Analysis"] = None,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
        workers_num: Optional[int] = None,
        pbar: Optional[tqdm.tqdm] = None,
    ) -> RandomizedEntangledEntropyMitigatedComplex:
        """Calculate entangled entropy.

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

        Args:
            shots (int): Shots of the experiment on quantum machine.
            counts (list[dict[str, int]]): Counts of the experiment on quantum machine.
            degree (Optional[Union[tuple[int, int], int]]): Degree of the subsystem.
            measure (Optional[tuple[int, int]], optional):
                Measuring range on quantum circuits. Defaults to None.
            all_system_source (Optional['EntropyRandomizedAnalysis'], optional):
                The source of the all system. Defaults to None.
            backend (PostProcessingBackendLabel, optional):
                Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.
            workers_num (Optional[int], optional):
                Number of multi-processing workers, it will be ignored if backend is Rust.
                if sets to 1, then disable to using multi-processing;
                if not specified, then use the number of all cpu counts by `os.cpu_count()`.
                Defaults to None.
            pbar (Optional[tqdm.tqdm], optional): Progress bar. Defaults to None.

        Returns:
            dict[str, float]: A dictionary contains
                purity, entropy, a list of each overlap, puritySD,
                purity of all system, entropy of all system,
                a list of each overlap in all system, puritySD of all system,
                degree, actual measure range, actual measure range in all system, bitstring range.
        """

        if shots is None or counts is None:
            raise ValueError("shots and counts should be specified.")

        return randomized_entangled_entropy_complex(
            shots=shots,
            counts=counts,
            degree=degree,
            measure=measure,
            all_system_source=all_system_source,
            backend=backend,
            workers_num=workers_num,
            pbar=pbar,
        )
