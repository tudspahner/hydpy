# -*- coding: utf-8 -*-
"""
Integration examples:

    The following tests are performed over a period of 20 hours:

    >>> from hydpy import pub, Timegrid, Timegrids, Nodes, Element
    >>> pub.timegrids = Timegrids(Timegrid('01.01.2000 00:00',
    ...                                    '01.01.2000 20:00',
    ...                                    '1h'))

    Import the model and define the time settings:

    >>> from hydpy.models.arma_v1 import *
    >>> parameterstep('1h')

    For testing purposes, the model input shall be retrieved from the nodes
    `input1` and `input2` and the model output shall be passed to node
    `output`.  Firstly, define all nodes:

    >>> nodes = Nodes('input1', 'input2', 'output')

    Define the element "stream" and build the connections between
    the nodes defined above and the `arma_v1` model instance:

    >>> stream = Element('stream',
    ...                  inlets=['input1', 'input2'],
    ...                  outlets='output')
    >>> stream.connect(model)

    Prepare a test function object, which prints the respective values of
    the model sequences `qin`, `qpin`, `qpout`, and `qout`.  The node sequence
    `sim` is added in order to prove that the values calculated for `qout` are
    actually passed to `sim`:

    >>> from hydpy.core.testtools import IntegrationTest
    >>> test = IntegrationTest(stream,
    ...                        seqs=(fluxes.qin, fluxes.qpin, fluxes.qpout,
    ...                              fluxes.qout, nodes.output.sequences.sim))

    To start the respective example runs from stationary conditions, a
    base flow value of 2m³/s is set for all values of the log sequences
    `login` and `logout`:

    >>> test.inits = ((logs.login, 2.),
    ...               (logs.logout, 2.))

    Print just the time instead of the whole date:
    >>> test.dateformat = '%H:%M'

    Define two flood events, one for each lake inflow:

    >>> nodes.input1.sequences.sim.series = (
    ...                         1., 1., 2., 4., 3., 2., 1., 1., 1., 1.,
    ...                         1., 1., 1., 1., 1., 1., 1., 1., 1., 1.)
    >>> nodes.input2.sequences.sim.series = (
    ...                         1., 2., 6., 9., 8., 6., 4., 3., 2., 1.,
    ...                         1., 1., 1., 1., 1., 1., 1., 1., 1., 1.)

    In the first example, a pure fourth order moving avarage (MA) process is
    defined:

    >>> responses(((), (0.2, 0.4, 0.3, 0.1)))

    This leads to a usual "unit hydrograph" convolution result, where all
    inflow "impulses" are seperated onto the actual and the three subsequent
    time steps:

    >>> test()
    |  date |  qin | qpin | qpout | qout | output |
    -----------------------------------------------
    | 00:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 01:00 |  3.0 |  3.0 |   2.2 |  2.2 |    2.2 |
    | 02:00 |  8.0 |  8.0 |   3.6 |  3.6 |    3.6 |
    | 03:00 | 13.0 | 13.0 |   6.9 |  6.9 |    6.9 |
    | 04:00 | 11.0 | 11.0 |  10.1 | 10.1 |   10.1 |
    | 05:00 |  8.0 |  8.0 |  10.7 | 10.7 |   10.7 |
    | 06:00 |  5.0 |  5.0 |   8.8 |  8.8 |    8.8 |
    | 07:00 |  4.0 |  4.0 |   6.3 |  6.3 |    6.3 |
    | 08:00 |  3.0 |  3.0 |   4.5 |  4.5 |    4.5 |
    | 09:00 |  2.0 |  2.0 |   3.3 |  3.3 |    3.3 |
    | 10:00 |  2.0 |  2.0 |   2.5 |  2.5 |    2.5 |
    | 11:00 |  2.0 |  2.0 |   2.1 |  2.1 |    2.1 |
    | 12:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 13:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 14:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 15:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 16:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 17:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 18:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |
    | 19:00 |  2.0 |  2.0 |   2.0 |  2.0 |    2.0 |

    In the second example, the mimimum order the MA process is defined,
    which is one.  The autoregression (AR) process is of order two.  Note
    that negative AR coefficients are allowed (also note the opposite signs
    of the coefficients contrast to the statistical literature):

    >>> responses(((1.1, -0.3), (0.2,)))

    Due to the AR process, the maximum time delay of some fractions of each
    input impulse is theoretically infinite:

    >>> test()
    |  date |  qin | qpin |    qpout |     qout |   output |
    --------------------------------------------------------
    | 00:00 |  2.0 |  2.0 |      2.0 |      2.0 |      2.0 |
    | 01:00 |  3.0 |  3.0 |      2.2 |      2.2 |      2.2 |
    | 02:00 |  8.0 |  8.0 |     3.42 |     3.42 |     3.42 |
    | 03:00 | 13.0 | 13.0 |    5.702 |    5.702 |    5.702 |
    | 04:00 | 11.0 | 11.0 |   7.4462 |   7.4462 |   7.4462 |
    | 05:00 |  8.0 |  8.0 |  8.08022 |  8.08022 |  8.08022 |
    | 06:00 |  5.0 |  5.0 | 7.654382 | 7.654382 | 7.654382 |
    | 07:00 |  4.0 |  4.0 | 6.795754 | 6.795754 | 6.795754 |
    | 08:00 |  3.0 |  3.0 | 5.779015 | 5.779015 | 5.779015 |
    | 09:00 |  2.0 |  2.0 |  4.71819 |  4.71819 |  4.71819 |
    | 10:00 |  2.0 |  2.0 | 3.856305 | 3.856305 | 3.856305 |
    | 11:00 |  2.0 |  2.0 | 3.226478 | 3.226478 | 3.226478 |
    | 12:00 |  2.0 |  2.0 | 2.792235 | 2.792235 | 2.792235 |
    | 13:00 |  2.0 |  2.0 | 2.503515 | 2.503515 | 2.503515 |
    | 14:00 |  2.0 |  2.0 | 2.316196 | 2.316196 | 2.316196 |
    | 15:00 |  2.0 |  2.0 | 2.196761 | 2.196761 | 2.196761 |
    | 16:00 |  2.0 |  2.0 | 2.121578 | 2.121578 | 2.121578 |
    | 17:00 |  2.0 |  2.0 | 2.074708 | 2.074708 | 2.074708 |
    | 18:00 |  2.0 |  2.0 | 2.045705 | 2.045705 | 2.045705 |
    | 19:00 |  2.0 |  2.0 | 2.027863 | 2.027863 | 2.027863 |

    The third example equalts the second one, except in additional time
    delay of exactly one hour, due to the changed MA process:

    >>> responses(((1.1, -0.3), (0.0, 0.2)))

    >>> test()
    |  date |  qin | qpin |    qpout |     qout |   output |
    --------------------------------------------------------
    | 00:00 |  2.0 |  2.0 |      2.0 |      2.0 |      2.0 |
    | 01:00 |  3.0 |  3.0 |      2.0 |      2.0 |      2.0 |
    | 02:00 |  8.0 |  8.0 |      2.2 |      2.2 |      2.2 |
    | 03:00 | 13.0 | 13.0 |     3.42 |     3.42 |     3.42 |
    | 04:00 | 11.0 | 11.0 |    5.702 |    5.702 |    5.702 |
    | 05:00 |  8.0 |  8.0 |   7.4462 |   7.4462 |   7.4462 |
    | 06:00 |  5.0 |  5.0 |  8.08022 |  8.08022 |  8.08022 |
    | 07:00 |  4.0 |  4.0 | 7.654382 | 7.654382 | 7.654382 |
    | 08:00 |  3.0 |  3.0 | 6.795754 | 6.795754 | 6.795754 |
    | 09:00 |  2.0 |  2.0 | 5.779015 | 5.779015 | 5.779015 |
    | 10:00 |  2.0 |  2.0 |  4.71819 |  4.71819 |  4.71819 |
    | 11:00 |  2.0 |  2.0 | 3.856305 | 3.856305 | 3.856305 |
    | 12:00 |  2.0 |  2.0 | 3.226478 | 3.226478 | 3.226478 |
    | 13:00 |  2.0 |  2.0 | 2.792235 | 2.792235 | 2.792235 |
    | 14:00 |  2.0 |  2.0 | 2.503515 | 2.503515 | 2.503515 |
    | 15:00 |  2.0 |  2.0 | 2.316196 | 2.316196 | 2.316196 |
    | 16:00 |  2.0 |  2.0 | 2.196761 | 2.196761 | 2.196761 |
    | 17:00 |  2.0 |  2.0 | 2.121578 | 2.121578 | 2.121578 |
    | 18:00 |  2.0 |  2.0 | 2.074708 | 2.074708 | 2.074708 |
    | 19:00 |  2.0 |  2.0 | 2.045705 | 2.045705 | 2.045705 |


    >>> responses(((1.5, -0.7), (0.0, 0.2)))
    >>> test()
    |  date |  qin | qpin |     qpout |      qout |    output |
    -----------------------------------------------------------
    | 00:00 |  2.0 |  2.0 |       2.0 |       2.0 |       2.0 |
    | 01:00 |  3.0 |  3.0 |       2.0 |       2.0 |       2.0 |
    | 02:00 |  8.0 |  8.0 |       2.2 |       2.2 |       2.2 |
    | 03:00 | 13.0 | 13.0 |       3.5 |       3.5 |       3.5 |
    | 04:00 | 11.0 | 11.0 |      6.31 |      6.31 |      6.31 |
    | 05:00 |  8.0 |  8.0 |     9.215 |     9.215 |     9.215 |
    | 06:00 |  5.0 |  5.0 |   11.0055 |   11.0055 |   11.0055 |
    | 07:00 |  4.0 |  4.0 |  11.05775 |  11.05775 |  11.05775 |
    | 08:00 |  3.0 |  3.0 |  9.682775 |  9.682775 |  9.682775 |
    | 09:00 |  2.0 |  2.0 |  7.383738 |  7.383738 |  7.383738 |
    | 10:00 |  2.0 |  2.0 |  4.697664 |  4.697664 |  4.697664 |
    | 11:00 |  2.0 |  2.0 |  2.277879 |  2.277879 |  2.277879 |
    | 12:00 |  2.0 |  2.0 |  0.528454 |  0.528454 |  0.528454 |
    | 13:00 |  2.0 |  2.0 | -0.401834 | -0.401834 | -0.401834 |
    | 14:00 |  2.0 |  2.0 | -0.572669 | -0.572669 | -0.572669 |
    | 15:00 |  2.0 |  2.0 |  -0.17772 |  -0.17772 |  -0.17772 |
    | 16:00 |  2.0 |  2.0 |  0.534289 |  0.534289 |  0.534289 |
    | 17:00 |  2.0 |  2.0 |  1.325837 |  1.325837 |  1.325837 |
    | 18:00 |  2.0 |  2.0 |  2.014753 |  2.014753 |  2.014753 |
    | 19:00 |  2.0 |  2.0 |  2.494044 |  2.494044 |  2.494044 |

    The plausiblity of the coefficients is not checked.  Be aware that
    the water balance is only met, if the sum of all equation is one.  But
    even then problems like negative discharge values might occur, if the
    coefficients are not set carefully, is shown in the fourth example:

    In the fifth example, the coefficients of the first two examples are
    combined.  For inflow discharges between 0 and 7m³/s, the pure AR
    process is applied.  For inflow discharges exceeding 7m³/s, inflow
    is seperated.  The AR process is still applied on a portion of 7m³/s,
    but for the inflow exceeding the threshold the mixed ARMA model is
    applied:

    >>> responses(_0=((), (0.2, 0.4, 0.3, 0.1)),
    ...           _7=((1.1, -0.3), (0.2,)))

    To again start from stationary conditions, one has to apply different
    values to both log sequences.  The base flow value of 2m³/s is only
    given to the (low flow) MA model, the (high flow) ARMA is initialized
    with zero values instead:

    >>> test.inits.login = [[2.0], [0.0]]
    >>> test.inits.logout = [[2.0], [0.0]]

    The seperate handling of the inflow can be studied by inspecting the
    columns of sequence `qpin` and sequence `qpout`.  The respective left
    columns show the input and output of the MA model, the respective right
    colums show the input and output of the ARMA model:

    >>> test()
    |  date |  qin |      qpin |         qpout |     qout |   output |
    ------------------------------------------------------------------
    | 00:00 |  2.0 | 2.0   0.0 | 2.0       0.0 |      2.0 |      2.0 |
    | 01:00 |  3.0 | 3.0   0.0 | 2.2       0.0 |      2.2 |      2.2 |
    | 02:00 |  8.0 | 7.0   1.0 | 3.4       0.2 |      3.6 |      3.6 |
    | 03:00 | 13.0 | 7.0   6.0 | 5.3      1.42 |     6.72 |     6.72 |
    | 04:00 | 11.0 | 7.0   4.0 | 6.6     2.302 |    8.902 |    8.902 |
    | 05:00 |  8.0 | 7.0   1.0 | 7.0    2.3062 |   9.3062 |   9.3062 |
    | 06:00 |  5.0 | 5.0   0.0 | 6.6   1.84622 |  8.44622 |  8.44622 |
    | 07:00 |  4.0 | 4.0   0.0 | 5.6  1.338982 | 6.938982 | 6.938982 |
    | 08:00 |  3.0 | 3.0   0.0 | 4.4  0.919014 | 5.319014 | 5.319014 |
    | 09:00 |  2.0 | 2.0   0.0 | 3.3  0.609221 | 3.909221 | 3.909221 |
    | 10:00 |  2.0 | 2.0   0.0 | 2.5  0.394439 | 2.894439 | 2.894439 |
    | 11:00 |  2.0 | 2.0   0.0 | 2.1  0.251116 | 2.351116 | 2.351116 |
    | 12:00 |  2.0 | 2.0   0.0 | 2.0  0.157896 | 2.157896 | 2.157896 |
    | 13:00 |  2.0 | 2.0   0.0 | 2.0  0.098351 | 2.098351 | 2.098351 |
    | 14:00 |  2.0 | 2.0   0.0 | 2.0  0.060817 | 2.060817 | 2.060817 |
    | 15:00 |  2.0 | 2.0   0.0 | 2.0  0.037394 | 2.037394 | 2.037394 |
    | 16:00 |  2.0 | 2.0   0.0 | 2.0  0.022888 | 2.022888 | 2.022888 |
    | 17:00 |  2.0 | 2.0   0.0 | 2.0  0.013959 | 2.013959 | 2.013959 |
    | 18:00 |  2.0 | 2.0   0.0 | 2.0  0.008488 | 2.008488 | 2.008488 |
    | 19:00 |  2.0 | 2.0   0.0 | 2.0  0.005149 | 2.005149 | 2.005149 |
"""

