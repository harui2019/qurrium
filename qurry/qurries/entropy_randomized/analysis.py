"""EntropyMeasureRandomized - Analysis (:mod:`qurry.qurries.entropy_randomized.analysis`)"""

from typing import Literal, Any, overload
from collections.abc import Iterable
from dataclasses import dataclass
import numpy as np

from .arguments import EMRArguments
from ...qurrium import (
    Commonparams,
    AnalysisPrototype,
    AnalyzeArgs,
    AnalysisMiddlewarePrototype,
    ProcessEntriesPrototype,
    AnalysisResultsPrototype,
)
from ...qurrium.utils import bitstring_mapping_getter
from ...process.randomized_measure.entangled_entropy import (
    randomized_entangled_entropy_mitigated,
    TargetSystemResult,
    AllSystemResult,
    PostProcessingBackendLabel,
    DEFAULT_PROCESS_BACKEND,
)
from ...process.utils import counts_list_recount_pyrust
from ...process.utils.purity import MitigatedResult, AllowedMitigatedInput


class EMRAnalyzeArgs(AnalyzeArgs, total=False):
    """The input of :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiAnalysis` and
    :meth:`~qurry.qurries.entropy_randomized.experiment.EMRExperiment.analyze`.
    """

    selected_qubits: list[int] | None
    """The selected qubits."""
    independent_all_system: bool
    """If True, then calculate the all system independently."""
    backend: PostProcessingBackendLabel
    """The backend for the process."""
    counts_used: Iterable[int] | None
    """The index of the counts used."""


