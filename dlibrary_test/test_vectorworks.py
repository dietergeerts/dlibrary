from unittest import TestCase
from dlibrary.vectorworks import Vectorworks
from dlibrary_test.testing import VectorworksInstance


class VectorworksTest(TestCase):

    def test_version_property(self):
        """
        The version should give back the current running version as a string. This is not the internal version!
        They changed the versioning from VW12 to VW13, which became VW2008 instead. Now it is yearly with the year.
        """
        VectorworksInstance().version_major = 1
        self.assertEqual(Vectorworks().version, '1')
        VectorworksInstance().version_major = 12
        self.assertEqual(Vectorworks().version, '12')
        VectorworksInstance().version_major = 13
        self.assertEqual(Vectorworks().version, '2008')
        VectorworksInstance().version_major = 20
        self.assertEqual(Vectorworks().version, '2015')

    def test_dongle_property(self):
        """
        The dongle should give back the active dongle, which are the last 6 digits of the active serial number.
        """
        VectorworksInstance().serial_number = '123456-654321'
        self.assertEqual(Vectorworks().dongle, '654321')
