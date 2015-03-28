from dlibrary.dialog.observable import LinkedObservableList, ObservableList, ObservableField


class AbstractViewModel(object):
    def __init__(self, model: object):
        self.__model = model

    @property
    def model(self) -> object: return self.__model


class ViewModelList(object):
    def __init__(self, model_list: list, abstract_view_model: callable, get_default_model: callable):
        self.__items = LinkedObservableList(model_list, abstract_view_model, lambda view_model: view_model.model)
        self.__selected_items = ObservableList()
        self.__abstract_view_model = abstract_view_model
        self.__get_default_model = get_default_model
        self.__new_item = ObservableField()
        self.__setup_new_item()

    @property
    def items(self) -> ObservableList: return self.__items

    @property
    def selected_items(self) -> ObservableList: return self.__selected_items

    @property
    def new_item(self) -> ObservableField: return self.__new_item

    def add_item(self): self.items.append(self.new_item.value); self.__setup_new_item()

    def __setup_new_item(self): self.new_item.value = self.__abstract_view_model(self.__get_default_model())