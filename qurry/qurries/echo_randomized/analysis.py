"""EchoListenRandomized - Analysis (:mod:`qurry.qurries.echo_randomized.analysis`)"""

from typing import Literal, Any
from collections.abc import Iterable
from dataclasses import dataclass
import numpy as np

from .arguments import ELRArguments
from ...qurrium import (
    Commonparams,
    AnalysisPrototype,
    AnalyzeArgs,
    AnalysisMiddlewarePrototype,
    ProcessEntriesPrototype,
    AnalysisResultsPrototype,
)
from ...qurrium.utils import bitstring_mapping_getter
from ...process.availability import PostProcessingBackendLabel
from ...process.utils import counts_list_recount_pyrust
from ...process.randomized_measure.wavefunction_overlap import (
    randomized_overlap_echo,
    DEFAULT_PROCESS_BACKEND,
    WaveFunctionOverlapResult,
)


class ELRAnalyzeArgs(AnalyzeArgs, total=False):
    """The input of :meth:`~qurry.qurrium.qurrium.QurriumPrototype.multiAnalysis` and
    :meth:`~qurry.qurries.echo_randomized.experiment.ELRExperiment.analyze`.
    """

    selected_classical_registers: Iterable[int] | None
    """The list of **the index of the selected_classical_registers**.
    It's not the qubit index of first or second quantum circuit,
    but their corresponding classical registers."""
    backend: PostProcessingBackendLabel
    """The backend for the process."""
    counts_used: Iterable[int] | None
    """The index of the counts used."""


@dataclass(frozen=True)
class ELRMiddleware(AnalysisMiddlewarePrototype):
    """The middleware entries between analyze and actual post-processing function."""

    __name__ = "ELRMiddleware"

    num_clregs: int
    """The number of qubits."""
    registers_mapping_1: dict[int, int]
    """The mapping of the classical registers with quantum registers.
    for the first quantum circuit.

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
    registers_mapping_2: dict[int, int]
    """The mapping of the classical registers with quantum registers.
    for the second quantum circuit.

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
    bitstring_mapping_1: dict[int, int]
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
    bitstring_mapping_2: dict[int, int]
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
    final_mapping_1: dict[int, int]
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
    final_mapping_2: dict[int, int]
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
    unitary_located_mapping_1: dict[int, int]
    """The range of the unitary operator for the first quantum circuit.

    .. code-block:: python

        {
            0: 0, # The quantum register 0 is used for the unitary operator 0.
            1: 1, # The quantum register 1 is used for the unitary operator 1.
            5: 2, # The quantum register 5 is used for the unitary operator 2.
            7: 3, # The quantum register 7 is used for the unitary operator 3.
        }

    The key is the index of the quantum register with the numerical order.
    The value is the index of the unitary operator with the numerical order.
    """
    unitary_located_mapping_2: dict[int, int]
    """The range of the unitary operator for the second quantum circuit.

    .. code-block:: python

        {
            0: 0, # The quantum register 0 is used for the unitary operator 0.
            1: 1, # The quantum register 1 is used for the unitary operator 1.
            5: 2, # The quantum register 5 is used for the unitary operator 2.
            7: 3, # The quantum register 7 is used for the unitary operator 3.
        }

    The key is the index of the quantum register with the numerical order.
    The value is the index of the unitary operator with the numerical order.
    """
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
            num_clregs=raw_dict["num_clregs"],
            registers_mapping_1={
                int(k): int(v) for k, v in raw_dict["registers_mapping_1"].items()
            },
            registers_mapping_2={
                int(k): int(v) for k, v in raw_dict["registers_mapping_2"].items()
            },
            bitstring_mapping_1={
                int(k): int(v) for k, v in raw_dict["bitstring_mapping_1"].items()
            },
            bitstring_mapping_2={
                int(k): int(v) for k, v in raw_dict["bitstring_mapping_2"].items()
            },
            final_mapping_1={int(k): int(v) for k, v in raw_dict["final_mapping_1"].items()},
            final_mapping_2={int(k): int(v) for k, v in raw_dict["final_mapping_2"].items()},
            unitary_located_mapping_1={
                int(k): int(v) for k, v in raw_dict["unitary_located_mapping_1"].items()
            },
            unitary_located_mapping_2={
                int(k): int(v) for k, v in raw_dict["unitary_located_mapping_2"].items()
            },
            counts_used=(
                None
                if raw_dict.get("counts_used") is None
                else [int(v) for v in raw_dict["counts_used"]]
            ),
        )


