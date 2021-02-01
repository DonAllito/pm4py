import sys
from enum import Enum
from typing import Optional, Dict, Any

import pandas as pd

from pm4py.objects.dfg.retrieval.pandas import get_partial_order_dataframe
from pm4py.util import exec_utils, constants, xes_constants
from pm4py.util import typing


class Parameters(Enum):
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    START_TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_START_TIMESTAMP_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY
    ZETA = "zeta"


def apply(df: pd.DataFrame, temporal_profile: typing.TemporalProfile,
          parameters: Optional[Dict[Any, Any]] = None) -> typing.TemporalProfileConformanceResults:
    """
    Checks the conformance of the dataframe using the provided temporal profile.

    Implements the approach described in:
    Stertz, Florian, Jürgen Mangler, and Stefanie Rinderle-Ma. "Temporal Conformance Checking at Runtime based on Time-infused Process Models." arXiv preprint arXiv:2008.07262 (2020).


    Parameters
    ---------------
    df
        Pandas dataframe
    temporal_profile
        Temporal profile
    parameters
        Parameters of the algorithm, including:
         - Parameters.ACTIVITY_KEY => the attribute to use as activity
         - Parameters.START_TIMESTAMP_KEY => the attribute to use as start timestamp
         - Parameters.TIMESTAMP_KEY => the attribute to use as timestamp
         - Parameters.ZETA => multiplier for the standard deviation
         - Parameters.CASE_ID_KEY => column to use as case identifier

    Returns
    ---------------
    list_dev
        A list containing, for each case, all the deviations.
        Each deviation is a tuple with four elements:
        - 1) The source activity of the recorded deviation
        - 2) The target activity of the recorded deviation
        - 3) The time passed between the occurrence of the source activity and the target activity
        - 4) The value of (time passed - mean)/std for this occurrence (zeta).

    """
    if parameters is None:
        parameters = {}

    activity_key = exec_utils.get_param_value(Parameters.ACTIVITY_KEY, parameters, xes_constants.DEFAULT_NAME_KEY)
    timestamp_key = exec_utils.get_param_value(Parameters.TIMESTAMP_KEY, parameters,
                                               xes_constants.DEFAULT_TIMESTAMP_KEY)
    start_timestamp_key = exec_utils.get_param_value(Parameters.START_TIMESTAMP_KEY, parameters, None)
    case_id_key = exec_utils.get_param_value(Parameters.CASE_ID_KEY, parameters, constants.CASE_CONCEPT_NAME)
    zeta = exec_utils.get_param_value(Parameters.ZETA, parameters, 6.0)

    temporal_profile = pd.DataFrame([{activity_key: x[0], activity_key + "_2": x[1], "@@min": y[0] - zeta * y[1],
                                      "@@max": y[0] + zeta * y[1], "@@mean": y[0], "@@std": y[1]} for x, y in
                                     temporal_profile.items()])

    cases = list(df[case_id_key].unique())
    ret = [[] for c in cases]
    efg = get_partial_order_dataframe(df, activity_key=activity_key, timestamp_key=timestamp_key,
                                      start_timestamp_key=start_timestamp_key, case_id_glue=case_id_key,
                                      keep_first_following=False)
    efg = efg[[case_id_key, activity_key, activity_key + "_2", "@@flow_time"]]
    efg = efg.merge(temporal_profile, on=[activity_key, activity_key + "_2"])
    efg = efg[(efg["@@flow_time"] < efg["@@min"]) | (efg["@@flow_time"] > efg["@@max"])][
        [case_id_key, activity_key, activity_key + "_2", "@@flow_time", "@@mean", "@@std"]].to_dict("r")

    for el in efg:
        this_zeta = abs(el["@@flow_time"] - el["@@mean"]) / el["@@std"] if el["@@std"] > 0 else sys.maxsize
        ret[cases.index(el[case_id_key])].append(
            (el[activity_key], el[activity_key + "_2"], el["@@flow_time"], this_zeta))

    return ret