from qiskit import QuantumCircuit
from qiskit.providers import Backend
from qiskit.quantum_info import Operator
from qiskit.circuit import Gate, Instruction
from qiskit_aer import AerProvider

import warnings
from typing import Literal, Union, Optional, Hashable, MutableMapping, Type, TypeVar


def wave_container_maker(
    typename: str = 'WaveContainer',
    base_type: Type[MutableMapping[Hashable, QuantumCircuit]] = dict,
) -> Type[MutableMapping]:
    if not isinstance(typename, str):
        raise TypeError('`typename` should be a string.')

    if not isinstance(base_type, type):
        raise TypeError('`base_type` should be a type.')

    if not isinstance(base_type(), MutableMapping):
        raise TypeError(
            '`base_type` should be a dict-like structure or a MutableMapping basically.')

    @property
    def lastWave(self) -> Optional[QuantumCircuit]:
        """The last wave function be called or used..
        Replace the property :prop:`waveNow`. in :cls:`QurryV4`"""
        if self.lastWaveKey == None:
            return None
        else:
            return self[self.lastWaveKey]

    def constructor(self, *args, **kwargs):
        super(base_type, self).__init__(*args, **kwargs)
        self.lastWaveKey = None

    def add(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: QuantumCircuit,
        key: Optional[Hashable] = None,
        replace: Literal[True, False, 'duplicate'] = False,
    ) -> Hashable:

        self.lastWaveKey = _add(self, wave, key, replace)
        return self.lastWaveKey

    def remove(self, key: Hashable):
        return _remove(self, key)

    def get_wave(
        self: MutableMapping[Hashable, QuantumCircuit],
        wave: Union[list[Hashable], Hashable, None] = None,
        runBy: Optional[Literal['gate', 'operator',
                                'instruction', 'copy', 'call']] = None
    ) -> Union[list[Union[Gate, Operator, Instruction, QuantumCircuit]], Union[Gate, Operator, Instruction, QuantumCircuit]]:
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
            waveReturn: The result of the wave as `Gate` or `Operator`.
        """

        if wave == None:
            wave = self.lastWave
        elif isinstance(wave, list):
            return [self.get_wave(w, runBy) for w in wave]

        if wave not in self:
            raise KeyError(f"Wave {wave} not found in {self}")

        if runBy == 'operator':
            return Operator(self[wave])
        elif runBy == 'gate':
            return self[wave].to_gate()
        elif runBy == 'instruction':
            return self[wave].to_instruction()
        elif runBy == 'copy':
            return self[wave].copy()
        elif runBy == 'call':
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
            runBy='call',
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
            runBy='operator',
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
            runBy='gate',
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
            runBy='copy',
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
            runBy='instruction',
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

    def __repr__(self: MutableMapping[Hashable, QuantumCircuit]):
        inner_lines = '\n'.join('    %s: ...' % k for k in self.keys())
        inner_lines2 = "{\n%s\n}" % inner_lines
        return f"<{typename}={inner_lines2} with {len(self)} waves load, a customized dictionary>"

    class_namespace = {
        '__init__': constructor,
        '__call__': __call__,

        'lastWave': lastWave,
        'add': add,
        'remove': remove,
        'get_wave': get_wave,
        'call': call,
        'operator': operator,
        'gate': gate,
        'copy_circuit': copy_circuit,
        'instruction': instruction,
        'has': has,

        '__repr__': __repr__,
    }

    result = type(typename, (base_type,), class_namespace)

    return result


DyanmicWaveContainerByDict = wave_container_maker('WaveContainer', dict)
"""A Qurry standard wave function container should be something dict-like structure, basically a typing.MutableMapping."""


def _add(
    _wave_container: MutableMapping[Hashable, QuantumCircuit],
    wave: QuantumCircuit,
    key: Optional[Hashable] = None,
    replace: Literal[True, False, 'duplicate'] = False,
) -> Hashable:
    """Add new wave function to measure.

    Args:
        waveCircuit (QuantumCircuit): The wave functions or circuits want to measure.
        key (Optional[Hashable], optional): Given a specific key to add to the wave function or circuit,
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

    if key is None:
        key = len(_wave_container)
        _wave_container[key] = wave

    elif isinstance(key, Hashable):
        if key in _wave_container:
            if replace == True:
                pass
            elif replace == 'duplicate':
                if isinstance(key, tuple):
                    key += (len(_wave_container), )
                else:
                    key = f"{key}.{len(_wave_container)}"
            else:
                key = len(_wave_container)
        _wave_container[key] = wave

    else:
        key = len(_wave_container)
        warnings.warn(
            f"'{key}' is '{type(key)}', a unhashable key, skipped being add.")

    return key


def _remove(
    _wave_container: MutableMapping[Hashable, QuantumCircuit],
    key: Optional[Hashable] = None,
) -> None:

    del _wave_container[key]