# import...
# ...from standard library
from __future__ import division, print_function
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...from HydPy
from hydpy.core.modelimports import *
# ...from arma
from hydpy.models.arma import arma_model
from hydpy.models.arma import arma_control
from hydpy.models.arma import arma_derived
from hydpy.models.arma import arma_fluxes
from hydpy.models.arma import arma_logs
from hydpy.models.arma import arma_inlets
from hydpy.models.arma import arma_outlets


class Model(modeltools.Model):
    """Rimo/Rido version of ARMA (arma_v1)."""

    _INLET_METHODS = (arma_model.pick_q_v1,)
    _RUN_METHODS = (arma_model.calc_qpin_v1,
                    arma_model.calc_login_v1,
                    arma_model.calc_qma_v1,
                    arma_model.calc_qar_v1,
                    arma_model.calc_qpout_v1,
                    arma_model.calc_logout_v1,
                    arma_model.calc_qout_v1)
    _OUTLET_METHODS = (arma_model.pass_q_v1,)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of arma_v1, directly defined by the user."""
    _PARCLASSES = (arma_control.Responses,)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of arma_v1, indirectly defined by the user."""
    _PARCLASSES = (arma_derived.Nmb,
                   arma_derived.MaxQ,
                   arma_derived.DiffQ,
                   arma_derived.AR_Order,
                   arma_derived.MA_Order,
                   arma_derived.AR_Coefs,
                   arma_derived.MA_Coefs)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of arma_v1"""
    _SEQCLASSES = (arma_fluxes.QIn,
                   arma_fluxes.QPIn,
                   arma_fluxes.QMA,
                   arma_fluxes.QAR,
                   arma_fluxes.QPOut,
                   arma_fluxes.QOut)


class LogSequences(sequencetools.LogSequences):
    """Log sequences of arma_v1."""
    _SEQCLASSES = (arma_logs.LogIn,
                   arma_logs.LogOut)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of arma_v1."""
    _SEQCLASSES = (arma_inlets.Q,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of arma_v1."""
    _SEQCLASSES = (arma_outlets.Q,)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()