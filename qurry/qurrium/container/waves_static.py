"""
================================================================
WaveContainer
(:mod:`qurry.qurry.qurrium.container.waves_static`)
================================================================

"""

from typing import Literal, Union, Optional, overload
from collections.abc import Hashable, Callable
import warnings

from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit import Gate, Instruction

from .waves_dynamic import _add, _remove, _process
from ...exceptions import QurryUnknownExportOption


class WaveContainer(dict[Hashable, QuantumCircuit]):
    """WaveContainer is a customized dictionary for storing waves."""

    __name__ = "WaveContainer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add(
        self,
        wave: QuantumCircuit,
        key: Optional[Hashable] = None,
        replace: Literal[True, False, "duplicate"] = True,
    ) -> Hashable:
        """Add wave to container.

        Args:
            wave (QuantumCircuit): The wave circuit.
            key (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`. Defaults to None.
            replace (Literal[True, False, "duplicate"], optional):
                Replace the wave with same key or not.
                Defaults to True.

        Returns:
            Hashable: The key of wave in 'dict' `.waves`.

        Raises:
            KeyError: If the wave with same key exists and `replace==False`.
        """
        return _add(_wave_container=self, wave=wave, key=key, replace=replace)

    def process(
        self, circuits: list[Union[QuantumCircuit, Hashable]]
    ) -> list[tuple[Hashable, QuantumCircuit]]:
        """Process the circuits in container.

        Args:
            circuits (list[Union[QuantumCircuit, Hashable]]):
                The circuits or keys of circuits in container.

        Returns:
            list[tuple[Hashable, QuantumCircuit]]: The processed circuits.
        """
        return _process(self, circuits)

    def remove(self, key: Hashable) -> None:
        """Remove wave from container.

        Args:
            key (Hashable): The key of wave in 'dict' `.waves`.
        """
        _remove(self, key)

    @overload
    def get_wave(self, wave: list[Hashable], run_by: Literal["gate"]) -> list[Gate]: ...

    @overload
    def get_wave(self, wave: list[Hashable], run_by: Literal["operator"]) -> list[Operator]: ...

    @overload
    def get_wave(
        self, wave: list[Hashable], run_by: Literal["instruction"]
    ) -> list[Instruction]: ...

    @overload
    def get_wave(
        self, wave: list[Hashable], run_by: Optional[Literal["copy", "call"]]
    ) -> list[QuantumCircuit]: ...

    @overload
    def get_wave(self, wave: Hashable, run_by: Literal["gate"]) -> Gate: ...

    @overload
    def get_wave(self, wave: Hashable, run_by: Literal["operator"]) -> Operator: ...

    @overload
    def get_wave(self, wave: Hashable, run_by: Literal["instruction"]) -> Instruction: ...

    @overload
    def get_wave(
        self, wave: Hashable, run_by: Optional[Literal["copy", "call"]]
    ) -> QuantumCircuit: ...

    def get_wave(self, wave=None, run_by=None):
        """Parse wave Circuit into `Instruction` as `Gate` or `Operator` on `QuantumCircuit`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                Defaults to None.
            run_by (Optional[str], optional):
                Export as `Gate`, `Operator`, `Instruction` or a copy when input is `None`.
                Defaults to `None`.


        Raises:
            ValueError: If `wave is None`.
            KeyError: If `wave` not in `self`.

        Returns:
            Union[
                list[Union[Gate, Operator, Instruction, QuantumCircuit]],
                Union[Gate, Operator, Instruction, QuantumCircuit]
            ]: The result of the wave as `Gate` or `Operator`.
        """

        if wave is None:
            raise ValueError("Need to input wave name.")
        if isinstance(wave, list):
            return [self.get_wave(w, run_by) for w in wave]

        if wave not in self:
            raise KeyError(f"Wave {wave} not found in {self}")

        actions: dict[
            str, Callable[[QuantumCircuit], Union[Gate, Operator, Instruction, QuantumCircuit]]
        ] = {
            "operator": Operator,
            "gate": lambda w: w.to_gate(),
            "instruction": lambda w: w.to_instruction(),
            "copy": lambda w: w.copy(),
            "call": lambda w: w,
        }
        run_by = "copy" if run_by is None else run_by
        if run_by not in actions:
            warnings.warn(
                "run_by should be 'gate', 'operator', 'instruction', 'copy' or 'call', "
                + f"but got {run_by}.",
                category=QurryUnknownExportOption,
            )

        return actions.get(run_by, lambda w: w.copy())(self[wave])

    @overload
    def call(self, wave: list[Hashable]) -> list[QuantumCircuit]: ...

    @overload
    def call(self, wave: Hashable) -> QuantumCircuit: ...

    def call(self, wave):
        """Export wave function as `QuantumCircuit`.

        Args:
            wave (Union[list[Hashable], Hashable]):
                The key of wave in 'dict' `.waves`.

        Returns:
            Union[list[QuantumCircuit], QuantumCircuit]:
                The circuit of wave function.
        """
        return self.get_wave(
            wave=wave,
            run_by="call",
        )

    def __call__(
        self, wave: Union[list[Hashable], Hashable]
    ) -> Union[list[QuantumCircuit], QuantumCircuit]:
        return self.call(wave=wave)

    def operator(self, wave: Union[list[Hashable], Hashable]) -> Union[list[Operator], Operator]:
        """Export wave function as `Operator`.

        Args:
            wave (Union[list[Hashable], Hashable]):
                The key of wave in 'dict' `.waves`.

        Returns:
            Union[list[Operator], Operator]:
                The operator of wave function.
        """
        return self.get_wave(
            wave=wave,
            run_by="operator",
        )

    def gate(self, wave: Union[list[Hashable], Hashable]) -> Union[list[Gate], Gate]:
        """Export wave function as `Gate`.

        Args:
            wave (Union[list[Hashable], Hashable]):
                The key of wave in 'dict' `.waves`.

        Returns:
            Union[list[Gate], Gate]:
                The gate of wave function.
        """
        return self.get_wave(
            wave=wave,
            run_by="gate",
        )

    def copy_circuit(
        self, wave: Union[list[Hashable], Hashable]
    ) -> Union[list[QuantumCircuit], QuantumCircuit]:
        """Export a copy of wave function as `QuantumCircuit`.

        Args:
            wave (Union[list[Hashable], Hashable]):
                The key of wave in 'dict' `.waves`.

        Returns:
            Union[list[QuantumCircuit], QuantumCircuit]:
                The copy circuit of wave function.
        """
        return self.get_wave(
            wave=wave,
            run_by="copy",
        )

    def instruction(
        self, wave: Union[list[Hashable], Hashable]
    ) -> Union[list[Instruction], Instruction]:
        """Export wave function as `Instruction`.

        Args:
            wave (Union[list[Hashable], Hashable]):
                The key of wave in 'dict' `.waves`.

        Returns:
            Union[list[Instruction], Instruction]:
                The instruction of wave function.
        """
        return self.get_wave(
            wave=wave,
            run_by="instruction",
        )

    def has(self, wavename: Hashable) -> bool:
        """Is there a wave with specific name.

        Args:
            wavename (Hashable): Name of wave which is used in `.waves`

        Returns:
            bool: Exist or not.
        """
        return wavename in self

    def __repr__(self):
        return f"{self.__name__}({super().__repr__()})"

    def _repr_oneline(self):
        return f"{self.__name__}(" + "{...}" + f", num={len(self)})"

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(f"{self.__name__}(" + "{...}" + f", num={len(self)})")
        else:
            original_repr = super().__repr__()
            original_repr_split = original_repr[1:-1].split(", ")
            length = len(original_repr_split)
            with p.group(2, f"{self.__name__}(" + "{", "})"):
                for i, item in enumerate(original_repr_split):
                    p.breakable()
                    p.text(item)
                    if i < length - 1:
                        p.text(",")

    def __str__(self):
        return super().__repr__()
