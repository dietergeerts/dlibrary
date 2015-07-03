from unittest import TestCase
from dlibrary.dialog.control import Layout, AlignMode, AbstractDataContext
from dlibrary.dialog.controls.button import Button
from dlibrary.utility.observable import ObservableCommand


class ButtonTest(TestCase):

    def setUp(self):
        self.__caption = 'Do This'
        self.__data_command = 'command'
        self.__data_context = type('Test', (object,), {})
        setattr(self.__data_context, self.__data_command, ObservableCommand(lambda: None))
        self.__data_parent = AbstractDataContext(self.__data_context)

    def test_control_alignment(self):
        """
        On aligning controls, a button should always shift to fit the layout.
        """
        self.assertTrue(Button.can_align(Layout.HORIZONTAL))
        self.assertEqual(AlignMode.SHIFT, Button.align_mode(Layout.HORIZONTAL))
        self.assertTrue(Button.can_align(Layout.VERTICAL))
        self.assertEqual(AlignMode.SHIFT, Button.align_mode(Layout.VERTICAL))

    def test_init_param_data_command(self):
        """
        The data_command reference should be given as a str. Otherwise, the button is useless.
        """
        self.assertRaises(ValueError, Button, 0, 0, '', self.__data_parent, '', None, self.__caption)
        self.assertRaises(ValueError, Button, 0, 0, '', self.__data_parent, '', '',   self.__caption)

    def test_init_param_caption(self):
        """
        The caption should be given as a str. Otherwise, the user will not know what it will do.
        """
        self.assertRaises(ValueError, Button, 0, 0, '', self.__data_parent, '', self.__data_command, None)
        self.assertRaises(ValueError, Button, 0, 0, '', self.__data_parent, '', self.__data_command, '')

    def test_init_valid_params(self):
        """
        Using valid parameters, the Button should be created normally.
        """
        Button(0, 0, '', self.__data_parent, '', self.__data_command, self.__caption)

    # TODO: The data_command has to be resolved to an ObservableCommand in order to be used with the Button.
    # TODO: The Button should listen to changes of the command, and act accordingly, being enabled/disabled.
    # TODO: The Button should execute the command when it receives its clicked event.
    # TODO: Test create method.
