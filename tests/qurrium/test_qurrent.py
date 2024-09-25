"""
================================================================
Test the qurry.qurrent module EntropyMeasure class.
================================================================

- hadamard test
    - [4-trivial] 0.0 <= 0.5. 1.0 ~= 1.0.
    - [4-GHZ] 0.005859375 <= 0.5. 0.505859375 ~= 0.5.
    - [4-topological-period]  0.033203125 <= 0.5. 0.283203125 ~= 0.25.
    - [6-trivial] 0.0 <= 0.5. 1.0 ~= 1.0.
    - [6-GHZ] 0.005859375 <= 0.5. 0.505859375 ~= 0.5.
    - [6-topological-period] 0.041015625 <= 0.5. 0.291015625 ~= 0.25.

- randomized measurement
    - [4-trivial] 0.38355971932411204 <= 0.5. 1.383559719324112 ~= 1.0.
    - [4-GHZ] 0.4259319674968719 <= 0.5. 0.9259319674968719 ~= 0.5.
    - [4-topological-period] 0.0010692214965820068 <= 0.5. 0.251069221496582 ~= 0.25.
    - [6-trivial] 0.38355971932411204 <= 0.5. 1.383559719324112 ~= 1.0.
    - [6-GHZ] 0.4259319674968719 <= 0.5. 0.9259319674968719 ~= 0.5.
    - [6-topological-period] 0.0010692214965820068 <= 0.5. 0.251069221496582 ~= 0.25.

"""

import os
import pytest
import numpy as np

from qurry.qurrent import EntropyMeasure
from qurry.tools.backend import GeneralSimulator
from qurry.capsule import mori, hoshi
from qurry.recipe import TrivialParamagnet, GHZ, TopologicalParamagnet

tag_list = mori.TagList()
statesheet = hoshi.Hoshi()

SEED_SIMULATOR = 2019  # <harmony/>
SEED_RANDOM_UNITARY = 42
THREDHOLD = 0.5
MANUAL_ASSERT_ERROR = False

exp_method_01 = EntropyMeasure(method="hadamard")
exp_method_02 = EntropyMeasure(method="randomized")

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
    """Test the quantity of entropy and purity.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    exp_id = exp_method_01.measure(wave=tgt, degree=(0, 2), backend=backend)
    exp_method_01.exps[exp_id].analyze()
    quantity = exp_method_01.exps[exp_id].reports[0].content._asdict()
    assert all(
        ["entropy" in quantity, "purity" in quantity]
    ), f"The necessary quantities 'entropy', 'purity' are not found: {quantity.keys()}."
    assert (not MANUAL_ASSERT_ERROR) and np.abs(quantity["purity"] - answer[tgt]) < THREDHOLD, (
        "The hadamard test result is wrong: "
        + f"{np.abs(quantity['purity'] - answer[tgt])} !< {THREDHOLD}."
        + f" {quantity['purity']} != {answer[tgt]}."
    )


def test_multi_output_01():
    """Test the multi-output of purity and entropy.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    config_list = [
        {
            "wave": k,
            "degree": (0, 2),
        }
        for k in wave_adds_01
    ]
    answer_list = [answer[k] for k in wave_adds_01]

    summoner_id = exp_method_01.multiOutput(
        config_list,
        backend=backend,
        summoner_name="qurrent_hadamard",
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )
    summoner_id = exp_method_01.multiAnalysis(summoner_id)
    quantity_container = exp_method_01.multimanagers[summoner_id].quantity_container
    for rk, report in quantity_container.items():
        for qk, quantities in report.items():
            for qqi, quantity in enumerate(quantities):
                assert isinstance(quantity, dict), f"The quantity is not a dict: {quantity}."
                assert all(["entropy" in quantity, "purity" in quantity]), (
                    "The necessary quantities 'entropy', 'purity' "
                    + f"are not found: {quantity.keys()}-{qk}-{rk}."
                )
                assert np.abs(quantity["purity"] - answer_list[qqi]) < THREDHOLD, (
                    "The hadamard test result is wrong: "
                    + f"{np.abs(quantity['purity'] - answer_list[qqi])} !< {THREDHOLD}."
                    + f" {quantity['purity']} != {answer_list[qqi]}."
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
    """Test the quantity of entropy and purity.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    exp_id = exp_method_02.measure(
        wave=tgt, random_unitary_seed=SEED_RANDOM_UNITARY, shots=4096, backend=backend
    )
    analysis_01 = exp_method_02.exps[exp_id].analyze((0, 2))
    quantity_01 = analysis_01.content._asdict()
    analysis_02 = exp_method_02.exps[exp_id].analyze((0, 2), counts_used=range(5))
    quantity_02 = analysis_02.content._asdict()
    assert all(
        ["entropy" in quantity_01, "purity" in quantity_01]
    ), f"The necessary quantities 'entropy', 'purity' are not found: {quantity_01.keys()}."
    assert quantity_02["entropyAllSys"] != quantity_01["entropyAllSys"], (
        "The all system entropy is not changed: "
        + f"counts_used: {quantity_01['counts_used']}: {quantity_02['entropyAllSys']}, "
        + f"counts_used: {quantity_02['counts_used']}: {quantity_02['entropyAllSys']},"
    )
    assert (not MANUAL_ASSERT_ERROR) and np.abs(quantity_01["purity"] - answer[tgt]) < THREDHOLD, (
        "The randomized measurement result is wrong: "
        + f"{np.abs(quantity_01['purity'] - answer[tgt])} !< {THREDHOLD}."
        + f" {quantity_01['purity']} != {answer[tgt]}."
    )


def test_multi_output_02():
    """Test the multi-output of purity and entropy.

    Args:
        tgt (Hashable): The target wave key in Qurry.
    """

    config_list = [{"wave": k, "random_unitary_seed": SEED_RANDOM_UNITARY} for k in wave_adds_02]
    answer_list = [answer[k] for k in wave_adds_01]

    summoner_id = exp_method_02.multiOutput(
        config_list,
        shots=4096,
        backend=backend,
        summoner_name="qurrent_randomized",
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )
    summoner_id = exp_method_02.multiAnalysis(summoner_id, degree=(0, 2))
    quantity_container = exp_method_02.multimanagers[summoner_id].quantity_container
    for rk, report in quantity_container.items():
        for qk, quantities in report.items():
            for qqi, quantity in enumerate(quantities):
                assert isinstance(quantity, dict), f"The quantity is not a dict: {quantity}."
                assert all(["entropy" in quantity, "purity" in quantity]), (
                    "The necessary quantities 'entropy', 'purity' "
                    + f"are not found: {quantity.keys()}-{qk}-{rk}."
                )
                assert np.abs(quantity["purity"] - answer_list[qqi]) < THREDHOLD, (
                    "The randomized measurement result is wrong: "
                    + f"{np.abs(quantity['purity'] - answer_list[qqi])} !< {THREDHOLD}."
                    + f" {quantity['purity']} != {answer_list[qqi]}."
                )

    read_summoner_id = exp_method_02.multiRead(
        summoner_name=exp_method_02.multimanagers[summoner_id].summoner_name,
        save_location=os.path.join(os.path.dirname(__file__), "exports"),
    )

    assert (
        read_summoner_id == summoner_id
    ), f"The read summoner id is wrong: {read_summoner_id} != {summoner_id}."
