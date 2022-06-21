from qiskit import (
    IBMQ, Aer, execute,
    QuantumRegister, ClassicalRegister, QuantumCircuit,
)
import pytest

from qurry.case import trivialParamagnet
from qurry.qurstrop import StringOperator

backend = {
    'aer': Aer.get_backend('aer_simulator'),
}

expDemo01 = StringOperator()
wave_adds = [
    (expDemo01.addWave(trivialParamagnet(i).wave(), i),) for i in range(6, 12, 2)
]

@pytest.mark.parametrize("tgt, ", wave_adds)
def test_quantity(
    tgt,
) -> bool:
    
    quantity = expDemo01.measure(wave=tgt[0], backend=backend['aer'])
    assert 'order' in quantity