from copy import copy
from enum import Enum

import matplotlib

from pm4py.util import exec_utils
from pm4py.visualization.graphs.util import common


class Parameters(Enum):
    TITLE = "title"
    FORMAT = "format"
    X_AXIS = "x_axis"
    Y_AXIS = "y_axis"


def apply_plot(x, y, parameters=None):
    """
    Visualizes a barchar provided its x-axis and y-axis points

    Parameters
    -----------------
    x
        X-axis points
    y
        Y-axis points
    parameters
        Parameters

    Returns
    -----------------
    tmp_file_name
        Temporary file name
    """
    if parameters is None:
        parameters = {}

    title = exec_utils.get_param_value(Parameters.TITLE, parameters, "")
    format = exec_utils.get_param_value(Parameters.FORMAT, parameters, "png")
    x_axis = exec_utils.get_param_value(Parameters.X_AXIS, parameters, "")
    y_axis = exec_utils.get_param_value(Parameters.Y_AXIS, parameters, "")

    filename = common.get_temp_file_name(format)

    current_backend = copy(matplotlib.get_backend())
    matplotlib.use('Agg')
    from matplotlib import pyplot

    pyplot.clf()
    fig = pyplot.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    ax.bar(x, y)
    pyplot.xlabel(x_axis)
    pyplot.ylabel(y_axis)
    pyplot.title(title)
    pyplot.savefig(filename, bbox_inches="tight", transparent=True)
    pyplot.clf()

    matplotlib.use(current_backend)

    return filename