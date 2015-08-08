from abc import ABCMeta
from unittest import TestCase
from dlibrary.dialog_custom import Layout, AlignMode, Align, TextStyleEnum, AbstractDataContext, Button, EditText, GroupBox, \
    ListBox, ListBrowser, PullDownMenu, Separator, StaticText, TabControl, TabPane
from dlibrary.utility import ObservableList, ObservableCommand


class AbstractControlTest(TestCase, metaclass=ABCMeta):

    def __init__(self, *args, alignments: dict):
        """
        :type alignments: {Layout(Enum): AlignMode(Enum)}
        """
        super().__init__(*args)
        self.__alignments = alignments

    @property
    def _control(self):
        return self.__control

    @_control.setter
    def _control(self, value):
        self.__control = value

    def test_control_alignment(self):
        if len(self.__alignments) == 0:
            self.assertFalse(Align.has_decorator(self._control))
        else:
            self.assertTrue(Align.has_decorator(self._control))

            if Layout.VERTICAL not in self.__alignments:
                self.assertFalse(Align.has_alignment(self._control, Layout.VERTICAL))
            else:
                self.assertTrue(Align.has_alignment(self._control, Layout.VERTICAL))
                self.assertEqual(Align.get_alignment(self._control, Layout.VERTICAL),
                                 self.__alignments[Layout.VERTICAL])

            if Layout.HORIZONTAL not in self.__alignments:
                self.assertFalse(Align.has_alignment(self._control, Layout.HORIZONTAL))
            else:
                self.assertTrue(Align.has_alignment(self._control, Layout.HORIZONTAL))
                self.assertEqual(Align.get_alignment(self._control, Layout.HORIZONTAL),
                                 self.__alignments[Layout.HORIZONTAL])


class ButtonTest(AbstractControlTest):

    def __init__(self, *args):
        super().__init__(
            *args,
            alignments={  # A button should always shift to fit the layout.
                Layout.HORIZONTAL: AlignMode.SHIFT,
                Layout.VERTICAL: AlignMode.SHIFT
            })

    def setUp(self):
        self.__caption = 'Do This'
        self.__data_command = 'command'
        self.__data_context = type('Test', (object,), {})
        setattr(self.__data_context, self.__data_command, ObservableCommand(lambda: None))
        self.__data_parent = AbstractDataContext(self.__data_context)
        self._control = Button(0, 0, '', self.__data_parent, '', self.__data_command, self.__caption)

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


class EditTextTest(AbstractControlTest):

    def __init__(self, *args):
        super().__init__(
            *args,
            alignments={  # An edit-text should resize on a vertical layout.
                Layout.VERTICAL: AlignMode.RESIZE
            })

    def setUp(self):
        self.__data_context = type('Test', (object,), {})
        self.__data_parent = AbstractDataContext(self.__data_context)
        self._control = EditText(0, 0, '', self.__data_parent, '', '', '', '', 20, 1)


class GroupBoxTest(AbstractControlTest):

    def __init__(self, *args):
        super().__init__(
            *args,
            alignments={  # A groupbox should always resize.
                Layout.HORIZONTAL: AlignMode.RESIZE,
                Layout.VERTICAL: AlignMode.RESIZE
            })

    def setUp(self):
        self.__data_context = type('Test', (object,), {})
        self.__data_parent = AbstractDataContext(self.__data_context)
        self._control = GroupBox(0, 0, '', self.__data_parent, '', '', '', False)


class ListBoxTest(AbstractControlTest):

    def __init__(self, *args):
        super().__init__(
            *args,
            alignments={  # A listbox should always resize.
                Layout.HORIZONTAL: AlignMode.RESIZE,
                Layout.VERTICAL: AlignMode.RESIZE
            })

    def setUp(self):
        self.__data_items = 'items'
        self.__data_selected_items = 'selected_items'
        self.__data_context = type('Test', (object,), {})
        setattr(self.__data_context, self.__data_items, ObservableList())
        setattr(self.__data_context, self.__data_selected_items, ObservableList())
        self.__data_parent = AbstractDataContext(self.__data_context)
        self._control = ListBox(0, 0, '', self.__data_parent, '', '', self.__data_items, self.__data_selected_items, '',
                                20, 20)


class ListBrowserTest(AbstractControlTest):

    def __init__(self, *args):
        super().__init__(
            *args,
            alignments={  # A list-browser should always resize.
                Layout.HORIZONTAL: AlignMode.RESIZE,
                Layout.VERTICAL: AlignMode.RESIZE
            })

    def setUp(self):
        self.__data_items = 'items'
        self.__data_selected_items = 'selected_items'
        self.__data_context = type('Test', (object,), {})
        setattr(self.__data_context, self.__data_items, ObservableList())
        setattr(self.__data_context, self.__data_selected_items, ObservableList())
        self.__data_parent = AbstractDataContext(self.__data_context)
        self._control = ListBrowser(0, 0, '', self.__data_parent, '', '', self.__data_items, self.__data_selected_items,
                                    False, (), 20, 20)


class PullDownMenuTest(AbstractControlTest):

    def __init__(self, *args):
        super().__init__(
            *args,
            alignments={  # A pull-down-menu should resize in a vertical layout.
                Layout.VERTICAL: AlignMode.RESIZE
            })

    def setUp(self):
        self.__data_items = 'items'
        self.__data_context = type('Test', (object,), {})
        setattr(self.__data_context, self.__data_items, ObservableList())
        self.__data_parent = AbstractDataContext(self.__data_context)
        self._control = PullDownMenu(0, 0, '', self.__data_parent, '', '', self.__data_items, '', '', 20)


class SeparatorTest(AbstractControlTest):

    def __init__(self, *args):
        super().__init__(
            *args,
            alignments={})  # A separator will align automatically in VW, so no need to align.

    def setUp(self):
        self.__data_context = type('Test', (object,), {})
        self.__data_parent = AbstractDataContext(self.__data_context)
        self._control = Separator(0, 0, '', self.__data_parent, '')


class StaticTextTest(AbstractControlTest):

    def __init__(self, *args):
        super().__init__(
            *args,
            alignments={  # A static text control should resize in a vertical layout.
                Layout.VERTICAL: AlignMode.RESIZE
            })

    def setUp(self):
        self.__data_context = type('Test', (object,), {})
        self.__data_parent = AbstractDataContext(self.__data_context)
        self._control = StaticText(0, 0, '', self.__data_parent, '', '', 20, TextStyleEnum.REGULAR)


class TabControlTest(AbstractControlTest):

    def __init__(self, *args):
        super().__init__(
            *args,
            alignments={  # A tab-control should always resize.
                Layout.HORIZONTAL: AlignMode.RESIZE,
                Layout.VERTICAL: AlignMode.RESIZE
            })

    def setUp(self):
        self.__data_context = type('Test', (object,), {})
        self.__data_parent = AbstractDataContext(self.__data_context)
        self._control = TabControl(0, 0, '', self.__data_parent, '', '')


class TabPaneTest(AbstractControlTest):

    def __init__(self, *args):
        super().__init__(
            *args,
            alignments={})  # A tab pane will be automatically aligned by VW in it's parent tab-control.

    def setUp(self):
        self.__data_context = type('Test', (object,), {})
        self.__data_parent = AbstractDataContext(self.__data_context)
        self._control = TabPane(0, 0, '', TabControl(0, 0, '', self.__data_parent, '', ''), '', '', '')


# Make sure that the test engine isn't picking up any abstract base test classes!
del AbstractControlTest
