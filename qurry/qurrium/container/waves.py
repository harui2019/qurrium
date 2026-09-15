"""WaveContainer (:mod:`qurry.qurrium.utils.wave_container`)"""

from typing import Literal, overload
import warnings

from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit import Gate, Instruction

from ...capsule import CustomDict, DEFAULT_INDENT

WCKeyable = str | int | tuple[str | int, ...]
"""Type alias for keys used in WaveContainer.

It can be a string, an integer, or a tuple of strings and/or integers.
But number key is only for internal use, not for user.
"""


def naming_circuit(target_circuit: QuantumCircuit, target_key: WCKeyable, exp_name: str) -> str:
    """Generate a name from experiment name, target key, and target circuit name.

    Args:
        target_circuit (QuantumCircuit): Target circuit.
        target_key (WCKeyable): Target key.
        exp_name (str): Experiment name.

    Returns:
        str: The generated name.
    """
    name_components = []
    if isinstance(exp_name, str) and len(exp_name) > 0:
        name_components.append(exp_name)

    if isinstance(target_key, tuple):
        name_components.append("-".join(str(k) for k in target_key))
    elif isinstance(target_key, str):
        name_components.append(target_key)
    elif isinstance(target_key, int):
        pass

    if isinstance(target_circuit.name, str) and len(target_circuit.name) > 0:
        name_components.append(target_circuit.name)
    return ".".join(name_components)


GET_WAVE_RETURN = {
    "operator": Operator,
    "gate": lambda w: w.to_gate(),
    "instruction": lambda w: w.to_instruction(),
    "copy": lambda w: w.copy(),
    "call": lambda w: w,
}

MAX_ADD_ATTEMPTS = 1000
"""Maximum number of attempts to find a new serial key when adding waves."""


