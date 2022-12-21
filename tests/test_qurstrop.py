import pytest
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit

from qurry.qurstrop import StringOperator
from qurry.tools import backendWrapper

expDemo01 = StringOperator()
try:
    from qurry.case import trivialParamagnet

    wave_adds = [
        (expDemo01.addWave(trivialParamagnet(i).wave(), i),) for i in range(6, 12, 2)
    ]
except:
    def trivialParamagnet(n) -> QuantumCircuit:
        """Construct the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """
        q = QuantumRegister(n, "q")
        qc = QuantumCircuit(q)
        [qc.h(q[i]) for i in range(n)]
    
        return qc
    wave_adds = [
        (expDemo01.addWave(trivialParamagnet(i), i),) for i in range(6, 12, 2)
    ]


backend = backendWrapper()('aer')

@pytest.mark.parametrize("tgt, ", wave_adds)
def test_quantity(
    tgt,
) -> bool:
    
    quantity = expDemo01.measure(wave=tgt[0], backend=backend)
    assert 'order' in quantity