@dataclass(frozen=True)
class ELRProcessEntries(ProcessEntriesPrototype):
    """The entries for post-processing."""

    __name__ = "ELRProcessEntries"

    selected_classical_registers: list[int]
    """The selected classical registers."""


@dataclass(frozen=True)
class ELROverlapResult(AnalysisResultsPrototype):
    """The default results of :class:`~qurry.qurries.echo_randomized.analysis.ELRAnalysis`,
    which contains only wavefunction overlap or Loschmidt echo."""

    __name__ = "ELROverlapResult"

    echo: np.float64 | float
    """The overlap value."""
    echo_sd: np.float64 | float
    """The overlap standard deviation."""
    echo_cells: dict[int, np.float64] | dict[int, float]
    """The overlap of each single count."""
    num_classical_registers: int
    """The number of classical registers."""
    classical_registers: list[int] | None
    """The list of the index of the selected classical registers."""
    classical_registers_actually: list[int]
    """The list of the index of the selected classical registers which is actually used."""
    # refactored
    counts_num: int
    """The number of first counts and second counts."""
    taking_time: float
    """The calculation time."""

    def side_product_fields(self) -> tuple[str, ...]:
        """The fields that will be stored as side product.

        Hint:
            Currently, only :attr:`echo_cells` is stored as side product.
        """
        return ("echo_cells",)

    def export(self) -> dict[str, Any]:
        """Export the results for file writing.

        Returns:
            dict[str, Any]: The data to be exported.
        """

        return {
            "echo": float(self.echo),
            "echo_sd": float(self.echo_sd),
            "echo_cells": {k: float(v) for k, v in self.echo_cells.items()},
            "num_classical_registers": self.num_classical_registers,
            "classical_registers": self.classical_registers,
            "classical_registers_actually": self.classical_registers_actually,
            "counts_num": self.counts_num,
            "taking_time": self.taking_time,
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
            echo=raw_dict["echo"],
            echo_sd=raw_dict["echo_sd"],
            echo_cells={int(k): float(v) for k, v in raw_dict["echo_cells"].items()},
            num_classical_registers=raw_dict["num_classical_registers"],
            classical_registers=(
                None
                if raw_dict.get("classical_registers") is None
                else [int(v) for v in raw_dict["classical_registers"]]
            ),
            classical_registers_actually=[int(v) for v in raw_dict["classical_registers_actually"]],
            counts_num=raw_dict["counts_num"],
            taking_time=raw_dict["taking_time"],
        )


