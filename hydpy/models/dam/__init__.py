# -*- coding: utf-8 -*-
"""
ToDo
"""
# import...
# ...from standard library
from __future__ import division, print_function
# ...from HydPy
from hydpy.core.modelimports import *
# ...from dam
from hydpy.models.dam.dam_control import ControlParameters
from hydpy.models.dam.dam_derived import DerivedParameters
from hydpy.models.dam.dam_solver import SolverParameters
from hydpy.models.dam.dam_fluxes import FluxSequences
from hydpy.models.dam.dam_states import StateSequences
from hydpy.models.dam.dam_logs import LogSequences
from hydpy.models.dam.dam_receivers import ReceiverSequences
from hydpy.models.dam.dam_inlets import InletSequences
from hydpy.models.dam.dam_outlets import OutletSequences
from hydpy.models.dam.dam_aides import AideSequences
from hydpy.models.dam.dam_model import Model

autodoc_basemodel()
tester = Tester()
cythonizer = Cythonizer()
cythonizer.complete()
