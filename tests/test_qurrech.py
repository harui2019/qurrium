"""
================================================================
Test the qurry.qurrech module EchoListen class.
================================================================

"""
import warnings
import pytest
from qiskit import QuantumRegister, QuantumCircuit

from qurry.qurrech import EchoListen
from qurry.tools import backendWrapper
from qurry.capsule import mori, hoshi

tag_list = mori.TagList()
hoshi = hoshi.Hoshi()

expDemo01 = EchoListen(method='hadamard')
expDemo02 = EchoListen(method='randomized')

try:
    from qurry.recipe.library import TrivialParamagnet

    wave_adds_01 = [
        (expDemo01.add(TrivialParamagnet(i).wave(), i),) for i in range(6, 12, 2)
    ]
    wave_adds_02 = [
        (expDemo02.add(TrivialParamagnet(i).wave(), i),) for i in range(6, 12, 2)
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
    wave_adds_01 = [
        (expDemo01.add(trivial_paramagnet(i), i),) for i in range(6, 12, 2)
    ]
    wave_adds_02 = [
        (expDemo02.add(trivial_paramagnet(i), i),) for i in range(6, 12, 2)
    ]


backend = backendWrapper()('aer')


@pytest.mark.parametrize("tgt, ", wave_adds_01)
def test_quantity_01(
    tgt,
) -> bool:
    """Test the quantity of entropy and purity.
    
    Args:
        tgt (tuple[QuantumCircuit, int]): The target wave and the number of qubits.
        
    Returns:
        bool: The result of the test.
    """

    exp_id = expDemo01.measure(
        tgt[0], tgt[0],
        backend=backend
    )
    expDemo01.exps[exp_id].analyze()
    quantity = expDemo01.exps[exp_id].reports[0].content._asdict()
    assert all(['echo' in quantity])


@pytest.mark.parametrize("tgt, ", wave_adds_02)
def test_quantity_02(
    tgt,
) -> bool:
    """Test the quantity of entropy and purity.

    Args:
        tgt (tuple[QuantumCircuit, int]): The target wave and the number of qubits.

    Returns:
        bool: The result of the test.
    """

    exp_id = expDemo02.measure(
        tgt[0], tgt[0],
        times=10,
        backend=backend
    )
    expDemo02.exps[exp_id].analyze(2)
    quantity = expDemo02.exps[exp_id].reports[0].content._asdict()
    assert all(['echo' in quantity])
