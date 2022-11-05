from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
import pytest
from qurry.qurrent import EntropyMeasure
from qurry.util import backendWrapper

expDemo01 = EntropyMeasure()
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


backend = backendWrapper()


@pytest.mark.parametrize("tgt, ", wave_adds)
def test_quantity(
    tgt,
) -> bool:
    
    quantity = expDemo01.measure(wave=tgt[0], backend=backend('aer'))
    assert all('entropy' in quantity, 'purity' in quantity)