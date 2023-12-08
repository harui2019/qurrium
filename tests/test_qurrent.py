"""
================================================================
Test the qurry.qurrent module EntropyMeasure class.
================================================================

"""
import pytest

from qurry.qurrent import EntropyMeasure
from qurry.tools.backend import GeneralAerSimulator
from qurry.capsule import mori, hoshi
from qurry.recipe.library import TrivialParamagnet, GHZ, TopologicalParamagnet

tag_list = mori.TagList()
statesheet = hoshi.Hoshi()

expDemo01 = EntropyMeasure(method="hadamard")
expDemo02 = EntropyMeasure(method="randomized")


wave_adds_01 = []
wave_adds_02 = []

for i in range(4, 7, 2):
    wave_adds_01.append(expDemo01.add(TrivialParamagnet(i).wave(), f"{i}-trivial"))
    wave_adds_02.append(expDemo02.add(TrivialParamagnet(i).wave(), f"{i}-trivial"))

    wave_adds_01.append(expDemo01.add(GHZ(i).wave(), f"{i}-GHZ"))
    wave_adds_02.append(expDemo02.add(GHZ(i).wave(), f"{i}-GHZ"))

    wave_adds_01.append(
        expDemo01.add(TopologicalParamagnet(i).wave(), f"{i}-topological")
    )
    wave_adds_02.append(
        expDemo02.add(TopologicalParamagnet(i).wave(), f"{i}-topological")
    )

backend = GeneralAerSimulator()
# backend = BasicAer.backends()[0]
print(backend.configuration())


@pytest.mark.parametrize("tgt", wave_adds_01)
def test_quantity_01(tgt):
    """Test the quantity of entropy and purity.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    exp_id = expDemo01.measure(wave=tgt, backend=backend)
    expDemo01.exps[exp_id].analyze()
    quantity = expDemo01.exps[exp_id].reports[0].content._asdict()
    assert all(["entropy" in quantity, "purity" in quantity])


@pytest.mark.parametrize("tgt", wave_adds_02)
def test_quantity_02(tgt):
    """Test the quantity of entropy and purity.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    exp_id = expDemo02.measure(wave=tgt, times=10, backend=backend)
    expDemo02.exps[exp_id].analyze(2)
    quantity = expDemo02.exps[exp_id].reports[0].content._asdict()
    assert all(["entropy" in quantity, "purity" in quantity])
