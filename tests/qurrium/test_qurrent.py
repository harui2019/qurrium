"""
================================================================
Test the qurry.qurrent module EntropyMeasure class.
================================================================

- hadamard test
    - [4-trivial] 0.0 <= 0.25. 1.0 ~= 1.0.
    - [4-GHZ] 0.005859375 <= 0.25. 0.505859375 ~= 0.5.
    - [4-topological-period] 0.033203125 <= 0.25. 0.283203125 ~= 0.25.
    - [6-trivial] 0.0 <= 0.25. 1.0 ~= 1.0.
    - [6-GHZ] 0.005859375 <= 0.25. 0.505859375 ~= 0.5.
    - [6-topological-period] 0.041015625 <= 0.25. 0.291015625 ~= 0.25.

- randomized measurement
    - [4-trivial] 0.10342769622802739 <= 0.25. 1.1034276962280274 ~= 1.0.
    - [4-GHZ] 0.14542131423950194 <= 0.25. 0.35457868576049806 ~= 0.5.
    - [4-topological-period] 0.003579425811767567 <= 0.25. 0.25357942581176757 ~= 0.25.
    - [6-trivial] 0.18802957534790044 <= 0.25. 0.8119704246520996 ~= 1.0.
    - [6-GHZ] 0.018079471588134777 <= 0.25. 0.4819205284118652 ~= 0.5.
    - [6-topological-period] 0.003579425811767567 <= 0.25. 0.25357942581176757 ~= 0.25.

"""

import os
import pytest
import numpy as np

from qurry.qurrent import EntropyMeasure
from qurry.tools.backend import GeneralSimulator
from qurry.capsule import mori, hoshi, quickRead
from qurry.recipe import TrivialParamagnet, GHZ, TopologicalParamagnet

tag_list = mori.TagList()
statesheet = hoshi.Hoshi()

FILE_LOCATION = os.path.join(os.path.dirname(__file__), "random_unitary_seeds.json")
SEED_SIMULATOR = 2019  # <harmony/>
THREDHOLD = 0.25
MANUAL_ASSERT_ERROR = False

exp_method_01 = EntropyMeasure(method="hadamard")
exp_method_02 = EntropyMeasure(method="randomized")

random_unitary_seeds_raw: dict[str, dict[str, dict[str, int]]] = quickRead(FILE_LOCATION)
random_unitary_seeds = {
    int(k): {int(k2): {int(k3): v3 for k3, v3 in v2.items()} for k2, v2 in v.items()}
    for k, v in random_unitary_seeds_raw.items()
}
seed_usage = {}
wave_adds_01 = []
wave_adds_02 = []
answer = {}

for i in range(4, 7, 2):
    wave_adds_01.append(exp_method_01.add(TrivialParamagnet(i), f"{i}-trivial"))
    wave_adds_02.append(exp_method_02.add(TrivialParamagnet(i), f"{i}-trivial"))
    answer[f"{i}-trivial"] = 1.0
    seed_usage[f"{i}-trivial"] = i
    # purity = 1.0

    wave_adds_01.append(exp_method_01.add(GHZ(i), f"{i}-GHZ"))
    wave_adds_02.append(exp_method_02.add(GHZ(i), f"{i}-GHZ"))
    answer[f"{i}-GHZ"] = 0.5
    seed_usage[f"{i}-GHZ"] = i
    # purity = 0.5

    wave_adds_01.append(
        exp_method_01.add(TopologicalParamagnet(i, "period"), f"{i}-topological-period")
    )
    wave_adds_02.append(
        exp_method_02.add(TopologicalParamagnet(i, "period"), f"{i}-topological-period")
    )
    answer[f"{i}-topological-period"] = 0.25
    seed_usage[f"{i}-topological-period"] = i
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

    exp_id = exp_method_01.measure(tgt, (0, 2), backend=backend)
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
        wave=tgt,
        times=20,
        random_unitary_seeds={i: random_unitary_seeds[seed_usage[tgt]][i] for i in range(20)},
        backend=backend,
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

    config_list = [
        {
            "wave": k,
            "times": 20,
            "random_unitary_seeds": {i: random_unitary_seeds[seed_usage[k]][i] for i in range(20)},
        }
        for k in wave_adds_02
    ]
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
