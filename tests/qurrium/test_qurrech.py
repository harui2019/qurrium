"""
================================================================
Test the qurry.qurrech module EchoListen class.
================================================================

- hadamard test
    - [4-trivial] 0.0 <= 0.75. 1.0 ~= 1.0.
    - [4-GHZ] 0.001953125 <= 0.75. 0.498046875 ~= 0.5.
    - [4-topological-period] 0.013671875 <= 0.75. 0.263671875 ~= 0.25.
    - [6-trivial] 0.0 <= 0.75. 1.0 ~= 1.0.
    - [6-GHZ] 0.001953125 <= 0.75. 0.498046875 ~= 0.5.
    - [6-topological-period] 0.046875 <= 0.75. 0.203125 ~= 0.25.

- randomized measurement
    - [4-trivial] 0.074896651506424 <= 0.75. 1.074896651506424 ~= 1.0.
    - [4-GHZ] 0.37087540805339814 <= 0.75. 0.12912459194660186 ~= 0.5.
    - [4-topological-period] 0.4087753367424011 <= 0.75. 0.6587753367424011 ~= 0.25.
    - [6-trivial] 0.12673971593379973 <= 0.75. 1.1267397159337997 ~= 1.0.
    - [6-GHZ] 0.465666207075119 <= 0.75. 0.03433379292488098 ~= 0.5.
    - [6-topological-period] 0.5656288474798202 <= 0.75. 0.8156288474798202 ~= 0.25.

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

SEED_SIMULATOR = 135331738096
SEED_RANDOM_UNITARY = 34
THREDHOLD = 0.75
MANUAL_ASSERT_ERROR = True

exp_method_01 = EchoListen(method="hadamard")
exp_method_02 = EchoListen(method="randomized")

wave_adds_01 = []
wave_adds_02 = []
answer = {}

for i in range(4, 7, 2):
    wave_adds_01.append(exp_method_01.add(TrivialParamagnet(i), f"{i}-trivial"))
    wave_adds_02.append(exp_method_02.add(TrivialParamagnet(i), f"{i}-trivial"))
    answer[f"{i}-trivial"] = 1.0
    # purity = 1.0

    wave_adds_01.append(exp_method_01.add(GHZ(i), f"{i}-GHZ"))
    wave_adds_02.append(exp_method_02.add(GHZ(i), f"{i}-GHZ"))
    answer[f"{i}-GHZ"] = 0.5
    # purity = 0.5

    wave_adds_01.append(
        exp_method_01.add(TopologicalParamagnet(i, "period"), f"{i}-topological-period")
    )
    wave_adds_02.append(
        exp_method_02.add(TopologicalParamagnet(i, "period"), f"{i}-topological-period")
    )
    answer[f"{i}-topological-period"] = 0.25
    # purity = 0.25

backend = GeneralSimulator()
# backend = BasicAer.backends()[0]
print(backend.configuration())  # type: ignore
backend.set_options(seed_simulator=SEED_SIMULATOR)  # type: ignore


@pytest.mark.parametrize("tgt", wave_adds_01)
def test_quantity_01(tgt):
    """Test the quantity of echo.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    exp_id = exp_method_01.measure(tgt, tgt, (0, 2), backend=backend)
    exp_method_01.exps[exp_id].analyze()
    quantity = exp_method_01.exps[exp_id].reports[0].content._asdict()
    assert all(
        ["echo" in quantity]
    ), f"The necessary quantities 'echo' are not found: {quantity.keys()}."
    assert (not MANUAL_ASSERT_ERROR) and np.abs(quantity["echo"] - answer[tgt]) < THREDHOLD, (
        "The hadamard test result is wrong: "
        + f"{np.abs(quantity['echo'] - answer[tgt])} !< {THREDHOLD}."
        + f" {quantity['echo']} != {answer[tgt]}."
    )


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
    answer_list = [answer[k] for k in wave_adds_01]

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
            for qqi, quantity in enumerate(quantities):
                assert isinstance(quantity, dict), f"The quantity is not a dict: {quantity}."
                assert all(
                    ["echo" in quantity]
                ), f"The necessary quantities 'echo' are not found: {quantity.keys()}-{qk}-{rk}."
                assert np.abs(quantity["echo"] - answer_list[qqi]) < THREDHOLD, (
                    "The hadamard test result is wrong: "
                    + f"{np.abs(quantity['echo'] - answer_list[qqi])} !< {THREDHOLD}."
                    + f" {quantity['echo']} != {answer_list[qqi]}."
                )

    read_summoner_id = exp_method_01.multiRead(
        summoner_name=exp_method_01.multimanagers[summoner_id].summoner_name,
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )

    assert (
        read_summoner_id == summoner_id
    ), f"The read summoner id is wrong: {read_summoner_id} != {summoner_id}."


@pytest.mark.parametrize("tgt", wave_adds_02)
def test_quantity_02(tgt):
    """Test the quantity of echo.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    exp_id = exp_method_02.measure(
        tgt, tgt, random_unitary_seed=SEED_SIMULATOR, shots=4096, backend=backend
    )
    exp_method_02.exps[exp_id].analyze((0, exp_method_02.waves[tgt].num_qubits - 1))
    quantity = exp_method_02.exps[exp_id].reports[0].content._asdict()
    assert all(
        ["echo" in quantity]
    ), f"The necessary quantities 'echo' are not found: {quantity.keys()}."
    assert (not MANUAL_ASSERT_ERROR) and np.abs(quantity["echo"] - answer[tgt]) < THREDHOLD, (
        "The randomized measurement result is wrong: "
        + f"{np.abs(quantity['echo'] - answer[tgt])} !< {THREDHOLD}."
        + f" {quantity['echo']} != {answer[tgt]}."
    )


def test_multi_output_02():
    """Test the multi-output of echo.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    config_list = [
        {"wave1": k, "wave2": k, "random_unitary_seed": SEED_SIMULATOR} for k in wave_adds_02
    ]
    answer_list = [answer[k] for k in wave_adds_01]

    summoner_id = exp_method_02.multiOutput(
        config_list,
        shots=4096,
        backend=backend,
        summoner_name="qurrech_randomized",
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )
    summoner_id = exp_method_02.multiAnalysis(summoner_id, degree=(0, 2))
    quantity_container = exp_method_02.multimanagers[summoner_id].quantity_container
    for rk, report in quantity_container.items():
        for qk, quantities in report.items():
            for qqi, quantity in enumerate(quantities):
                assert isinstance(quantity, dict), f"The quantity is not a dict: {quantity}."
                assert all(
                    ["echo" in quantity]
                ), f"The necessary quantities 'echo' are not found: {quantity.keys()}-{qk}-{rk}."
                assert np.abs(quantity["echo"] - answer_list[qqi]) < THREDHOLD, (
                    "The randomized measurement result is wrong: "
                    + f"{np.abs(quantity['echo'] - answer_list[qqi])} !< {THREDHOLD}."
                    + f" {quantity['echo']} != {answer_list[qqi]}."
                )

    read_summoner_id = exp_method_02.multiRead(
        summoner_name=exp_method_02.multimanagers[summoner_id].summoner_name,
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )

    assert (
        read_summoner_id == summoner_id
    ), f"The read summoner id is wrong: {read_summoner_id} != {summoner_id}."
