import pytest
import warnings
from qiskit import QuantumRegister, QuantumCircuit

from qurry.qurrent import EntropyMeasure
from qurry.tools import backendWrapper

import qurry.capsule.mori as mori
import qurry.capsule.hoshi as hoshi

expDemo01 = EntropyMeasure(method='hadamard')
try:
    from qurry.recipe.library import TrivialParamagnet

    wave_adds = [
        (expDemo01.add(TrivialParamagnet(i).wave(), i),) for i in range(6, 12, 2)
    ]
except:
    warnings.warn("TrivialParamagnet not found. Use the following instead.")
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
        (expDemo01.add(trivialParamagnet(i), i),) for i in range(6, 12, 2)
    ]


backend = backendWrapper()('aer')


@pytest.mark.parametrize("tgt, ", wave_adds)
def test_quantity(
    tgt,
) -> bool:
    
    ID = expDemo01.measure(wave=tgt[0], backend=backend)
    expDemo01.exps[ID].analyze()
    quantity = expDemo01.exps[ID].reports[0].content._asdict()
    assert all(['entropy' in quantity, 'purity' in quantity])