"""
================================================================
Dynamic Wave Container - A experimental feature of Qurry
(:mod:`qurry.qurrium.container.waves_dynamic`)
================================================================
"""

from typing import Literal, Union, Optional, Type, MutableMapping, overload
from collections.abc import Hashable, Callable
import warnings

from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit import Gate, Instruction


def add(
    self: MutableMapping[Hashable, QuantumCircuit],
    wave: QuantumCircuit,
    key: Optional[Hashable] = None,
    replace: Literal[True, False, "duplicate"] = False,
) -> Hashable:
    """Add new wave function to measure.

    Args:
        _wave_container (WaveContainer): The container of waves.
        wave (QuantumCircuit): The wave function or circuit to add.
        key (Optional[Hashable], optional):
            Given a specific key to add to the wave function or circuit,
            if `key == None`, then generate a number as key.
            Defaults to `None`.
        replace (Literal[True, False, &#39;duplicate&#39;], optional):
            If the key is already in the wave function or circuit,
            then replace the old wave function or circuit when `True`,
            or duplicate the wave function or circuit when `'duplicate'`,
            otherwise only changes `.lastwave`.
            Defaults to `False`.

    Returns:
        Optional[Hashable]: Key of given wave function in `.waves`.
    """
    return _add(self, wave, key, replace)


def process(
    self, circuits: list[Union[QuantumCircuit, Hashable]]
) -> list[tuple[Hashable, QuantumCircuit]]:
    """Process the circuits for Qurrium.

    Args:
        circuits (list[Union[QuantumCircuit, Hashable]]): The circuits.

    Raises:
        KeyError: If the wave not found in the container.
        ValueError: If the circuit is invalid.
    """
    return _process(self, circuits)


def remove(self, key: Hashable):
    """Remove wave function from measure.

    Args:
        key (Hashable): The key of wave function or circuit.
    """
    return _remove(self, key)


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


@overload
def get_wave(
    self, wave: list[Hashable], run_by: Optional[Literal["copy", "call"]]
) -> list[QuantumCircuit]: ...
@overload
def get_wave(self, wave: list[Hashable], run_by: Literal["gate"]) -> list[Gate]: ...
@overload
def get_wave(self, wave: list[Hashable], run_by: Literal["operator"]) -> list[Operator]: ...
@overload
def get_wave(self, wave: list[Hashable], run_by: Literal["instruction"]) -> list[Instruction]: ...
@overload
def get_wave(self, wave: Hashable, run_by: Optional[Literal["copy", "call"]]) -> QuantumCircuit: ...
@overload
def get_wave(self, wave: Hashable, run_by: Literal["gate"]) -> Gate: ...
@overload
def get_wave(self, wave: Hashable, run_by: Literal["operator"]) -> Operator: ...
@overload
def get_wave(self, wave: Hashable, run_by: Literal["instruction"]) -> Instruction: ...


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
    return actions.get(run_by, lambda w: w.copy())(self[wave])


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


def wave_container_maker(
    typename: str = "WaveContainer",
    base_type: Type[MutableMapping[Hashable, QuantumCircuit]] = dict,
) -> Type[MutableMapping]:
    """A customized dictionary for storing waves.

    Args:
        typename (str, optional): The name of the new type. Defaults to "WaveContainer".
        base_type (Type[MutableMapping[Hashable, QuantumCircuit]], optional):
            The base type of the new type. Defaults to dict.

    Returns:
        Type[MutableMapping]: The new type of wave container.
    """

    if not isinstance(typename, str):
        raise TypeError("`typename` should be a string.")

    if not isinstance(base_type, type):
        raise TypeError("`base_type` should be a type.")

    if not isinstance(base_type(), MutableMapping):
        raise TypeError(
            "`base_type` should be a dict-like structure or a MutableMapping basically."
        )

    def constructor(self, *args, **kwargs):
        super(base_type, self).__init__(*args, **kwargs)

    def __call__(
        self, wave: Union[list[Hashable], Hashable]
    ) -> Union[list[QuantumCircuit], QuantumCircuit]:
        return self.call(wave=wave)

    def __repr__(self):
        return f"{type(self).__name__}({super(self).__repr__()})"

    def _repr_oneline(self):
        return f"{self.__name__}(" + "{...}" + f", num={len(self)})"

    def _repr_pretty_(self, p, cycle):
        if cycle:
            p.text(f"{type(self).__name__}(" + "{...}" + f", num={len(self)})")
        else:
            original_repr = super(self).__repr__()
            original_repr_split = original_repr[1:-1].split(", ")
            length = len(original_repr_split)
            with p.group(2, f"{type(self).__name__}(" + "{", "})"):
                for i, item in enumerate(original_repr_split):
                    p.breakable()
                    p.text(item)
                    if i < length - 1:
                        p.text(",")

    def __str__(self):
        return super(self).__repr__()

    class_namespace = {
        "__init__": constructor,
        "__call__": __call__,
        "add": add,
        "remove": remove,
        "get_wave": get_wave,
        "call": call,
        "operator": operator,
        "gate": gate,
        "copy_circuit": copy_circuit,
        "instruction": instruction,
        "has": has,
        "process": process,
        "__repr__": __repr__,
        "_repr_oneline": _repr_oneline,
        "_repr_pretty_": _repr_pretty_,
        "__str__": __str__,
    }

    result = type(typename, (base_type,), class_namespace)

    return result


