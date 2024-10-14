"""
================================================================
Experiment Utilities
(:mod:`qurry.qurrium.experiment.utils`)
================================================================

"""

import warnings
from uuid import uuid4, UUID
from typing import Optional, Any

from ..analysis import AnalysisPrototype
from ...tools.datetime import current_time, DatetimeDict
from ...exceptions import QurryHashIDInvalid


EXPERIMENT_UNEXPORTS = ["side_product", "result", "circuits"]
"""Unexports properties."""
DEPRECATED_PROPERTIES = ["figTranspiled", "fig_original"]
"""Deprecated properties.
    - `figTranspiled` is deprecated since v0.6.0.
    - `fig_original` is deprecated since v0.6.10.
"""


def exp_id_process(exp_id: Optional[str]) -> str:
    """Check the exp_id is valid or not, if not, then generate a new one.

    Args:
        exp_id (Optional[str]): The id of the experiment to be checked.

    Returns:
        str: The valid exp_id.
    """

    if exp_id is None:
        return str(uuid4())

    try:
        UUID(exp_id, version=4)
    except ValueError as e:
        exp_id = None
        warnings.warn(
            f"exp_id is not a valid UUID, it will be generated automatically.\n{e}",
            category=QurryHashIDInvalid,
        )
    else:
        return exp_id
    return str(uuid4())


def commons_dealing(
    commons_dict: dict[str, Any],
    analysis_container: type[AnalysisPrototype],
) -> dict[str, Any]:
    """Dealing some special commons arguments.

    Args:
        commons_dict (dict[str, Any]): The common parameters of the experiment.
        analysis_container (AnalysisPrototype): The analysis container of the experiment.

    Returns:
        dict[str, Any]: The dealt common parameters of the experiment.
    """
    if "datetimes" not in commons_dict:
        commons_dict["datetimes"] = DatetimeDict({"bulid": current_time()})
    else:
        commons_dict["datetimes"] = DatetimeDict(commons_dict["datetimes"])
    if "default_analysis" in commons_dict:
        filted_analysis = []
        for raw_input_analysis in commons_dict["default_analysis"]:
            if isinstance(raw_input_analysis, dict):
                filted_analysis.append(
                    analysis_container.input_filter(**raw_input_analysis)[0]._asdict()
                )
            elif isinstance(raw_input_analysis, analysis_container.AnalysisInput):
                filted_analysis.append(raw_input_analysis._asdict())
            else:
                warnings.warn(
                    f"Analysis input {raw_input_analysis} is not a 'dict' or "
                    "'.analysis_container.AnalysisInput', it will be ignored."
                )
        commons_dict["default_analysis"] = filted_analysis
    else:
        commons_dict["default_analysis"] = []
    if "tags" in commons_dict:
        if isinstance(commons_dict["tags"], list):
            commons_dict["tags"] = tuple(commons_dict["tags"])

    return commons_dict
