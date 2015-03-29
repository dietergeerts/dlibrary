from dlibrary.dialog.observable import LinkedObservableList, ObservableList, ObservableField, ObservableCommand


class AbstractViewModel(object):
    def __init__(self, model: object):
        self.__model = model

    @property
    def model(self) -> object: return self.__model


class ViewModelList(object):
    def __init__(self, model_list: list, abstract_view_model: callable, create_new_model: callable,
                 can_add_new_model: callable=None, can_add_dependent_property_observables: set={}):
        self.__items = LinkedObservableList(model_list, abstract_view_model, lambda view_model: view_model.model)
        self.__selected_items = ObservableList()
        self.__abstract_view_model = abstract_view_model
        self.__create_new_model = create_new_model
        self.__can_add_new_model = can_add_new_model
        self.__can_add_dependency = ObservableField()
        self.__can_add_dependencies = can_add_dependent_property_observables
        self.__new_item = ObservableField()
        self.__add_item = ObservableCommand(self.__on_add_item, self.__can_add_item, {self.__can_add_dependency})
        self.__setup_new_item()

    @property
    def items(self) -> ObservableList: return self.__items

    @property
    def selected_items(self) -> ObservableList: return self.__selected_items

    @property
    def new_item(self) -> ObservableField: return self.__new_item

    @property
    def add_item(self) -> ObservableCommand: return self.__add_item

    def __can_add_item(self):
        return self.__can_add_new_model(self.new_item.value.model) if self.__can_add_new_model is not None else True

    def __on_add_item(self): self.items.append(self.new_item.value); self.__setup_new_item()

    def __setup_new_item(self):
        if self.new_item.value: self.__unsubscribe_to_dependencies(self.new_item.value)
        self.new_item.value = self.__abstract_view_model(self.__create_new_model())
        self.__subscribe_to_dependencies(self.new_item.value)
        self.__on_new_item_dependency_changed()  # To reset check with the new item!

    def __subscribe_to_dependencies(self, view_model: AbstractViewModel):
        for dependency in self.__can_add_dependencies:
            observable = getattr(view_model, dependency)
            if isinstance(observable, ObservableField):
                observable.field_changed_event.subscribe(self.__on_new_item_dependency_changed)
            elif isinstance(observable, ObservableList):
                observable.list_changed_event.subscribe(self.__on_new_item_dependency_changed)
                observable.list_reordered_event.subscribe(self.__on_new_item_dependency_changed)

    def __unsubscribe_to_dependencies(self, view_model: AbstractViewModel):
        for dependency in self.__can_add_dependencies:
            observable = getattr(view_model, dependency)
            if isinstance(observable, ObservableField):
                observable.field_changed_event.unsubscribe(self.__on_new_item_dependency_changed)
            elif isinstance(observable, ObservableList):
                observable.list_changed_event.unsubscribe(self.__on_new_item_dependency_changed)
                observable.list_reordered_event.unsubscribe(self.__on_new_item_dependency_changed)

    def __on_new_item_dependency_changed(self, *args, **kwargs):
        self.__can_add_dependency.field_changed_event.raise_event()