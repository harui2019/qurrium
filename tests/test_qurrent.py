"""
================================================================
Test the qurry.qurrent module.
================================================================

"""
import warnings
import pytest
from qiskit import QuantumRegister, QuantumCircuit

from qurry.qurrent import EntropyMeasure
from qurry.tools import backendWrapper
from qurry.capsule import mori, hoshi

tag_list = mori.TagList()
hoshi = hoshi.Hoshi()

expDemo01 = EntropyMeasure(method='hadamard')
try:
    from qurry.recipe.library import TrivialParamagnet

    wave_adds = [
        (expDemo01.add(TrivialParamagnet(i).wave(), i),) for i in range(6, 12, 2)
    ]
except ImportError:
    warnings.warn("TrivialParamagnet not found. Use the following instead.")
    def trivial_paramagnet(n) -> QuantumCircuit:
        """Construct the example circuit.

        Returns:
            QuantumCircuit: The example circuit.
        """
        q = QuantumRegister(n, "q")
        qc = QuantumCircuit(q)
        for i in range(n):
            qc.h(q[i])

        return qc
    wave_adds = [
        (expDemo01.add(trivial_paramagnet(i), i),) for i in range(6, 12, 2)
    ]


backend = backendWrapper()('aer')


@pytest.mark.parametrize("tgt, ", wave_adds)
def test_quantity(
    tgt,
) -> bool:
    """Test the quantity of entropy and purity.
    
    Args:
        tgt (tuple[QuantumCircuit, int]): The target wave and the number of qubits.
        
    Returns:
        bool: The result of the test.
    """

    exp_id = expDemo01.measure(wave=tgt[0], backend=backend)
    expDemo01.exps[exp_id].analyze()
    quantity = expDemo01.exps[exp_id].reports[0].content._asdict()
    assert all(['entropy' in quantity, 'purity' in quantity])