class WaveContainer(CustomDict[WCKeyable, QuantumCircuit]):
    """WaveContainer is a customized dictionary for storing
    :class:`~qiskit.circuit.QuantumCircuit`."""

    @staticmethod
    def wave_keyable_check(key: WCKeyable) -> bool:
        """Check if the key is a valid WCKeyable.

        Args:
            key (WCKeyable): The key to check.
        Returns:
            bool: True if the key is valid, False otherwise.
        """
        if isinstance(key, int):
            return False
        if not isinstance(key, (str, tuple)):
            return False
        if isinstance(key, tuple) and any(not isinstance(k, (str, int)) for k in key):
            return False
        return True

    def add(
        self,
        wave: QuantumCircuit,
        key: WCKeyable | None = None,
        replace: Literal[True, False, "duplicate"] = True,
    ) -> WCKeyable:
        """Add new wave function to measure.

        Args:
            wave (QuantumCircuit): The wave function or circuit to add.
            key (WCKeyable | None, optional):
                Given a specific key to add to the wave function or circuit,
                if `key == None`, then generate a number as key.
                Defaults to None.
            replace (Literal[True, False, "duplicate"], optional):
                If the key is already in the wave function or circuit,
                then replace the old wave function or circuit when `True`,
                or duplicate the wave function or circuit when `'duplicate'`.
                Otherwise, generate a number as key and raise warning when `False`.
                Defaults to `True`.

        Raises:
            RuntimeError: If a new serial key cannot be found.

        Returns:
            Key of given wave function in `.waves`.
        """

        if not isinstance(wave, QuantumCircuit):
            raise TypeError(f"waveCircuit should be a QuantumCircuit, not {type(wave)}")

        if not isinstance(replace, (bool, str)) or (
            isinstance(replace, str) and replace != "duplicate"
        ):
            raise TypeError(f"replace should be a bool or 'duplicate', not {type(replace)}")

        serial_key = len(self)
        max_tries = MAX_ADD_ATTEMPTS  # Prevent infinite loop
        while serial_key in self and max_tries > 0:
            serial_key += 1
            max_tries -= 1
        if max_tries == 0:
            raise RuntimeError(
                "Cannot find a new serial key for the wave container. "
                + f"Attended serial key from {len(self)} to {serial_key} are all occupied."
            )

        if key is None:
            self[serial_key] = wave
            return serial_key

        if isinstance(key, int):
            raise ValueError("Number key is only for internal use, not for user.")
        if not isinstance(key, (str, tuple)) and key is not None:
            raise TypeError(f"key should be str, tuple, or None, not {type(key)}")
        if isinstance(key, tuple) and any(not isinstance(k, (str, int)) for k in key):
            raise TypeError(
                "Each element of tuple key should be str or int. "
                + f"Got {[type(k) for k in key]}."
            )

        if key not in self:
            self[key] = wave
            return key

        if replace is True:
            self[key] = wave
            return key

        if replace is False:
            warnings.warn(
                f"Wave {key} already exists in {self}, "
                + f"so the new wave is added with key {serial_key}.",
            )
            self[serial_key] = wave
            return serial_key

        new_key = key + (serial_key,) if isinstance(key, tuple) else f"{key}.{serial_key}"
        self[new_key] = wave
        return new_key

    def _add_or_get(
        self, circ_or_key: QuantumCircuit | WCKeyable
    ) -> tuple[WCKeyable, QuantumCircuit]:
        """Add new wave function to measure or get the wave function from container.

        Args:
            circ_or_key (QuantumCircuit | WCKeyable):
                The wave function or circuit to add,
                or the key of wave function in container.
        Returns:
            The key and wave function in container.
        """

        if isinstance(circ_or_key, QuantumCircuit):
            key = self.add(circ_or_key)
            return key, self[key]
        if circ_or_key in self:
            return circ_or_key, self[circ_or_key]
        if self.wave_keyable_check(circ_or_key):
            raise KeyError(f"Wave {circ_or_key} not found in {self}")
        raise TypeError(
            "circ_or_key should be "
            + f"QuantumCircuit or key in container, not {type(circ_or_key)}"
        )

    def process(
        self, circuits: list[QuantumCircuit | WCKeyable]
    ) -> list[tuple[WCKeyable, QuantumCircuit]]:
        """Process the circuits in container.

        Args:
            circuits (list[QuantumCircuit | WCKeyable]):
                The circuits or keys of circuits in container.

        Returns:
            The processed circuits.
        """
        return [self._add_or_get(circ_or_key) for circ_or_key in circuits]

    def remove(self, key: WCKeyable) -> None:
        """Remove wave from container.

        Args:
            key (WCKeyable): The key of wave in 'dict' `.waves`.
        """
        del self[key]

    @overload
    def get_wave(self, key_or_keys: WCKeyable, run_by: Literal["gate"]) -> Gate: ...
    @overload
    def get_wave(self, key_or_keys: WCKeyable, run_by: Literal["operator"]) -> Operator: ...
    @overload
    def get_wave(self, key_or_keys: WCKeyable, run_by: Literal["instruction"]) -> Instruction: ...
    @overload
    def get_wave(
        self, key_or_keys: WCKeyable, run_by: Literal["copy", "call"] | None = None
    ) -> QuantumCircuit: ...

    @overload
    def get_wave(self, key_or_keys: list[WCKeyable], run_by: Literal["gate"]) -> list[Gate]: ...
    @overload
    def get_wave(
        self, key_or_keys: list[WCKeyable], run_by: Literal["operator"]
    ) -> list[Operator]: ...
    @overload
    def get_wave(
        self, key_or_keys: list[WCKeyable], run_by: Literal["instruction"]
    ) -> list[Instruction]: ...
    @overload
    def get_wave(
        self, key_or_keys: list[WCKeyable], run_by: Literal["copy", "call"] | None = None
    ) -> list[QuantumCircuit]: ...

    def get_wave(self, key_or_keys, run_by=None):
        """Transform wave function to different forms.

        Args:
            key_or_keys (list[WCKeyable] | WCKeyable):
                The key of wave in the container.
            run_by (str | None, optional):
                The method to export wave function.
                - "operator": Export as :class:`~qiskit.quantum_info.Operator`.
                - "gate": Export as :class:`~qiskit.circuit.Gate`.
                - "instruction": Export as :class:`~qiskit.circuit.Instruction`.
                - "copy": Export as a copy of :class:`~qiskit.circuit.QuantumCircuit`.
                - "call": Export the original :class:`~qiskit.circuit.QuantumCircuit`.
                if `run_by is None` , it will return a copy of
                :class:`~qiskit.circuit.QuantumCircuit`.
                Defaults to None.

        Raises:
            ValueError: If `run_by` is not valid.
            KeyError: If the wave is not found in the container.

        Returns:
            The result of the wave.
        """

        if isinstance(key_or_keys, list):
            return [self.get_wave(w, run_by) for w in key_or_keys]

        if run_by not in GET_WAVE_RETURN:
            raise ValueError(
                f"run_by should be {list(GET_WAVE_RETURN.keys())}, but got {run_by}.",
            )
        if key_or_keys not in self:
            raise KeyError(f"Wave {key_or_keys} not found in {self}")

        return GET_WAVE_RETURN.get(run_by, lambda w: w.copy())(self[key_or_keys])

    @overload
    def operator(self, key_or_keys: WCKeyable) -> Operator: ...
    @overload
    def operator(self, key_or_keys: list[WCKeyable]) -> list[Operator]: ...

    def operator(self, key_or_keys):
        """Export wave function as `Operator`.

        Args:
            wave (list[WCKeyable] | WCKeyable):
                The key of wave in 'dict' `.waves`.

        Returns:
            The operator of wave function.
        """
        return self.get_wave(key_or_keys=key_or_keys, run_by="operator")

    @overload
    def gate(self, key_or_keys: list[WCKeyable]) -> list[Gate]: ...
    @overload
    def gate(self, key_or_keys: WCKeyable) -> Gate: ...

    def gate(self, key_or_keys):
        """Export wave function as :class:`~qiskit.circuit.Gate`.

        Args:
            key_or_keys (list[WCKeyable] | WCKeyable):
                The key of wave in the container.

        Returns:
            The gate of wave function.
        """
        return self.get_wave(key_or_keys=key_or_keys, run_by="gate")

    @overload
    def copy_circuit(self, key_or_keys: WCKeyable) -> QuantumCircuit: ...
    @overload
    def copy_circuit(self, key_or_keys: list[WCKeyable]) -> list[QuantumCircuit]: ...

    def copy_circuit(self, key_or_keys):
        """Export a copy of wave function as :class:`~qiskit.circuit.QuantumCircuit`.

        Args:
            key_or_keys (list[WCKeyable] | WCKeyable):
                The key of wave in the container.

        Returns:
            The copy circuit of wave function.
        """
        return self.get_wave(key_or_keys=key_or_keys, run_by="copy")

    @overload
    def instruction(self, key_or_keys: WCKeyable) -> Instruction: ...
    @overload
    def instruction(self, key_or_keys: list[WCKeyable]) -> list[Instruction]: ...

    def instruction(self, key_or_keys):
        """Export wave function as :class:`~qiskit.circuit.Instruction`.

        Args:
            key_or_keys (list[WCKeyable] | WCKeyable):
                The key of wave in the container.

        Returns:
            The instruction of wave function.
        """
        return self.get_wave(key_or_keys=key_or_keys, run_by="instruction")

    def has(self, key: WCKeyable) -> bool:
        """Check if the wave exists in container.

        Args:
            key (WCKeyable): Key of wave which is used in container.

        Returns:
            bool: Exist or not.
        """
        return key in self

    def __repr__(self):
        return f"{self.__class__.__name__}(num={len(self)}, {super().__repr__()})"

    def _repr_oneline(self):
        return f"{self.__class__.__name__}(num={len(self)}, " + (r"{...}" if self else r"{}") + ")"

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(self._repr_oneline())
            return

        if not self:
            p.text(f"{self.__class__.__name__}" + "(num=0, {})")
            return

        with p.group(DEFAULT_INDENT, f"{self.__class__.__name__}(num={len(self)}" + ", {", "})"):
            for i, (k, v) in enumerate(self.items()):
                p.breakable()
                p.pretty(k)
                p.text(": ")
                p.pretty(v)
                if i < len(self) - 1:
                    p.text(",")