@dataclass(frozen=True)
class EMRMiddleware(AnalysisMiddlewarePrototype):
    """The middleware entries between analyze and actual post-processing function."""

    __name__ = "EMRMiddleware"

    num_qubits: int
    """The number of qubits."""
    selected_qubits: list[int]
    """The selected qubits."""
    registers_mapping: dict[int, int]
    """The mapping of the classical registers with quantum registers.

    .. code-block:: python

        {
            0: 0, # The quantum register 0 is mapped to the classical register 0.
            1: 1, # The quantum register 1 is mapped to the classical register 1.
            5: 2, # The quantum register 5 is mapped to the classical register 2.
            7: 3, # The quantum register 7 is mapped to the classical register 3.
        }

    The key is the index of the quantum register with the numerical order.
    The value is the index of the classical register with the numerical order.
    """
    bitstring_mapping: dict[int, int]
    """The mapping of the bitstring with the classical registers.
    When there are mulitple classical registers, 
    the bitstring is the concatenation of the classical registers with space on bitstring.
    For example, there are three registers with the size of 4, 4, and 6, 
    which the first six bits are for the randomized measurement.

    .. code-block:: python

        {'010000 0100 0001': 1024}
        # The bitstring is '010000 0100 0001'.
        # The last four bits are the first classical register.
        # The middle four bits are the second classical register.
        # The first six bits are the last classical register for the randomized measurement.

    So, the mapping will be like this.

    .. code-block:: python


        {
            0: 10, # The classical register 0 is mapped to the bitstring on the index 0.
            1: 11, # The classical register 0 is mapped to the bitstring on the index 1.
            2: 12, # The classical register 0 is mapped to the bitstring on the index 2.
            3: 13, # The classical register 0 is mapped to the bitstring on the index 3.
            4: 14, # The classical register 0 is mapped to the bitstring on the index 4.
            5: 15, # The classical register 0 is mapped to the bitstring on the index 5.
        }

    But, if there is only one classical register, 
    the bitstring will map to the classical register directly.

    .. code-block:: python

        {'010000': 1024}

    Will be like this.

    .. code-block:: python

        {
            0: 0, # The classical register 0 is mapped to the bitstring on the index 0.
            1: 1, # The classical register 0 is mapped to the bitstring on the index 1.
            2: 2, # The classical register 0 is mapped to the bitstring on the index 2.
            3: 3, # The classical register 0 is mapped to the bitstring on the index 3.
            4: 4, # The classical register 0 is mapped to the bitstring on the index 4.
            5: 5, # The classical register 0 is mapped to the bitstring on the index 5.
        }

    """
    final_mapping: dict[int, int]
    """The final mapping of the classical registers after selection with the quantum registers.

    .. code-block:: python

        {
            "registers_mapping": {
                2: 0,
                3: 1
            },  # qubit index to original classical index
            "bitstring_mapping": {
                0: 5,
                1: 6,
            },  # original classical index to shifted index, which the index on full bitstring
            "final_mapping": {
                2: 5,
                3: 6
            },  # qubit index to shifted index, which the index on full bitstring
        }
    
    More details can be found in :func:`~qurry.qurrium.utils.counts.bitstring_mapping_getter`.
    """
    unitary_located: list[int] | None = None
    """The range of the unitary operator."""
    counts_used: Iterable[int] | None = None
    """The index of the counts used. If not specified, then use all counts."""

    def export(self) -> dict[str, Any]:
        """Export the results for file writing.

        Returns:
            dict[str, Any]: The data to be exported.
        """

        return {
            **self.asdict(),
            "counts_used": list(self.counts_used) if self.counts_used is not None else None,
        }

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Load the results from a dictionary.

        Args:
            raw_dict (dict[str, Any]): The data to load.

        Returns:
            The loaded results object.
        """
        missing_fields = set(cls.dataclass_fields()) - set(raw_dict.keys())
        if missing_fields:
            raise ValueError(f"Missing fields for {cls.__name__}: {missing_fields}")

        return cls(
            num_qubits=raw_dict["num_qubits"],
            selected_qubits=raw_dict["selected_qubits"],
            registers_mapping={int(k): int(v) for k, v in raw_dict["registers_mapping"].items()},
            bitstring_mapping={int(k): int(v) for k, v in raw_dict["bitstring_mapping"].items()},
            final_mapping={int(k): int(v) for k, v in raw_dict["final_mapping"].items()},
            unitary_located=(
                None
                if raw_dict.get("unitary_located") is None
                else [int(v) for v in raw_dict["unitary_located"]]
            ),
            counts_used=(
                None
                if raw_dict.get("counts_used") is None
                else [int(v) for v in raw_dict["counts_used"]]
            ),
        )


@dataclass(frozen=True)
class EMRProcessEntries(ProcessEntriesPrototype):
    """The entries for post-processing."""

    __name__ = "EMRProcessEntries"

    selected_classical_registers: list[int]
    """The selected classical registers."""
    existed_all_system: AllSystemResult | None
    """The source of all system."""
    backend: PostProcessingBackendLabel
    """The backend for the process."""

    def export(self) -> dict[str, Any]:
        """Export the results for file writing.

        Returns:
            dict[str, Any]: The data to be exported.
        """

        return {
            "shots": self.shots,
            "selected_classical_registers": self.selected_classical_registers,
            "existed_all_system": (
                EMRAllSystemResult(**self.existed_all_system).export()
                if self.existed_all_system is not None
                else None
            ),
            "backend": self.backend,
        }

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Load the results from a dictionary.

        Args:
            raw_dict (dict[str, Any]): The data to load.
        """
        missing_fields = set(cls.dataclass_fields()) - set(raw_dict.keys())
        if missing_fields:
            raise ValueError(f"Missing fields for {cls.__name__}: {missing_fields}")

        if raw_dict["existed_all_system"] is None:
            return cls(**raw_dict)

        existed_all_system_data = raw_dict.get("existed_all_system")
        raw_dict["existed_all_system"] = (
            EMRAllSystemResult.ingest(existed_all_system_data)
            if existed_all_system_data is not None
            else None
        )

        return cls(**raw_dict)


