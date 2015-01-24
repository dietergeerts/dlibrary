from dlibrary.dialog.dialog import Dialog
from dlibrary.dialog.observable import ObservableList, ObservableField
from dlibrary.utility.exception import VSException

import pydevd
pydevd.settrace('localhost', port=8080, stdoutToServer=True, stderrToServer=True, suspend=False)


def run():
    try: dialog = Dialog('Main', DLibraryTestVsmViewModel())
    except VSException: raise
    except FileNotFoundError: raise
    except PermissionError: raise
    except OSError: raise
    else: dialog.show()

    # vs.AlertCritical('Could not find dialog file:', dialog_name)
    # vs.AlertCritical('Insufficient permissions on dialog file:', dialog_name)
    # vs.AlertCritical('Contents of dialog file is invalid:', dialog_name)


class DLibraryTestVsmViewModel(object):
    def __init__(self):
        item1 = DLibraryTestVsmViewModelItem('one', 'two')
        item2 = DLibraryTestVsmViewModelItem('three', 'four')
        item3 = DLibraryTestVsmViewModelItem('five', 'six')
        self.__items = ObservableList([item1, item2, item3])
        self.__selected_items = ObservableList([item1])
        self.__selected_items2 = ObservableList()
        self.__new_item = ObservableField(DLibraryTestVsmViewModelItem('new', 'new'))

    @property
    def items(self) -> ObservableList: return self.__items

    @property
    def selected_items(self) -> ObservableList: return self.__selected_items

    @property
    def selected_items2(self) -> ObservableList: return self.__selected_items2

    @property
    def new_item(self) -> ObservableField: return self.__new_item

    def add_item(self):
        self.__items.append(self.new_item.value)
        self.new_item.value = DLibraryTestVsmViewModelItem('new2', 'new2')


class DLibraryTestVsmViewModelItem(object):
    def __init__(self, prop_one: str, prop_two: str):
        self.__prop_one = ObservableField(prop_one)
        self.__prop_one.field_changed_event.subscribe(self.__update_prop_three)
        self.__prop_two = ObservableField(prop_two)
        self.__prop_two.field_changed_event.subscribe(self.__update_prop_three)
        self.__prop_three = ObservableField()
        self.__update_prop_three('', '')

    @property
    def prop_one(self) -> ObservableField: return self.__prop_one

    @property
    def prop_two(self) -> ObservableField: return self.__prop_two

    @property
    def prop_three(self) -> ObservableField: return self.__prop_three

    def __update_prop_three(self, old, new): self.prop_three.value = self.prop_one.value + ' | ' + self.prop_two.value