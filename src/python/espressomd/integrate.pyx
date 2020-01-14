#
# Copyright (C) 2013-2019 The ESPResSo project
#
# This file is part of ESPResSo.
#
# ESPResSo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ESPResSo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from cpython.exc cimport PyErr_CheckSignals, PyErr_SetInterrupt
include "myconfig.pxi"
import espressomd.code_info
from espressomd.utils cimport *
cimport globals

cdef class Integrator:
    """
    Integrator class.

    This class interfaces the Velocity Verlet integrator.

    """

    cdef str _method
    cdef object _steepest_descent_params
    cdef object _isotropic_npt_params

    def __init__(self):
        self._method = "VV"
        self._steepest_descent_params = {}
        self._isotropic_npt_params = {}

    # __getstate__ and __setstate__ define the pickle interaction
    def __getstate__(self):
        state = {}
        state['_method'] = self._method
        state['_steepest_descent_params'] = self._steepest_descent_params
        state['_isotropic_npt_params'] = self._isotropic_npt_params
        return state

    def __setstate__(self, state):
        self.__init__()
        self._method = state['_method']
        if self._method == "STEEPEST_DESCENT":
            self.set_steepest_descent(**state['_steepest_descent_params'])
        elif self._method == "NVT":
            self.set_nvt()
        elif self._method == "SD":
            self.set_sd()
        elif self._method == "NPT":
            self.set_isotropic_npt(**state['_isotropic_npt_params'])

    def get_state(self):
        """Returns the integrator status."""
        return self.__getstate__()

    def run(self, steps=1, recalc_forces=False, reuse_forces=False):
        """
        Run the integrator.

        Parameters
        ----------
        steps : :obj:`int`
            Number of time steps to integrate.
        recalc_forces : :obj:`bool`, optional
            Recalculate the forces regardless of whether they are reusable.
        reuse_forces : :obj:`bool`, optional
            Reuse the forces from previous time step.

        """
        if self._method == "VV" or self._method == "NVT" or self._method == "NPT" or self._method == "SD":
            check_type_or_throw_except(
                steps, 1, int, "Integrate requires a positive integer for the number of steps")
            check_type_or_throw_except(
                recalc_forces, 1, bool, "recalc_forces has to be a bool")
            check_type_or_throw_except(
                reuse_forces, 1, bool, "reuse_forces has to be a bool")

            _integrate(steps, recalc_forces, reuse_forces)

            if globals.set_py_interrupt:
                PyErr_SetInterrupt()
                globals.set_py_interrupt = False
                PyErr_CheckSignals()

        elif self._method == "STEEPEST_DESCENT":
            minimize_energy_init(self._steepest_descent_params["f_max"],
                                 self._steepest_descent_params["gamma"],
                                 steps,
                                 self._steepest_descent_params["max_displacement"])
            mpi_minimize_energy()
        else:
            raise ValueError("No integrator method set!")

        handle_errors("Encountered errors during integrate")

    def set_steepest_descent(self, *args, **kwargs):
        """
        Set parameters for steepest descent.

        .. seealso::
            :class:`espressomd.minimize_energy.MinimizeEnergy`

        """
        req = ["f_max", "gamma", "max_displacement"]
        for key in kwargs:
            if key not in req:
                raise Exception("Set required parameter %s first." % key)

        self._steepest_descent_params.update(kwargs)
        self._method = "STEEPEST_DESCENT"

    def set_vv(self):
        """
        Set the integration method to Velocity Verlet.

        """
        self._method = "VV"

    def set_nvt(self):
        """
        Set the integration method to NVT.

        """
        self._method = "NVT"
        integrate_set_nvt()

    def set_sd(self):
        """
        Set the integration method to SD.

        """
        self._method = "SD"
        integrate_set_sd()
        handle_errors(
            "Encountered error while setting integration method to SD")

    def set_isotropic_npt(self, ext_pressure, piston,
                          direction=(True, True, True), cubic_box=False):
        """
        Set the integration method to NPT.

        Parameters
        ----------
        ext_pressure : :obj:`float`
            The external pressure.
        piston : :obj:`float`
            The mass of the applied piston.
        direction : (3,) array_like of :obj:`bool`, optional
            Select which dimensions are allowed to fluctuate by assigning
            them to ``True``.
        cubic_box : :obj:`bool`, optional
            If ``True``, a cubic box is assumed and the value of ``direction``
            will be ignored when rescaling the box. This is required e.g. for
            electrostatics and magnetostatics.

        """
        IF NPT:
            self._method = "NPT"
            if isinstance(direction, np.ndarray):
                direction = list(map(int, direction))
            self._isotropic_npt_params['ext_pressure'] = ext_pressure
            self._isotropic_npt_params['piston'] = piston
            self._isotropic_npt_params['direction'] = direction
            self._isotropic_npt_params['cubic_box'] = cubic_box
            check_type_or_throw_except(
                ext_pressure, 1, float, "NPT parameter ext_pressure must be a float")
            check_type_or_throw_except(
                piston, 1, float, "NPT parameter piston must be a float")
            check_type_or_throw_except(
                direction, 3, int, "NPT parameter direction must be an array-like of three bools")
            check_type_or_throw_except(
                cubic_box, 1, int, "NPT parameter cubic_box must be a bool")
            if (integrate_set_npt_isotropic(ext_pressure, piston, direction[0],
                                            direction[1], direction[2], cubic_box)):
                handle_errors(
                    "Encountered errors setting up the NPT integrator")
        ELSE:
            raise Exception("NPT not compiled in.")
