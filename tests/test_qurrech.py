"""
================================================================
Test the qurry.qurrech module EchoListen class.
================================================================

"""
import pytest

from qurry.qurrech import EchoListen
from qurry.tools import backendWrapper
from qurry.capsule import mori, hoshi
from qurry.recipe.library import TrivialParamagnet

tag_list = mori.TagList()
hoshi = hoshi.Hoshi()

expDemo01 = EchoListen(method='hadamard')
expDemo02 = EchoListen(method='randomized')


wave_adds_01 = [
    (expDemo01.add(TrivialParamagnet(i).wave(), i),) for i in range(6, 12, 2)
]
wave_adds_02 = [
    (expDemo02.add(TrivialParamagnet(i).wave(), i),) for i in range(6, 12, 2)
]

backend = backendWrapper()('aer')


# @pytest.mark.parametrize("tgt, ", wave_adds_01)
# def test_quantity_01(
#     tgt,
# ) -> bool:
#     """Test the quantity of entropy and purity.

#     Args:
#         tgt (tuple[QuantumCircuit, int]): The target wave and the number of qubits.

#     Returns:
#         bool: The result of the test.
#     """

#     exp_id = expDemo01.measure(
#         tgt[0], tgt[0],
#         backend=backend
#     )
#     expDemo01.exps[exp_id].analyze()
#     quantity = expDemo01.exps[exp_id].reports[0].content._asdict()
#     assert all(['echo' in quantity])


# @pytest.mark.parametrize("tgt, ", wave_adds_02)
# def test_quantity_02(
#     tgt,
# ) -> bool:
#     """Test the quantity of entropy and purity.

#     Args:
#         tgt (tuple[QuantumCircuit, int]): The target wave and the number of qubits.

#     Returns:
#         bool: The result of the test.
#     """

#     exp_id = expDemo02.measure(
#         tgt[0], tgt[0],
#         times=10,
#         backend=backend
#     )
#     expDemo02.exps[exp_id].analyze(2)
#     quantity = expDemo02.exps[exp_id].reports[0].content._asdict()
#     assert all(['echo' in quantity])