@dataclass(frozen=True)
class EMRTargetSystemResult(AnalysisResultsPrototype):
    """The target system result of
    :class:`~qurry.qurries.entropy_randomized.analysis.EMRAnalysis`."""

    __name__ = "EMRTargetSystemResult"

    purity: np.float64 | float
    """The purity of the system."""
    entropy: np.float64 | float
    """The entropy of the system."""
    purity_sd: np.float64 | float
    """The standard deviation of the purity."""
    entropy_sd: np.float64 | float
    """The standard deviation of the entropy."""
    purity_cells: dict[int, np.float64] | dict[int, float]
    """The purity of each single count."""

    num_classical_registers: int
    """The number of classical registers."""
    classical_registers: list[int] | None
    """The list of the index of the selected classical registers."""
    classical_registers_actually: list[int]
    """The list of the index of the selected classical registers which is actually used."""

    taking_time: float
    """The calculation time."""
    counts_num: int
    """The number of counts."""

    def side_product_fields(self) -> tuple[str, ...]:
        """The fields that will be stored as side product.

        Hint:
            Currently, only :attr:`purity_cells` is stored as side product.
        """
        return ("purity_cells",)

    def _pre_export_target_system(self) -> dict[str, Any]:
        """Pre-process the results for file writing.

        Returns:
            dict[str, Any]: The data to be exported.
        """

        return {
            "purity": float(self.purity),
            "entropy": float(self.entropy),
            "purity_sd": float(self.purity_sd),
            "entropy_sd": float(self.entropy_sd),
            "purity_cells": {k: float(v) for k, v in self.purity_cells.items()},
            "num_classical_registers": self.num_classical_registers,
            "classical_registers": self.classical_registers,
            "classical_registers_actually": self.classical_registers_actually,
            "taking_time": self.taking_time,
            "counts_num": self.counts_num,
        }

    def export(self) -> dict[str, Any]:
        """Export the results for file writing.

        Returns:
            dict[str, Any]: The data to be exported.
        """

        return self._pre_export_target_system()

    @classmethod
    def _pre_ingest_target_system(cls, raw_dict: dict[str, Any]) -> dict[str, Any]:
        """Pre-process the raw dictionary before ingestion.

        Args:
            raw_dict (dict[str, Any]): The raw read dictionary.

        Returns:
            dict[str, Any]: The pre-processed dictionary.
        """
        return {
            "purity": raw_dict["purity"],
            "entropy": raw_dict["entropy"],
            "purity_sd": raw_dict["purity_sd"],
            "entropy_sd": raw_dict["entropy_sd"],
            "purity_cells": {int(k): float(v) for k, v in raw_dict["purity_cells"].items()},
            "num_classical_registers": raw_dict["num_classical_registers"],
            "classical_registers": (
                None
                if raw_dict.get("classical_registers") is None
                else [int(v) for v in raw_dict["classical_registers"]]
            ),
            "classical_registers_actually": [
                int(v) for v in raw_dict["classical_registers_actually"]
            ],
            "taking_time": raw_dict["taking_time"],
            "counts_num": raw_dict["counts_num"],
        }

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Load the results from a dictionary.

        Args:
            raw_dict (dict[str, Any]): The data to load.

        Returns:
            The loaded results object.
        """

        return cls(**cls._pre_ingest_target_system(raw_dict))


@dataclass(frozen=True)
class EMRAllSystemResult(EMRTargetSystemResult):
    """The all system result of :class:`~qurry.qurries.entropy_randomized.analysis.EMRAnalysis`."""

    __name__ = "EMRAllSystemResult"

    preparing_datetime: str
    """The datetime string when preparing the all system result."""
    result_hash_id: str
    """The hash id of the result for verification."""
    all_system_source: Literal["independent"] | str
    """The name of source of all system.

    - independent: The all system is calculated independently.
    """

    def export(self) -> dict[str, Any]:
        """Export the results for file writing.

        Returns:
            dict[str, Any]: The data to be exported.
        """

        export_content = self._pre_export_target_system()
        export_content.update(
            {
                "preparing_datetime": self.preparing_datetime,
                "result_hash_id": self.result_hash_id,
                "all_system_source": self.all_system_source,
            }
        )
        return export_content

    @classmethod
    def ingest(cls, raw_dict: dict[str, Any]):
        """Load the results from a dictionary.

        Args:
            raw_dict (dict[str, Any]): The data to load.

        Returns:
            The loaded results object.
        """

        pre_ingest_target = cls._pre_ingest_target_system(raw_dict)
        return cls(
            **pre_ingest_target,
            preparing_datetime=raw_dict["preparing_datetime"],
            result_hash_id=raw_dict["result_hash_id"],
            all_system_source=raw_dict["all_system_source"],
        )


@dataclass(frozen=True)
class EMRMitigatedResult(AnalysisResultsPrototype):
    """The mitigated result of :class:`~qurry.qurries.entropy_randomized.analysis.EMRAnalysis`."""

    __name__ = "EMRMitigatedResult"

    error_rate: AllowedMitigatedInput
    """The error rate of the measurement from depolarizing error migigation calculated."""
    mitigated_purity: AllowedMitigatedInput
    """The mitigated purity of the subsystem."""
    mitigated_entropy: AllowedMitigatedInput
    """The mitigated entanglement entropy of the subsystem."""

    def export(self) -> dict[str, Any]:
        """Export the results for file writing.

        Returns:
            dict[str, Any]: The data to be exported.
        """

        export_content = {}
        for field in self.fields:
            value = getattr(self, field)
            export_content[field] = (
                value.tolist() if isinstance(value, np.ndarray) else float(value)
            )

        return export_content


class EMRResultsType(
    dict[
        Literal["target_system", "all_system", "mitigated"] | str,
        type[EMRTargetSystemResult] | type[EMRAllSystemResult] | type[EMRMitigatedResult],
    ],
):
    """The results of :class:`~qurry.qurries.classical_shadow.analysis.SUAnalysis`."""

    @overload
    def __getitem__(self, key: Literal["target_system"]) -> type[EMRTargetSystemResult]: ...
    @overload
    def __getitem__(self, key: Literal["all_system"]) -> type[EMRAllSystemResult]: ...
    @overload
    def __getitem__(self, key: Literal["mitigated"]) -> type[EMRMitigatedResult]: ...
    @overload
    def __getitem__(
        self, key: str
    ) -> type[EMRTargetSystemResult] | type[EMRAllSystemResult] | type[EMRMitigatedResult]: ...

    def __getitem__(self, key):
        return super().__getitem__(key)


class EMRResults(
    dict[
        Literal["target_system", "all_system", "mitigated"] | str,
        EMRTargetSystemResult | EMRAllSystemResult | EMRMitigatedResult,
    ]
):
    """The results of :class:`~qurry.qurries.classical_shadow.analysis.SUAnalysis`."""

    @overload
    def __getitem__(self, key: Literal["target_system"]) -> EMRTargetSystemResult: ...
    @overload
    def __getitem__(self, key: Literal["all_system"]) -> EMRAllSystemResult: ...
    @overload
    def __getitem__(self, key: Literal["mitigated"]) -> EMRMitigatedResult: ...
    @overload
    def __getitem__(
        self, key: str
    ) -> EMRTargetSystemResult | EMRAllSystemResult | EMRMitigatedResult: ...

    def __getitem__(self, key):
        return super().__getitem__(key)


class EMRAnalysis(
    AnalysisPrototype[
        EMRArguments,
        EMRAnalyzeArgs,
        EMRMiddleware,
        EMRProcessEntries,
        EMRResultsType,
        EMRResults,
    ]
):
    """The container for the analysis of
    :class:`~qurry.qurries.entropy_randomized.experiment.EMRExperiment`."""

    __name__ = "EMRAnalysis"

    @classmethod
    def analyze_arguments_type(cls) -> type[EMRAnalyzeArgs]:
        """The analyze arguments type for this analysis."""
        return EMRAnalyzeArgs

    @classmethod
    def middleware_entries_type(cls) -> type[EMRMiddleware]:
        """The middleware entries type for this analysis."""
        return EMRMiddleware

    @classmethod
    def postprocess_entries_type(cls) -> type[EMRProcessEntries]:
        """The post-processing entries type for this analysis."""
        return EMRProcessEntries

    @classmethod
    def available_results_types(cls) -> EMRResultsType:
        """The results type for this analysis."""
        return EMRResultsType(
            {
                "target_system": EMRTargetSystemResult,
                "all_system": EMRAllSystemResult,
                "mitigated": EMRMitigatedResult,
            }
        )

    @classmethod
    def quantities(
        cls,
        shots: int,
        counts: list[dict[str, int]],
        selected_classical_registers: Iterable[int] | None = None,
        existed_all_system: AllSystemResult | None = None,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    ) -> tuple[TargetSystemResult, AllSystemResult, MitigatedResult]:
        """Randomized entangled entropy with complex.

        Args:
            shots (int):
                The number of shots.
            counts (list[dict[str, int]]):
                The counts of the experiment.
            selected_classical_registers: Iterable[int] | None = None,
                The selected classical registers. Defaults to None.
            existed_all_system: AllSystemResult | None = None,
                The source of all system. Defaults to None.
            backend (PostProcessingBackendLabel, optional):
                The backend label. Defaults to DEFAULT_PROCESS_BACKEND.

        Returns:
            The target system result, all system result, and mitigated result.
        """

        return randomized_entangled_entropy_mitigated(
            shots=shots,
            counts=counts,
            selected_classical_registers=selected_classical_registers,
            existed_all_system=existed_all_system,
            backend=backend,
        )

    @classmethod
    def generate_entries(
        cls,
        arguments: EMRArguments,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: EMRAnalyzeArgs,
        existed_all_system: AllSystemResult | None = None,
    ) -> tuple[EMRAnalyzeArgs, EMRMiddleware, EMRProcessEntries, list[dict[str, int]]]:
        """Generate the entries for analysis.

        Args:
            arguments (EMRArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (EMRAnalyzeArgs): The analyze arguments.
            existed_all_system: AllSystemResult | None = None,
                The source of all system. Defaults to None.

        Returns:
            The generated entries for analysis and the possibly filtered counts.
        """

        counts_used = analyze_arguments.get("counts_used", None)
        if isinstance(counts_used, Iterable):
            if max(counts_used) >= len(counts):
                raise ValueError(
                    f"counts_used should be less than {len(counts)}, but get {max(counts_used)}."
                )
            counts = [counts[i] for i in counts_used]
        elif counts_used is not None:
            raise TypeError(
                f"counts_used should be Iterable[int] or None, but got {type(counts_used)}."
            )

        bitstring_mapping, final_mapping = bitstring_mapping_getter(
            counts, arguments.registers_mapping
        )

        selected_qubits = analyze_arguments.get("selected_qubits", None)
        selected_qubits = (
            [qi % arguments.actual_num_qubits for qi in selected_qubits]
            if selected_qubits
            else list(arguments.registers_mapping.keys())
        )
        if len(set(selected_qubits)) != len(selected_qubits):
            raise ValueError(
                f"selected_qubits should not have duplicated elements, but got {selected_qubits}."
            )

        counts_of_last_clreg = counts_list_recount_pyrust(
            counts,
            len(next(iter(counts[0]))),
            list(final_mapping.values()),
        )

        return (
            analyze_arguments,
            EMRMiddleware(
                num_qubits=arguments.actual_num_qubits,
                selected_qubits=selected_qubits,
                registers_mapping=arguments.registers_mapping,
                bitstring_mapping=bitstring_mapping,
                final_mapping=final_mapping,
                unitary_located=arguments.unitary_located,
                counts_used=counts_used,
            ),
            EMRProcessEntries(
                shots=commonparams.shots,
                selected_classical_registers=[
                    arguments.registers_mapping[qi] for qi in selected_qubits
                ],
                existed_all_system=existed_all_system,
                backend=analyze_arguments.get("backend", DEFAULT_PROCESS_BACKEND),
            ),
            counts_of_last_clreg,
        )

    @classmethod
    def perform_analysis(
        cls,
        arguments: EMRArguments,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: EMRAnalyzeArgs,
        serial: int,
        outfields: dict[str, Any] | None = None,
        datetime: str | None = None,
        existed_all_system: AllSystemResult | None = None,
    ):
        """Perform the analysis for the experiment.

        Args:
            arguments (EMRArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (EMRAnalyzeArgs): The analyze arguments.
            serial (int): The serial number of the analysis.
            outfields (dict[str, Any] | None, optional):
                The unused arguments of the analysis. Defaults to None.
            datetime (str | None, optional):
                The datetime of the analysis. Defaults to None.
            existed_all_system (AllSystemResult | None, optional):
                The source of all system. Defaults to None.

        Returns:
            The result of the analysis.
        """
        analyze_arguments, middleware_entries, postprocess_entries, counts_of_last_clreg = (
            cls.generate_entries(
                arguments,
                commonparams,
                counts,
                analyze_arguments,
                existed_all_system,
            )
        )

        tgt_sys_dict, all_sys_dict, mitigated_dict = cls.quantities(
            shots=commonparams.shots,
            counts=counts_of_last_clreg,
            selected_classical_registers=postprocess_entries.selected_classical_registers,
            existed_all_system=postprocess_entries.existed_all_system,
            backend=postprocess_entries.backend,
        )

        tgt_sys_result = EMRTargetSystemResult(**tgt_sys_dict)
        all_sys_result = EMRAllSystemResult(**all_sys_dict)
        mitigated_result = EMRMitigatedResult(**mitigated_dict)

        return cls(
            analyze_arguments=analyze_arguments,
            middleware_entries=middleware_entries,
            postprocess_entries=postprocess_entries,
            results=EMRResults(
                {
                    "target_system": tgt_sys_result,
                    "all_system": all_sys_result,
                    "mitigated": mitigated_result,
                }
            ),
            serial=serial,
            outfields=outfields,
            datetime=datetime,
        )

    def is_independent_all_system(self, count_used: Iterable[int]) -> bool:
        """Check if the all system is calculated independently.

        Args:
            count_used (Iterable[int]): The index of the counts used.

        Returns:
            True if the all system is calculated independently, False otherwise.
        """
        all_system_result = self.results.get("all_system", None)
        if not isinstance(all_system_result, EMRAllSystemResult):
            raise ValueError("The all system result is not available.")
        if all_system_result is None:
            return False

        counts_used_self = self.analyze_arguments.get("counts_used", None)
        if counts_used_self is None:
            counts_used_self = list(range(all_system_result.counts_num))

        return all_system_result.all_system_source == "independent" and set(
            counts_used_self
        ) == set(count_used)

    def get_all_system_result(self) -> AllSystemResult | None:
        """Get the all system result.

        Returns:
            The all system result if available, None otherwise.
        """
        all_system_result = self.results.get("all_system", None)
        if not isinstance(all_system_result, EMRAllSystemResult):
            return None

        return AllSystemResult(**all_system_result.asdict())
