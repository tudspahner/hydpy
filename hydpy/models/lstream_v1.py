# -*- coding: utf-8 -*-
"""

The following figure shows the general structure of L-Stream Version 1:

.. image:: HydPy-L-Stream_Version-1.png


Integration test:

    >>> from hydpy.models.lstream_v1 import *
    >>> parameterstep('1d')
    >>> simulationstep('12h')

    Secondly, the final model output shall be passed to `outflow`:

    >>> from hydpy.cythons import pointerutils
    >>> inflow, outflow = pointerutils.Double(0.), pointerutils.Double(0.)
    >>> inlets.q.shape = 1
    >>> inlets.q.setpointer(inflow, 0)
    >>> outlets.q.setpointer(outflow)

    Define the geometry and roughness values for the first test channel:

    >>> bm(2.)
    >>> bnm(4.)
    >>> hm(1.)
    >>> bv(.5, 10.)
    >>> bbv(1., 2.)
    >>> bnv(1., 8.)
    >>> bnvr(20.)
    >>> ekm(1.)
    >>> skm(20.)
    >>> ekv(1.)
    >>> skv(60., 80.)
    >>> gef(.01)
    >>> laen(10.)

    Set the error tolerances of the iteration small enough, not to
    compromise the shown first six decimal places of the following results:

    >>> qtol(1e-10)
    >>> htol(1e-10)

    >>> parameters.update()

    >>> states.qz.old = 1.
    >>> states.qz.new = 1.
    >>> states.qa.old = 1.

    >>> inflow[0] = 2.
    >>> outflow[0] = 0.
    >>> model.doit(0)
    >>> print(round(outflow[0], 6))
    1.737971
    >>> inflow[0] = 2000.
    >>> outflow[0] = 0.
    >>> model.doit(1)
    >>> print(round(outflow[0], 6))
    1932.529863
"""
# import...
# ...from standard library
from __future__ import division, print_function
# ...from HydPy
from hydpy.core.modelimports import *
from hydpy.core import modeltools
from hydpy.core import parametertools
from hydpy.core import sequencetools
# ...from lstream
from hydpy.models.lstream import lstream_model
from hydpy.models.lstream import lstream_control
from hydpy.models.lstream import lstream_derived
from hydpy.models.lstream import lstream_fluxes
from hydpy.models.lstream import lstream_states
from hydpy.models.lstream import lstream_aides
from hydpy.models.lstream import lstream_inlets
from hydpy.models.lstream import lstream_outlets


class Model(modeltools.Model):
    """LARSIM-Stream (Manning) version of HydPy-L-Stream (lstream_v1)."""
    _INLET_METHODS = (lstream_model.pick_q_v1,)
    _RUN_METHODS = (lstream_model.calc_qref_v1,
                    lstream_model.calc_hmin_qmin_hmax_qmax_v1,
                    lstream_model.calc_h_v1,
                    lstream_model.calc_ag_v1,
                    lstream_model.calc_rk_v1,
                    lstream_model.calc_qa_v1)
    _ADD_METHODS = (lstream_model.calc_am_um_v1,
                    lstream_model.calc_qm_v1,
                    lstream_model.calc_av_uv_v1,
                    lstream_model.calc_qv_v1,
                    lstream_model.calc_avr_uvr_v1,
                    lstream_model.calc_qvr_v1,
                    lstream_model.calc_qg_v1)
    _OUTLET_METHODS = (lstream_model.pass_q_v1,)


class ControlParameters(parametertools.SubParameters):
    """Control parameters of lstream_v1, directly defined by the user."""
    _PARCLASSES = (lstream_control.Laen,
                   lstream_control.Gef,
                   lstream_control.HM,
                   lstream_control.BM,
                   lstream_control.BV,
                   lstream_control.BBV,
                   lstream_control.BNM,
                   lstream_control.BNV,
                   lstream_control.BNVR,
                   lstream_control.SKM,
                   lstream_control.SKV,
                   lstream_control.EKM,
                   lstream_control.EKV,
                   lstream_control.QTol,
                   lstream_control.HTol)


class DerivedParameters(parametertools.SubParameters):
    """Derived parameters of lstream_v1, indirectly defined by the user.
    """
    _PARCLASSES = (lstream_derived.HV,
                   lstream_derived.QM,
                   lstream_derived.QV,
                   lstream_derived.Sek)


class FluxSequences(sequencetools.FluxSequences):
    """Flux sequences of LARSIM-ME."""
    _SEQCLASSES = (lstream_fluxes.QRef,
                   lstream_fluxes.H,
                   lstream_fluxes.AM,
                   lstream_fluxes.AV,
                   lstream_fluxes.AVR,
                   lstream_fluxes.AG,
                   lstream_fluxes.UM,
                   lstream_fluxes.UV,
                   lstream_fluxes.UVR,
                   lstream_fluxes.UG,
                   lstream_fluxes.QM,
                   lstream_fluxes.QV,
                   lstream_fluxes.QVR,
                   lstream_fluxes.QG,
                   lstream_fluxes.RK)


class StateSequences(sequencetools.StateSequences):
    """State sequences of lstream_v1."""
    _SEQCLASSES = (lstream_states.QZ,
                   lstream_states.QA)


class AideSequences(sequencetools.AideSequences):
    """Aide sequences of lstream_v1."""
    _SEQCLASSES = (lstream_aides.Temp,
                   lstream_aides.HMin,
                   lstream_aides.HMax,
                   lstream_aides.QMin,
                   lstream_aides.QMax,
                   lstream_aides.QTest)


class InletSequences(sequencetools.LinkSequences):
    """Upstream link sequences of lstream_v1."""
    _SEQCLASSES = (lstream_inlets.Q,)


class OutletSequences(sequencetools.LinkSequences):
    """Downstream link sequences of lstream_v1."""
    _SEQCLASSES = (lstream_outlets.Q,)


tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