class ELRAnalysis(
    AnalysisPrototype[
        ELRArguments,
        ELRAnalyzeArgs,
        ELRMiddleware,
        ELRProcessEntries,
        dict[Literal["target_system"] | str, type[ELROverlapResult]],
        dict[Literal["target_system"] | str, ELROverlapResult],
    ]
):
    """The container for the analysis of
    :class:`~qurry.qurries.echo_randomized.experiment.ELRExperiment`."""

    __name__ = "ELRAnalysis"

    @classmethod
    def analyze_arguments_type(cls) -> type[ELRAnalyzeArgs]:
        """The analyze arguments type for this analysis."""
        return ELRAnalyzeArgs

    @classmethod
    def middleware_entries_type(cls) -> type[ELRMiddleware]:
        """The middleware entries type for this analysis."""
        return ELRMiddleware

    @classmethod
    def postprocess_entries_type(cls) -> type[ELRProcessEntries]:
        """The post-processing entries type for this analysis."""
        return ELRProcessEntries

    @classmethod
    def available_results_types(cls) -> dict[str, type[ELROverlapResult]]:
        """The results type for this analysis."""
        return {"target_system": ELROverlapResult}

    @classmethod
    def quantities(
        cls,
        shots: int,
        first_counts: list[dict[str, int]],
        second_counts: list[dict[str, int]],
        selected_classical_registers: Iterable[int] | None = None,
        backend: PostProcessingBackendLabel = DEFAULT_PROCESS_BACKEND,
    ) -> WaveFunctionOverlapResult:
        """Calculate the wavefunction overlap from counts.

        Args:
            shots (int):
                Shots of the experiment on quantum machine.
            first_counts (list[dict[str, int]]):
                Counts of the experiment on quantum machine.
            second_counts (list[dict[str, int]]):
                Counts of the experiment on quantum machine.
            selected_classical_registers (Iterable[int] | None, optional):
                The list of **the index of the selected_classical_registers**.
            backend (PostProcessingBackendLabel, optional):
                Backend for the process. Defaults to DEFAULT_PROCESS_BACKEND.

        Returns:
            WaveFuctionOverlapResult: A dictionary contains purity, entropy,
                a list of each overlap, puritySD, degree, actual measure range, bitstring range.
        """

        return randomized_overlap_echo(
            shots=shots,
            first_counts=first_counts,
            second_counts=second_counts,
            selected_classical_registers=selected_classical_registers,
            backend=backend,
        )

    @classmethod
    def generate_entries(
        cls,
        arguments: ELRArguments,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: ELRAnalyzeArgs,
    ) -> tuple[
        ELRAnalyzeArgs,
        ELRMiddleware,
        ELRProcessEntries,
        tuple[list[dict[str, int]], list[dict[str, int]]],
    ]:
        """Generate the entries for analysis.

        Args:
            arguments (ELRArguments): The arguments for the experiment.
            commonparams (Commonparams): The common parameters for the experiment.
            counts (list[dict[str, int]]): The counts from the experiment.
            analyze_arguments (ELRAnalyzeArgs): The analyze arguments.

        Returns:
            The generated entries for analysis.
        """
        existed_classical_registers = list(arguments.registers_mapping_1.values())
        existed_classical_registers_check = list(arguments.registers_mapping_2.values())
        assert existed_classical_registers == existed_classical_registers_check, (
            "The classical registers of two circuits should be the same, "
            + f"but got {existed_classical_registers} and {existed_classical_registers_check}."
            + f"from registers_mapping_1: {arguments.registers_mapping_1} and "
            + f"registers_mapping_2: {arguments.registers_mapping_2}. "
            + "This should be ensured in the function 'params_control' of experiment."
        )
        assert existed_classical_registers == list(range(len(existed_classical_registers))), (
            "The classical registers should be continuous, "
            + f"but got {existed_classical_registers}. "
            + f"from registers_mapping_1: {arguments.registers_mapping_1} and "
            + f"registers_mapping_2: {arguments.registers_mapping_2}. "
            + "This should be ensured in the function 'params_control' of experiment."
        )

        num_clregs = len(existed_classical_registers)
        selected_classical_registers = analyze_arguments.get("selected_classical_registers", None)
        selected_classical_registers = (
            list(arguments.registers_mapping_1.values())
            if selected_classical_registers is None
            else [ci % num_clregs for ci in selected_classical_registers]
        )

        if len(set(selected_classical_registers)) != len(selected_classical_registers):
            raise ValueError(
                "The selected_classical_registers should not have duplicate values, "
                + f"but got {selected_classical_registers}."
            )
        not_existed_classical_registers = set(selected_classical_registers) - set(
            existed_classical_registers
        )
        if not_existed_classical_registers:
            raise ValueError(
                f"Some classical registers {not_existed_classical_registers} "
                + "are not existed in the register mapping of two circuit. "
                + f"registers_mapping_1: {arguments.registers_mapping_1}, "
                + f"registers_mapping_2: {arguments.registers_mapping_2}, "
                + f"selected: {selected_classical_registers}"
            )

        first_counts = counts[: arguments.times]
        second_counts = counts[arguments.times :]
        assert len(first_counts) == len(second_counts), (
            "The number of first and second counts should be the same, "
            + f"but got {len(first_counts)} and {len(second_counts)}. "
            + f"from counts with length {len(counts)}, "
            + f"times: {arguments.times}."
        )
        bitstring_mapping_1, final_mapping_1 = bitstring_mapping_getter(
            first_counts, arguments.registers_mapping_1
        )
        bitstring_mapping_2, final_mapping_2 = bitstring_mapping_getter(
            second_counts, arguments.registers_mapping_2
        )
        counts_used = analyze_arguments.get("counts_used", None)
        if isinstance(counts_used, Iterable):
            if max(counts_used) >= len(counts):
                raise ValueError(
                    f"counts_used should be less than {len(counts)}, but get {max(counts_used)}."
                )
            first_counts = [first_counts[i] for i in counts_used]
            second_counts = [second_counts[i] for i in counts_used]
        elif counts_used is not None:
            raise TypeError(
                f"counts_used should be Iterable[int] or None, but got {type(counts_used)}."
            )

        first_counts_of_last_clreg = counts_list_recount_pyrust(
            first_counts,
            len(next(iter(first_counts[0]))),
            list(final_mapping_1.values()),
        )
        second_counts_of_last_clreg = counts_list_recount_pyrust(
            second_counts,
            len(next(iter(second_counts[0]))),
            list(final_mapping_2.values()),
        )

        return (
            analyze_arguments,
            ELRMiddleware(
                num_clregs=num_clregs,
                registers_mapping_1=arguments.registers_mapping_1,
                registers_mapping_2=arguments.registers_mapping_2,
                bitstring_mapping_1=bitstring_mapping_1,
                bitstring_mapping_2=bitstring_mapping_2,
                final_mapping_1=final_mapping_1,
                final_mapping_2=final_mapping_2,
                unitary_located_mapping_1=arguments.unitary_located_mapping_1,
                unitary_located_mapping_2=arguments.unitary_located_mapping_2,
                counts_used=counts_used,
            ),
            ELRProcessEntries(
                shots=commonparams.shots,
                selected_classical_registers=selected_classical_registers,
            ),
            (first_counts_of_last_clreg, second_counts_of_last_clreg),
        )

    @classmethod
    def perform_analysis(
        cls,
        arguments: ELRArguments,
        commonparams: Commonparams,
        counts: list[dict[str, int]],
        analyze_arguments: ELRAnalyzeArgs,
        serial: int,
        outfields: dict[str, Any] | None = None,
        datetime: str | None = None,
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

        Returns:
            The result of the analysis.
        """
        (
            analyze_arguments,
            middleware_entries,
            postprocess_entries,
            (first_counts_of_last_clreg, second_counts_of_last_clreg),
        ) = cls.generate_entries(
            arguments,
            commonparams,
            counts,
            analyze_arguments,
        )

        wavefunction_overlap_dict = cls.quantities(
            shots=commonparams.shots,
            first_counts=first_counts_of_last_clreg,
            second_counts=second_counts_of_last_clreg,
            selected_classical_registers=postprocess_entries.selected_classical_registers,
            backend=analyze_arguments.get("backend", DEFAULT_PROCESS_BACKEND),
        )

        return cls(
            analyze_arguments=analyze_arguments,
            middleware_entries=middleware_entries,
            postprocess_entries=postprocess_entries,
            results={"target_system": ELROverlapResult(**wavefunction_overlap_dict)},
            serial=serial,
            outfields=outfields,
            datetime=datetime,
        )
