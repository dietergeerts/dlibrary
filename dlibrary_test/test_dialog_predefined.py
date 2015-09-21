from unittest import TestCase
from dlibrary.dialog_predefined import PlugInFileVsExceptionAlert, PlugInFileFileNotFoundErrorAlert, \
    PlugInFilePermissionErrorAlert, PlugInFileOsErrorAlert
from dlibrary_test.testing import VectorworksInstance


class PlugInFileVsExceptionAlertTest(TestCase):

    def test_creation_and_show(self):
        """
        The text of the alert should contain the plug-in name we give it.
        """
        PlugInFileVsExceptionAlert('DPluginTest').show()
        self.assertIn('DPluginTest', VectorworksInstance().last_alert_critical['text'])


class PlugInFileFileNotFoundErrorAlertTest(TestCase):

    def test_creation_and_show(self):
        """
        The text of the alert should contain the filename we give it.
        """
        PlugInFileFileNotFoundErrorAlert('DTest.xml').show()
        self.assertIn('DTest.xml', VectorworksInstance().last_alert_critical['text'])


class PlugInFilePermissionErrorAlertTest(TestCase):

    def test_creation_and_show(self):
        """
        The text of the alert should contain the filename we give it.
        """
        PlugInFilePermissionErrorAlert('DTest.xml').show()
        self.assertIn('DTest.xml', VectorworksInstance().last_alert_critical['text'])


class PlugInFileOsErrorAlertTest(TestCase):

    def test_creation_and_show(self):
        """
        The text of the alert should contain the filename we give it.
        """
        PlugInFileOsErrorAlert('DTest.xml').show()
        self.assertIn('DTest.xml', VectorworksInstance().last_alert_critical['text'])
