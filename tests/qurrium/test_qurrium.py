"""
================================================================
Test the qurry.qurrent module EntropyMeasure class.
================================================================

"""

import os
import pytest

from qurry.qurrium import WavesExecuter, SamplingExecuter
from qurry.tools.backend import GeneralSimulator
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

backend = GeneralSimulator()
# backend = BasicAer.backends()[0]
print(backend.configuration())  # type: ignore


@pytest.mark.parametrize("tgt", wave_adds_01)
def test_quantity_01(tgt):
    """Test the quantity of entropy and purity.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    exp_id = exp_demo_01.measure(wave=tgt, sampling=10, backend=backend)
    exp_demo_01.exps[exp_id].analyze()
    quantity = exp_demo_01.exps[exp_id].reports[0].content._asdict()
    assert all(
        ["dummy" in quantity, "utlmatic_answer" in quantity]
    ), f"The necessary quantities 'dummy', 'utlmatic_answer' are not found: {quantity.keys()}."


@pytest.mark.parametrize("tgt", wave_adds_02)
def test_quantity_02(tgt):
    """Test the quantity of entropy and purity.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    exp_id = exp_demo_02.measure(waves=[tgt for _ in range(5)], backend=backend)
    exp_demo_02.exps[exp_id].analyze()
    quantity = exp_demo_02.exps[exp_id].reports[0].content._asdict()
    assert all(
        ["dummy" in quantity, "utlmatic_answer" in quantity]
    ), f"The necessary quantities 'dummy', 'utlmatic_answer' are not found: {quantity.keys()}."


def test_multi_output_01():
    """Test the multi-output of echo.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    config_list = [{"wave": k} for k in wave_adds_01[:3]]
    summoner_id = exp_demo_01.multiOutput(
        config_list,
        backend=backend,
        summoner_name="sampling_excuter",
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )
    summoner_id = exp_demo_01.multiAnalysis(summoner_id)
    quantity_container = exp_demo_01.multimanagers[summoner_id].quantity_container
    for rk, report in quantity_container.items():
        for qk, quantities in report.items():
            for quantity in quantities:
                assert isinstance(quantity, dict), f"The quantity is not a dict: {quantity}."
                assert all(["utlmatic_answer" in quantity]), (
                    "The necessary quantities 'dummy', 'utlmatic_answer' "
                    + f"are not found: {quantity.keys()}-{qk}-{rk}."
                )

    read_summoner_id = exp_demo_01.multiRead(
        summoner_name=exp_demo_01.multimanagers[summoner_id].summoner_name,
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )

    assert (
        read_summoner_id == summoner_id
    ), f"The read summoner id is wrong: {read_summoner_id} != {summoner_id}."


def test_multi_output_02():
    """Test the multi-output of echo.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    config_list = [{"waves": [k for _ in range(5)]} for k in wave_adds_02[:3]]
    summoner_id = exp_demo_02.multiOutput(
        config_list,
        backend=backend,
        summoner_name="waves_excuter",
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )
    summoner_id = exp_demo_02.multiAnalysis(summoner_id)
    quantity_container = exp_demo_02.multimanagers[summoner_id].quantity_container
    for rk, report in quantity_container.items():
        for qk, quantities in report.items():
            for quantity in quantities:
                assert isinstance(quantity, dict), f"The quantity is not a dict: {quantity}."
                assert all(["utlmatic_answer" in quantity]), (
                    "The necessary quantities 'dummy', 'utlmatic_answer' "
                    + f"are not found: {quantity.keys()}-{qk}-{rk}."
                )

    read_summoner_id = exp_demo_02.multiRead(
        summoner_name=exp_demo_02.multimanagers[summoner_id].summoner_name,
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )

    assert (
        read_summoner_id == summoner_id
    ), f"The read summoner id is wrong: {read_summoner_id} != {summoner_id}."
