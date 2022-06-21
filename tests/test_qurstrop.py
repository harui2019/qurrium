from qiskit import (
    IBMQ, Aer, execute,
    QuantumRegister, ClassicalRegister, QuantumCircuit,
)
import pytest

from ..qurry.case import trivialParamagnet
from ..qurry import MagnetSquare

backend = {
    'qasm': Aer.get_backend('qasm_simulator'),
    'state': Aer.get_backend('statevector_simulator'),
    'aer': Aer.get_backend('aer_simulator'),
}

expDemo01 = MagnetSquare()
wave_adds = [
    (expDemo01.addWave(trivialParamagnet(2).wave(i)),) for i in range(0, 10, 2)
]

@pytest.mark.parametrize("tgt", wave_adds)
def test_quantity(
    tgt: int,
) -> bool:
    
    quantity = expDemo01.measure(tgt)
    assert 'magnetsq' in quantity