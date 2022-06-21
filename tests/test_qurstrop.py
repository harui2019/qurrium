from qiskit import (
    IBMQ, Aer, execute,
    QuantumRegister, ClassicalRegister, QuantumCircuit,
)
import pytest

import sys, os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')
import qurry

# from qurry.case import trivialParamagnet
from qurry.qurstrop import StringOperator

backend = {
    'aer': Aer.get_backend('aer_simulator'),
}

def trivialParamagnet(n) -> QuantumCircuit:
    """Construct the example circuit.

    Returns:
        QuantumCircuit: The example circuit.
    """
    q = QuantumRegister(n, "q")
    qc = QuantumCircuit(q)
    [qc.h(q[i]) for i in range(n)]
    
    return qc

expDemo01 = StringOperator()
wave_adds = [
    # (expDemo01.addWave(trivialParamagnet(i).wave(), i),) for i in range(6, 12, 2)
    (expDemo01.addWave(trivialParamagnet(i), i),) for i in range(6, 12, 2)
]

@pytest.mark.parametrize("tgt, ", wave_adds)
def test_quantity(
    tgt,
) -> bool:
    
    quantity = expDemo01.measure(wave=tgt[0], backend=backend['aer'])
    assert 'order' in quantity