DyanmicWaveContainerByDict = wave_container_maker("WaveContainer", dict)
"""
A Qurry standard wave function container 
should be something dict-like structure, 
basically a typing.MutableMapping.
"""


def _add(
    _wave_container: MutableMapping[Hashable, QuantumCircuit],
    wave: QuantumCircuit,
    key: Optional[Hashable] = None,
    replace: Literal[True, False, "duplicate"] = False,
) -> Hashable:
    """Add new wave function to measure.

    Args:
        _wave_container (WaveContainer): The container of waves.
        wave (QuantumCircuit): The wave function or circuit to add.
        key (Optional[Hashable], optional):
            Given a specific key to add to the wave function or circuit,
            if `key == None`, then generate a number as key.
            Defaults to `None`.
        replace (Literal[True, False, &#39;duplicate&#39;], optional):
            If the key is already in the wave function or circuit,
            then replace the old wave function or circuit when `True`,
            or duplicate the wave function or circuit when `'duplicate'`,
            otherwise only changes `.lastwave`.
            Defaults to `False`.

    Returns:
        Optional[Hashable]: Key of given wave function in `.waves`.
    """

    if not isinstance(wave, QuantumCircuit):
        raise TypeError(f"waveCircuit should be a QuantumCircuit, not {type(wave)}")
    if isinstance(key, int):
        raise ValueError("Number key is only for internal use, not for user.")

    if key is None:
        key = len(_wave_container)
        _wave_container[key] = wave

    elif isinstance(key, Hashable):
        if key in _wave_container:
            if replace is True:
                pass
            elif replace == "duplicate":
                if isinstance(key, tuple):
                    key += (len(_wave_container),)
                else:
                    key = f"{key}.{len(_wave_container)}"
            else:
                key = len(_wave_container)
        _wave_container[key] = wave

    else:
        key = len(_wave_container)
        warnings.warn(f"'{key}' is '{type(key)}', a unhashable key, skipped being add.")

    return key


def _remove(
    _wave_container: MutableMapping[Hashable, QuantumCircuit],
    key: Optional[Hashable] = None,
) -> None:
    del _wave_container[key]


def _process(
    _wave_container: MutableMapping[Hashable, QuantumCircuit],
    circuits: list[Union[QuantumCircuit, Hashable]],
) -> list[tuple[Hashable, QuantumCircuit]]:
    """Process the circuits for Qurrium.

    Args:
        _wave_container (WaveContainer): The container of waves.
        circuits (list[Union[QuantumCircuit, Hashable]]): The circuits.

    Raises:
        KeyError: If the wave not found in the container.
        ValueError: If the circuit is invalid.

    Returns:
        dict[Hashable, QuantumCircuit]: The circuits maps.
    """
    circuits_items: list[tuple[Hashable, QuantumCircuit]] = []
    for _circuit in circuits:
        if isinstance(_circuit, QuantumCircuit):
            key = _add(_wave_container, wave=_circuit)
            circuits_items.append((key, _wave_container[key]))
        elif isinstance(_circuit, Hashable):
            if _circuit in _wave_container:
                circuits_items.append((_circuit, _wave_container[_circuit]))
            else:
                raise KeyError(f"Wave {_circuit} not found in {_wave_container}")
        else:
            raise ValueError(f"Invalid type of circuit: {_circuit}, type: {type(_circuit)}")

    if len(circuits_items) != len(circuits):
        raise ValueError(f"Lost some circuits: {[k for k, _ in circuits_items]}, {circuits}")
    return circuits_items
