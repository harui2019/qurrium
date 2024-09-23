"""
================================================================
Test the qurry.qurrech module EchoListen class.
================================================================

"""

import os
import pytest
import numpy as np

from qurry.qurrech import EchoListen
from qurry.tools.backend import GeneralSimulator
from qurry.capsule import mori, hoshi
from qurry.recipe import TrivialParamagnet, GHZ, TopologicalParamagnet

tag_list = mori.TagList()
statesheet = hoshi.Hoshi()

exp_method_01 = EchoListen(method="hadamard")
exp_method_02 = EchoListen(method="randomized")

wave_adds_01 = []
wave_adds_02 = []

for i in range(4, 7, 2):
    wave_adds_01.append(exp_method_01.add(TrivialParamagnet(i), f"{i}-trivial"))
    wave_adds_02.append(exp_method_02.add(TrivialParamagnet(i), f"{i}-trivial"))

    wave_adds_01.append(exp_method_01.add(GHZ(i), f"{i}-GHZ"))
    wave_adds_02.append(exp_method_02.add(GHZ(i), f"{i}-GHZ"))

    wave_adds_01.append(exp_method_01.add(TopologicalParamagnet(i), f"{i}-topological"))
    wave_adds_02.append(exp_method_02.add(TopologicalParamagnet(i), f"{i}-topological"))

backend = GeneralSimulator()
# backend = BasicAer.backends()[0]
print(backend.configuration())  # type: ignore


@pytest.mark.parametrize("tgt", wave_adds_01)
def test_quantity_01(tgt):
    """Test the quantity of echo.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    exp_id = exp_method_01.measure(tgt, tgt, backend=backend)
    exp_method_01.exps[exp_id].analyze()
    quantity = exp_method_01.exps[exp_id].reports[0].content._asdict()
    assert all(
        ["echo" in quantity]
    ), f"The necessary quantities 'echo' are not found: {quantity.keys()}."
    assert (
        np.abs(quantity["echo"] - 1.0) < 1e-0
    ), f"The hadamard test result is wrong: {np.abs(quantity['purity'] - 1.0)} !<= < 1e-0."


@pytest.mark.parametrize("tgt", wave_adds_02)
def test_quantity_02(tgt):
    """Test the quantity of echo.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    exp_id = exp_method_02.measure(tgt, tgt, 10, backend=backend)
    exp_method_02.exps[exp_id].analyze((0, exp_method_02.waves[tgt].num_qubits - 1))
    quantity = exp_method_02.exps[exp_id].reports[0].content._asdict()
    assert all(
        ["echo" in quantity]
    ), f"The necessary quantities 'echo' are not found: {quantity.keys()}."


def test_multi_output_01():
    """Test the multi-output of echo.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    config_list = [
        {
            "wave1": k,
            "wave2": k,
            "degree": (0, 2),
        }
        for k in wave_adds_01
    ]
    summoner_id = exp_method_01.multiOutput(
        config_list,
        backend=backend,
        summoner_name="qurrech_hadamard",
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )
    summoner_id = exp_method_01.multiAnalysis(summoner_id)
    quantity_container = exp_method_01.multimanagers[summoner_id].quantity_container
    for rk, report in quantity_container.items():
        for qk, quantities in report.items():
            for quantity in quantities:
                assert isinstance(quantity, dict), f"The quantity is not a dict: {quantity}."
                assert all(
                    ["echo" in quantity]
                ), f"The necessary quantities 'echo' are not found: {quantity.keys()}-{qk}-{rk}."

    read_summoner_id = exp_method_01.multiRead(
        summoner_name=exp_method_01.multimanagers[summoner_id].summoner_name,
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

    config_list = [
        {
            "wave1": k,
            "wave2": k,
        }
        for k in wave_adds_02
    ]
    summoner_id = exp_method_02.multiOutput(
        config_list,
        backend=backend,
        summoner_name="qurrech_randomized",
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )
    summoner_id = exp_method_02.multiAnalysis(summoner_id, degree=(0, 2))
    quantity_container = exp_method_02.multimanagers[summoner_id].quantity_container
    for rk, report in quantity_container.items():
        for qk, quantities in report.items():
            for quantity in quantities:
                assert isinstance(quantity, dict), f"The quantity is not a dict: {quantity}."
                assert all(
                    ["echo" in quantity]
                ), f"The necessary quantities 'echo' are not found: {quantity.keys()}-{qk}-{rk}."

    read_summoner_id = exp_method_02.multiRead(
        summoner_name=exp_method_02.multimanagers[summoner_id].summoner_name,
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )

    assert (
        read_summoner_id == summoner_id
    ), f"The read summoner id is wrong: {read_summoner_id} != {summoner_id}."
