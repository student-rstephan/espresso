import sys
import numpy as np
import unittest as ut
import espressomd
import espressomd.observables
import espressomd.lb
from espressomd import utils
import tests_common


@ut.skipIf(
    not espressomd.has_features('LB_GPU') or espressomd.has_features('SHANCHEN'),
    "LB_GPU not compiled in or SHANCHEN activated, can not check functionality.")
class TestCylindricalLBObservable(ut.TestCase):
    """
    Testcase for the CylindricalFluxDensityObservable.

    """
    system = espressomd.System(box_l=(10,10,10))
    system.time_step = 0.01
    system.cell_system.skin = 0.4

    params = {
        'ids': range(10),
        'center': [5.0, 5.0, 5.0],  # center of the histogram
        'axis': 'y',
        'n_r_bins': 10,  # number of bins in r
        'n_phi_bins': 10,  # -*- in phi
        'n_z_bins': 10,  # -*- in z
        'min_r': 0.0,
        'min_phi': -np.pi,
        'min_z': 0.0,
        'max_r': 5.0,
        'max_phi': np.pi,
        'max_z': 10.0,
    }
    
    @classmethod
    def setUpClass(self):
        self.lbf = espressomd.lb.LBFluidGPU(
        agrid=1.0, fric=1.0, dens=1.0, visc=1.0, tau=0.01)
        self.system.actors.add(self.lbf)

    def tearDown(self):
        self.lbf[np.floor(self.position)].velocity = [0.0, 0.0, 0.0]

    def swap_axis(self, arr, axis):
        if axis == 'x':
            arr = np.dot(tests_common.rotation_matrix(
                [0, 1, 0], np.pi / 2.0), arr)
        elif axis == 'y':
            arr = np.dot(tests_common.rotation_matrix(
                [1, 0, 0], -np.pi / 2.0), arr)
        return arr

    def swap_axis_inverse(self, arr, axis):
        if axis == 'x':
            arr = np.dot(tests_common.rotation_matrix(
                [0, 1, 0], -np.pi / 2.0), arr)
        elif axis == 'y':
            arr = np.dot(tests_common.rotation_matrix(
                [1, 0, 0], np.pi / 2.0), arr)
        return arr

    def pol_coords(self):
        positions = np.zeros((len(self.params['ids']), 3))
        for i, p in enumerate(self.system.part):
            tmp = p.pos - np.array(self.params['center'])
            tmp = self.swap_axis_inverse(tmp, self.params['axis'])
            positions[i, :] = tests_common.transform_pos_from_cartesian_to_polar_coordinates(
                tmp)
        return positions

    def set_particles(self):
        self.system.part.clear()
        # Choose the cartesian velocities such that each particle gets the same
        # v_r, v_phi and v_z, respectively.
        self.v_r = .75
        self.v_phi = 2.5
        self.v_z = 1.5
        node_positions = np.arange(-4.5, 5.0, 1.0)
        for i, value in enumerate(node_positions):
            position = np.array(
                [node_positions[i], node_positions[i], node_positions[i]])
            v_y = (position[0] * np.sqrt(position[0]**2.0 + position[1]**2.0) * self.v_phi +
                   position[1] * self.v_r) / np.sqrt(position[0]**2.0 + position[1]**2.0)
            v_x = (self.v_r * np.sqrt(position[0]**2.0 + position[1] **
                                      2.0) - position[1] * v_y) / position[0]
            velocity = np.array([v_x, v_y, self.v_z])
            velocity = self.swap_axis(velocity, self.params['axis'])
            self.position = self.swap_axis(position, self.params['axis'])
            self.position += np.array(self.params['center'])
            self.system.part.add(id=i, pos=self.position)
            self.lbf[np.floor(self.position)].velocity = velocity

    def normalize_with_bin_volume(self, histogram):
        bin_volume = tests_common.get_cylindrical_bin_volume(
            self.params['n_r_bins'],
            self.params['n_phi_bins'],
            self.params['n_z_bins'],
            self.params['min_r'],
            self.params['max_r'],
            self.params['min_phi'],
            self.params['max_phi'],
            self.params['min_z'],
            self.params['max_z'])
        # Normalization
        for i in range(self.params['n_r_bins']):
            histogram[i, :, :] /= bin_volume[i]
        return histogram

    def LB_fluxdensity_profile_test(self):
        self.set_particles()
        # Set up the Observable.
        p = espressomd.observables.CylindricalLBFluxDensityProfileAtParticlePositions(
            **self.params)
        core_hist = np.array(
            p.calculate()).reshape(
            self.params['n_r_bins'],
            self.params['n_phi_bins'],
            self.params['n_z_bins'],
            3)
        core_hist_v_r = core_hist[:, :, :, 0]
        core_hist_v_phi = core_hist[:, :, :, 1]
        core_hist_v_z = core_hist[:, :, :, 2]
        self.pol_positions = self.pol_coords()
        np_hist, _ = np.histogramdd(self.pol_positions, bins=(self.params['n_r_bins'],
                                                              self.params['n_phi_bins'],
                                                              self.params['n_z_bins']),
                                    range=[(self.params['min_r'],
                                            self.params['max_r']),
                                           (self.params['min_phi'],
                                            self.params['max_phi']),
                                           (self.params['min_z'],
                                            self.params['max_z'])])
        np_hist = self.normalize_with_bin_volume(np_hist)
        np.testing.assert_array_almost_equal(np_hist * self.v_r, core_hist_v_r)
        np.testing.assert_array_almost_equal(
            np_hist * self.v_phi, core_hist_v_phi)
        np.testing.assert_array_almost_equal(np_hist * self.v_z, core_hist_v_z)

    def LB_velocity_profile_test(self):
        self.set_particles()
        # Set up the Observable.
        p = espressomd.observables.CylindricalLBVelocityProfileAtParticlePositions(
            **self.params)
        core_hist = np.array(
            p.calculate()).reshape(
            self.params['n_r_bins'],
            self.params['n_phi_bins'],
            self.params['n_z_bins'],
            3)
        core_hist_v_r = core_hist[:, :, :, 0]
        core_hist_v_phi = core_hist[:, :, :, 1]
        core_hist_v_z = core_hist[:, :, :, 2]
        self.pol_positions = self.pol_coords()
        np_hist, _ = np.histogramdd(self.pol_positions, bins=(self.params['n_r_bins'],
                                                              self.params['n_phi_bins'],
                                                              self.params['n_z_bins']),
                                    range=[(self.params['min_r'],
                                            self.params['max_r']),
                                           (self.params['min_phi'],
                                            self.params['max_phi']),
                                           (self.params['min_z'],
                                            self.params['max_z'])])
        for x in np.nditer(np_hist, op_flags=['readwrite']):
            if x[...] > 0.0:
                x[...] /= x[...]
        np.testing.assert_array_almost_equal(np_hist * self.v_r, core_hist_v_r)
        np.testing.assert_array_almost_equal(np_hist * self.v_phi, core_hist_v_phi)
        np.testing.assert_array_almost_equal(np_hist * self.v_z, core_hist_v_z)

    def test_x_axis(self):
        self.params['axis'] = 'x'
        self.LB_fluxdensity_profile_test()
        self.LB_velocity_profile_test()

    def test_y_axis(self):
        self.params['axis'] = 'y'
        self.LB_fluxdensity_profile_test()
        self.LB_velocity_profile_test()

    def test_z_axis(self):
        self.params['axis'] = 'z'
        self.LB_fluxdensity_profile_test()
        self.LB_velocity_profile_test()


if __name__ == "__main__":
    suite = ut.TestSuite()
    suite.addTests(ut.TestLoader().loadTestsFromTestCase(
        TestCylindricalLBObservable))
    result = ut.TextTestRunner(verbosity=4).run(suite)
    sys.exit(not result.wasSuccessful())