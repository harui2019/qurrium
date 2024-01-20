"""
================================================================
WaveContainer
(:mod:`qurry.qurry.qurrium.container.waves_static`)
================================================================

"""

from typing import Literal, Union, Optional, Hashable, MutableMapping
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit import Gate, Instruction


from .waves_dynamic import _add, _remove


class WaveContainer(dict[Hashable, QuantumCircuit]):
    """WaveContainer is a customized dictionary for storing waves."""

    __name__ = "WaveContainer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: QuantumCircuit,
        key: Optional[Hashable] = None,
        replace: Literal[True, False, "duplicate"] = False,
    ) -> Hashable:
        """Add wave to container.

        Args:
            wave (QuantumCircuit): The wave circuit.
            key (Optional[Hashable], optional): The key of wave in 'fict' `.waves`. Defaults to None.
            replace (Literal[True, False, "duplicate"], optional): Replace the wave with same key or not. Defaults to False.

        Returns:
            Hashable: The key of wave in 'dict' `.waves`.

        Raises:
            KeyError: If the wave with same key exists and `replace==False`.
        """
        return _add(_wave_container=self, wave=wave, key=key, replace=replace)

    def remove(
        self: MutableMapping[Hashable, QuantumCircuit],
        key: Hashable,
    ) -> None:
        """Remove wave from container.

        Args:
            key (Hashable): The key of wave in 'dict' `.waves`.
        """
        _remove(self, key)

    def get_wave(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
        run_by: Optional[
            Literal["gate", "operator", "instruction", "copy", "call"]
        ] = None,
    ) -> Union[
        list[Union[Gate, Operator, Instruction, QuantumCircuit]],
        Union[Gate, Operator, Instruction, QuantumCircuit],
    ]:
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

        if run_by == "operator":
            return Operator(self[wave])
        if run_by == "gate":
            return self[wave].to_gate()
        if run_by == "instruction":
            return self[wave].to_instruction()
        if run_by == "copy":
            return self[wave].copy()
        if run_by == "call":
            return self[wave]

        return self[wave].to_gate()

    def call(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[QuantumCircuit], QuantumCircuit]:
        """Export wave function as `QuantumCircuit`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.

                Defaults to None.

        Returns:
            QuantumCircuit: The circuit of wave function.
        """
        return self.get_wave(
            wave=wave,
            run_by="call",
        )

    def __call__(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[QuantumCircuit], QuantumCircuit]:
        return self.call(wave=wave)

    def operator(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Operator], Operator]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.get_wave(
            wave=wave,
            run_by="operator",
        )

    def gate(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Gate], Gate]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.get_wave(
            wave=wave,
            run_by="gate",
        )

    def copy_circuit(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Gate], Gate]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.get_wave(
            wave=wave,
            run_by="copy",
        )

    def instruction(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Gate], Gate]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.get_wave(
            wave=wave,
            run_by="instruction",
        )

    def has(
        self: MutableMapping[Hashable, QuantumCircuit],
        wavename: Hashable,
    ) -> bool:
        """Is there a wave with specific name.

        Args:
            wavename (Hashable): Name of wave which is used in `.waves`

        Returns:
            bool: Exist or not.
        """
        return wavename in self

    def __repr__(self):
        inner_lines = "\n".join(f"    {k}: ..." for k in self.keys())
        inner_lines2 = "{\n%s\n}" % inner_lines
        return (
            f"<{self.__name__}={inner_lines2} with {len(self)} "
            + "waves load, a customized dictionary>"
        )
