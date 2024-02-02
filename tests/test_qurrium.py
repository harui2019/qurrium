"""
================================================================
Test the qurry.qurrent module EntropyMeasure class.
================================================================

"""

import pytest
from qurry.qurrium import WavesExecuter, SamplingExecuter
from qurry.tools.backend import GeneralAerSimulator
from qurry.capsule import mori, hoshi
from qurry.recipe import TrivialParamagnet, GHZ, TopologicalParamagnet

tag_list = mori.TagList()
statesheet = hoshi.Hoshi()

exp_demo_01 = SamplingExecuter()
exp_demo_02 = WavesExecuter()

wave_adds_01 = []
wave_adds_02 = []

for i in range(4, 7, 2):
    wave_adds_01.append(exp_demo_01.add(TrivialParamagnet(i), f"{i}-trivial"))
    wave_adds_02.append(exp_demo_02.add(TrivialParamagnet(i), f"{i}-trivial"))

    wave_adds_01.append(exp_demo_01.add(GHZ(i), f"{i}-GHZ"))
    wave_adds_02.append(exp_demo_02.add(GHZ(i), f"{i}-GHZ"))

    wave_adds_01.append(exp_demo_01.add(TopologicalParamagnet(i), f"{i}-topological"))
    wave_adds_02.append(exp_demo_02.add(TopologicalParamagnet(i), f"{i}-topological"))

backend = GeneralAerSimulator()
# backend = BasicAer.backends()[0]
print(backend.configuration())


@pytest.mark.parametrize("tgt", wave_adds_01)
def test_quantity_01(tgt):
    """Test the quantity of entropy and purity.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    exp_id = exp_demo_01.measure(wave=tgt, sampling=10, backend=backend)
    exp_demo_01.exps[exp_id].analyze()
    quantity = exp_demo_01.exps[exp_id].reports[0].content._asdict()
    assert all(["dummy" in quantity, "utlmatic_answer" in quantity])


@pytest.mark.parametrize("tgt", wave_adds_02)
def test_quantity_02(tgt):
    """Test the quantity of entropy and purity.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    exp_id = exp_demo_02.measure(waves=[tgt for _ in range(10)], backend=backend)
    exp_demo_02.exps[exp_id].analyze()
    quantity = exp_demo_02.exps[exp_id].reports[0].content._asdict()
    assert all(["dummy" in quantity, "utlmatic_answer" in quantity])
