import warnings
from typing import Union, NamedTuple, Literal, Optional, overload
from abc import abstractmethod

from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit.quantum_info import Operator
from qiskit.circuit.gate import Gate
from qiskit.circuit.instruction import Instruction

from ..tools.backend import AerProvider, AerSimulator


AER_BACKEND: AerSimulator = AerProvider().get_backend('aer_simulator')


class Qurecipe:
    """The abstract class to define a case.
        Position for `qurry.recipe`
        See https://github.com/harui2019/qurry/issues/82
    """

    # params
    @abstractmethod
    class arguments(NamedTuple):
        """The parameters of the case."""

    class arguments(NamedTuple):
        num_qubits: int = 1
        name: str = ''

    _required_fields = ['num_qubits', 'name']

    # circuit
    @abstractmethod
    def method(self) -> list[QuantumCircuit]:
        """Construct the example circuit."""
        ...

    def method(self):
        """Construct the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """
        q = QuantumRegister(self.params.num_qubits, "q")
        qc = QuantumCircuit(q, name=self.name)

        return [qc]

    @abstractmethod
    def __init__(self, num_qubits: int, name: str, *args, **kwargs) -> None:
        """Initializing the case.
        """
        ...

    def __init__(
        self,
        num_qubits: int,
        name: str = f"_dummy",
    ) -> None:
        """Initializing the case.

        Args:
            numQubits (int): The number of qubits for constructing the example circuit.
        """

        self.case_name = '_dummy'
        self._initialize(
            name=name,
            num_qubits=num_qubits,
        )

    def _initialize(self, name: str, *args, **kwargs) -> None:
        """Initializing the case.
        """
        if hasattr(self, 'params'):
            return
        for k in self._required_fields:
            if not k in self.arguments._fields:
                raise AttributeError(
                    f"the field '{k}' is required in the params of {self.__class__}"
                )
        self.params: Qurecipe.arguments = (
            self.arguments(**{**kwargs, 'name': name}))
        self.name = self.params.name
        self.circuits = self.method()
        assert isinstance(self.circuits, list), "return type is not list"

    def __repr__(self):
        return f"Qurecipe({self.params.__repr__()})"

    _ATTR_NAME = {
        'operator': '_operator',
        'gate': '_gate',
        'instruction': '_instruction',
        'copy': '_wave'
    }

    @overload
    def _wave_return(
        self,
        type_as: Literal['gate', 'operator', 'instruction', 'copy'],
        _c: QuantumCircuit,
        _i: int,
        remake: bool = False,
    ) -> Union[Gate, Operator, Instruction, QuantumCircuit]:
        ...

    @overload
    def _wave_return(
        self,
        type_as: Literal['gate', 'operator', 'instruction', 'copy'],
        _c: Optional[QuantumCircuit] = None,
        _i: Optional[int] = None,
        remake: bool = False,
    ) -> Union[list[Gate], list[Operator], list[Instruction], list[QuantumCircuit]]:
        ...

    # wave return

    def _wave_return(
        self,
        type_as: Literal['gate', 'operator', 'instruction', 'copy'] = 'copy',
        _c: Optional[QuantumCircuit] = None,
        _i: Optional[int] = None,
        remake: bool = False,
    ):
        """Return the example circuit as `Gate`, `Operator`, `Instruction`, or a copy of the example circuit.

        Args:
            type_as (Literal[&#39;gate&#39;, &#39;operator&#39;, &#39;instruction&#39;, &#39;copy&#39;], optional): 
                Export instruction as something, `None` for 'gate'. Defaults to `'gate'`.
            _c (Optional[QuantumCircuit], optional): Inner circuit for recursion. Defaults to None.
            _i (Optional[int], optional): Inner index for recursion. Defaults to None.
            remake (bool, optional): Regenerate instruction. Defaults to False.

        Returns:
            Union[
                list[Union[Gate, Operator, Instruction, QuantumCircuit]], 
                Union[Gate, Operator, Instruction, QuantumCircuit]
            ]: Instrunction.
        """

        if _i is None:
            if not remake and hasattr(self, self._ATTR_NAME[type_as]):
                return self.__getattribute__(self._ATTR_NAME[type_as])

        to_attr = self._ATTR_NAME[type_as] if type_as in self._ATTR_NAME else '_wave'
        _return = None
        if _c is None:
            _c: list[QuantumCircuit] = self.circuits

        if isinstance(_c, list):
            _return = [
                self._wave_return(type_as=type_as, _c=w, _i=i, remake=remake)
                for i, w in enumerate(_c)]

        elif type_as == 'operator' and isinstance(_c, QuantumCircuit):
            _c = transpile(_c, backend=AER_BACKEND)
            _return = Operator(_c)

        elif type_as == 'gate' and isinstance(_c, QuantumCircuit):
            _c = transpile(_c, backend=AER_BACKEND)
            _return = _c.to_gate(label=_c.name)

        elif type_as == 'instruction' and isinstance(_c, QuantumCircuit):
            _c = transpile(_c, backend=AER_BACKEND)
            _return = _c.to_instruction(label=_c.name)

        elif type_as == 'copy' and isinstance(_c, QuantumCircuit):
            _return = _c.copy(name=_c.name)

        else:
            raise TypeError(f"Invalid type_as: {type_as}")

        if _i is None:
            self.__setattr__(to_attr, _return)

        return _return

    def _wave_caller(
        self,
        index: Optional[Union[int, Literal['all']]] = None,
        type_as: Literal['gate', 'operator', 'instruction', 'copy'] = 'copy',
        remake: bool = False,
    ) -> Union[
        Gate, Operator, Instruction, QuantumCircuit,
        list[Gate], list[Operator], list[Instruction], list[QuantumCircuit]
    ]:
        _w: Union[
            Gate, Operator, Instruction, QuantumCircuit,
            list[Gate], list[Operator], list[Instruction], list[QuantumCircuit]
        ] = self._wave_return(
            type_as=type_as, remake=remake)
        assert isinstance(_w, list), "return type is not list"

        if index == 'all':
            return _w

        if len(_w) == 1:
            if not index is None:
                warnings.warn("There is only one circuit in this case.")
            return _w[0]
        else:
            if index is None:
                raise IndexError(
                    "There are more than one circuit in this case.")
            else:
                return _w[index]

    def gate(
        self,
        index: Optional[int] = None,
        remake: bool = False,
    ) -> Gate:
        """Return the example circuit as `Gate`.

        Returns:
            Gate: The example circuit.
        """
        return self._wave_caller(
            index=index, type_as='gate', remake=remake)

    def gates(
        self,
        remake: bool = False,
    ) -> list[Gate]:
        return self._wave_caller(
            index='all', type_as='gate', remake=remake)

    def operator(
        self,
        index: Optional[int] = None,
        remake: bool = False,
    ) -> Operator:
        """Return the example circuit as `Operator`.

        Returns:
            Operator: The example circuit.
        """
        return self._wave_caller(
            index=index, type_as='operator', remake=remake)

    def operators(
        self,
        remake: bool = False,
    ) -> list[Operator]:
        return self._wave_caller(
            index='all', type_as='operator', remake=remake)

    def wave(
        self,
        index: Optional[int] = None,
        remake: bool = False,
    ) -> QuantumCircuit:
        """Return a copy of the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """
        return self._wave_caller(
            index=index, type_as='copy', remake=remake)

    def waves(
        self,
        remake: bool = False,
    ) -> list[QuantumCircuit]:
        return self._wave_caller(
            index='all', type_as='copy', remake=remake)

    def instruction(
        self,
        index: Optional[int] = None,
        remake: bool = False,
    ) -> Instruction:
        """Return the example circuit as `Instruction`.

        Returns:
            Instruction: The example circuit.
        """
        return self._wave_caller(
            index=index, type_as='instruction', remake=remake)

    def instructions(
        self,
        remake: bool = False,
    ) -> list[Instruction]:
        return self._wave_caller(
            index='all', type_as='instruction', remake=remake)


class TrotterBlock(Qurecipe):
    """The specific class to define a Trotter block.
    """


class SSH(Qurecipe):
    """The specific class to define SSH circuits.
    """
    trotter_block: dict[float, TrotterBlock] = {}
    """The dictionary of trotter block."""
    combined: dict[float, dict[float, int]] = {}
    """The total number of used trotter blocks."""
