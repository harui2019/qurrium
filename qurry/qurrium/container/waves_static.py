from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit import Gate, Instruction

from typing import Literal, Union, Optional, Hashable, MutableMapping

from .waves_dynamic import _add, _remove


class WaveContainer(dict[Hashable, QuantumCircuit]):
    __name__ = "WaveContainer"

    @property
    def lastWave(self) -> QuantumCircuit:
        """The last wave function be called or used.
        Replace the property :prop:`waveNow`. in :cls:`QurryV4`"""
        if self.lastWaveKey == None:
            raise KeyError("No wave function added yet.")
        else:
            return self[self.lastWaveKey]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lastWaveKey = None

    def add(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: QuantumCircuit,
        key: Optional[Hashable] = None,
        replace: Literal[True, False, "duplicate"] = False,
    ) -> Hashable:
        self.lastWaveKey = _add(
            _wave_container=self, wave=wave, key=key, replace=replace
        )
        return self.lastWaveKey

    def remove(
        self: MutableMapping[Hashable, QuantumCircuit],
        key: Hashable,
    ) -> None:
        _remove(self, key)

    def get_wave(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
        runBy: Optional[
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
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.
            runBy (Optional[str], optional):
                Export as `Gate`, `Operator`, `Instruction` or a copy when input is `None`.
                Defaults to `None`.

        Returns:
            Union[
                list[Union[Gate, Operator, Instruction, QuantumCircuit]],
                Union[Gate, Operator, Instruction, QuantumCircuit]
            ]: The result of the wave as `Gate` or `Operator`.
        """

        if wave == None:
            wave = self.lastWave
        elif isinstance(wave, list):
            return [self.get_wave(w, runBy) for w in wave]

        if wave not in self:
            raise KeyError(f"Wave {wave} not found in {self}")

        if runBy == "operator":
            return Operator(self[wave])
        elif runBy == "gate":
            return self[wave].to_gate()
        elif runBy == "instruction":
            return self[wave].to_instruction()
        elif runBy == "copy":
            return self[wave].copy()
        elif runBy == "call":
            self.lastWaveKey = wave
            return self[wave]
        else:
            return self[wave].to_gate()

    def call(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[QuantumCircuit], QuantumCircuit]:
        """Export wave function as `QuantumCircuit`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            QuantumCircuit: The circuit of wave function.
        """
        return self.get_wave(
            wave=wave,
            runBy="call",
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
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.get_wave(
            wave=wave,
            runBy="operator",
        )

    def gate(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Gate], Gate]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.get_wave(
            wave=wave,
            runBy="gate",
        )

    def copy_circuit(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Gate], Gate]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.get_wave(
            wave=wave,
            runBy="copy",
        )

    def instruction(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
    ) -> Union[list[Gate], Gate]:
        """Export wave function as `Operator`.

        Args:
            wave (Optional[Hashable], optional):
                The key of wave in 'fict' `.waves`.
                If `wave==None`, then chooses `.lastWave` automatically added by last calling of `.addWave`.
                Defaults to None.

        Returns:
            Operator: The operator of wave function.
        """
        return self.get_wave(
            wave=wave,
            runBy="instruction",
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
        inner_lines = "\n".join("    %s: ..." % str(k) for k in self.keys())
        inner_lines2 = "{\n%s\n}" % inner_lines
        return f"<{self.__name__}={inner_lines2} with {len(self)} waves load, a customized dictionary>"
