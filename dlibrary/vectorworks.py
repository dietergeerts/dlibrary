"""Module for all Vectorworks related stuff, like settings and active plugin features.
"""
import os
from abc import ABCMeta, abstractmethod

import vs
from dlibrary.object_base import AbstractKeyedObject, ObjectRepository
from dlibrary.utility import SingletonMeta


class PlatformEnum(object):
    """Enum to identify the platform Vectorworks is running on.
    """

    MAC_OS = 1
    WINDOWS = 2


class Vectorworks(object, metaclass=SingletonMeta):
    """Singleton to represent the running Vectorworks instance.
    """

    def __init_version_information(self):
        major, minor, maintenance, self.__platform, build_number = vs.GetVersionEx()
        self.__version = str(major + 1995 if major > 12 else major)

    def __init_user_information(self):
        self.__user_id = vs.GetActiveSerialNumber()[-6:]

    @property
    def platform(self) -> int:
        """The platform (= OS) Vectorworks is running on.
        :rtype: PlatformEnum
        """
        self.__init_version_information() if self.__platform is None else None
        return self.__platform

    @property
    def version(self) -> str:
        """Vectorworks' main version, like '12.5', or '2016'.
        :rtype: str
        """
        self.__init_version_information() if self.__version is None else None
        return self.__version

    @property
    def user_id(self) -> str:
        """The user' identification number (= last 6 digits of serial = dongle number)
        :rtype: str
        """
        self.__init_user_information() if self.__user_id is None else None
        return self.__user_id

    def get_os_independent_filepath(self, filepath: str) -> str:
        """Resolves the filepath to be os independent.

        Patrick Stanford <patstanford@coviana.com> on the VectorScript Discussion List:
        Since Mac OS 10, as they're rewritten it using UNIX kernel, the mac uses Posix natively.
        Since VW predates that, the old calls use HFS paths and need to be converted for newer APIs.
        You can ask VW to do the conversion, as simply replacing the characters are not enough (Posix
        uses volume mounting instead of drive names). This can be done through vs.ConvertHSF2PosixPath().
        """
        return vs.ConvertHSF2PosixPath(filepath)[1] if self.platform == PlatformEnum.MAC_OS else filepath

    def get_plugin_file_filepath(self, filename: str) -> str:
        """Resolves the filepath based on the filename for a file in one of the plugin directories.
        """
        return self.get_os_independent_filepath(os.path.join(vs.FindFileInPluginFolder(filename)[1], filename))

    # noinspection PyMethodMayBeStatic
    def show_message(self, message: str):
        """Show a floating message in the message palette.

        Handy to show processing information or script results.
        Any previous messages will be cleared.
        """
        vs.Message(message)

    # noinspection PyMethodMayBeStatic
    def clear_message(self):
        """Clear any floating messages and close the message palette.
        """
        vs.ClrMessage()


class VectorworksSecurity(object):
    """Decorator to secure a function based on the user id and/or VW version running.
    
    If used together with other decorators, all decorators below will not be executed if permission is denied.
    So keep that in mind when applying multiple decorators to your function, as some may not be executed!
    """

    def __init__(self, version: str=None, user_ids: set=None, on_version_denied: callable=None, 
                 on_user_id_denied: callable=None):
        """
        :param user_ids: User id == last 6 digits of serial == dongle number!
        :type user_ids: set[str]
        :type on_version_denied: (str) -> None  
        :type on_user_id_denied: (str) -> None
        """
        self.__version = version
        self.__user_ids = user_ids
        self.__on_version_denied = on_version_denied
        self.__on_user_id_denied = on_user_id_denied        

    def __call__(self, function: callable) -> callable:
        
        def decorator(*args, **kwargs):
            if self.__has_version_permission() and self.__has_user_id_permission():
                function(*args, **kwargs)
                
        return decorator
    
    def __has_version_permission(self) -> bool:
        permission = True
        if self.__version:
            version = Vectorworks().version
            permission = version == self.__version
            if not permission and self.__on_version_denied:
                self.__on_version_denied(version)
        return permission
    
    def __has_user_id_permission(self) -> bool:
        permission = True        
        if self.__user_ids:
            user_id = Vectorworks().user_id
            permission = user_id in self.__user_ids
            if not permission and self.__on_user_id_denied:
                self.__on_user_id_denied(user_id)
        return permission


class ActivePlugin(object, metaclass=SingletonMeta):
    """Singleton to represent the currently executing plugin, hence 'active'.

    Note that this is a singleton in the view of the currently executing plugin script.
    Be aware of this when changing this class' functionality.
    """

    @property
    def name(self) -> str:
        """Will return the name of the menu/tool/object plugin.
        :rtype: str
        """
        return vs.GetPluginInfo()[1]

    @property
    def handle(self) -> vs.Handle:
        """Will return the instance or definition handle of an object plugin.
        :rtype: vs.Handle
        """
        succeeded, name, plugin_handle, record_handle, wall_handle = vs.GetCustomObjectInfo()
        return plugin_handle if succeeded else vs.GetObject(self.name)

    @property
    def instance(self) -> AbstractKeyedObject:
        """Will return the instance, represented by PluginObject, or None if in definition 'mode'.
        :rtype: PluginObject
        """
        succeeded, name, plugin_handle, record_handle, wall_handle = vs.GetCustomObjectInfo()
        return ObjectRepository().get(plugin_handle) if succeeded else None


class ActivePluginEventEnum(object):
    """Enum to identify the possible plugin events.
    """

    VSO_ON_RESET = 3           # data: -; Will also happen for none-event-enabled plugins!
    VSO_ON_INITIALIZATION = 5  # data: -
    VSO_ON_DOUBLE_CLICK = 7    # data: -; Will only happen when double click behaviour is set to custom event!
    VSO_ON_WIDGET_CLICK = 35   # data: widget_id
    VSO_ON_WIDGET_PREP = 41    # data: -
    VSO_ON_ADD_STATE = 44      # data: widget_id


class OnActivePluginEvent(object):
    """Decorator for setting an event callback for an event-enabled plugin.

    The function which we decorate will execute first, to enable extra initialization prior to the callback.
    For none-event-enabled plugins, only the VSO_ON_RESET event will happen!
    """

    def __init__(self, event: int, callback: callable):
        """
        :type event: ActivePluginEventEnum  
        :type callback: (int) -> None
        """
        self.__event = event
        self.__callback = callback

    def __call__(self, function: callable) -> callable:

        def decorator(*args, **kwargs):
            function(*args, **kwargs)
            event, data = vs.vsoGetEventInfo()
            self.__callback(data) if event == self.__event else None

        return decorator


class AbstractResetArgs(object, metaclass=ABCMeta):
    """Abstract base class for reset arguments.
    """
    pass


class EmptyResetArgs(AbstractResetArgs):
    """Reset arguments for when they are something else then available here.
    """
    pass


class CreationResetArgs(AbstractResetArgs):
    """Reset arguments for when the reset happened because of creation.
    """
    pass


class ParameterChangeResetArgs(AbstractResetArgs):
    """Reset arguments for when the reset happened because of a parameter change.
    """

    def __init__(self, index: int):
        self.__index = index
        
    def __init_name(self):
        self.__name = vs.GetFldName(vs.GetCustomObjectInfo()[3], self.__index)

    @property
    def name(self) -> str:
        """Returns the name of the changed parameter.
        :rtype: str
        """
        self.__init_name() if self.__name is None else None
        return self.__name


class OnActivePluginReset(object):
    """Decorator for setting a reset callback with reset args for an event-enabled plugin.
    
    (!) If you don't need the reset args, then use OnActivePluginEvent, as it creates more overhead for VW.   
    The function which we decorate will execute first, to enable extra initialization prior to the callback.
    """

    def __init__(self, callback: callable):
        """
        :type callback: (AbstractResetArgs) -> None
        """
        self.__callback = callback
        self.__reset_args = None

    def __call__(self, function: callable) -> callable:

        @OnActivePluginEvent(ActivePluginEventEnum.VSO_ON_RESET, self.__execute_callback)
        @OnActivePluginEvent(ActivePluginEventEnum.VSO_ON_RESET, self.__resolve_reset_args)
        @OnActivePluginEvent(ActivePluginEventEnum.VSO_ON_ADD_STATE, self.__add_reset_args_state)
        @OnActivePluginEvent(ActivePluginEventEnum.VSO_ON_INITIALIZATION, self.__init_reset_args)
        def decorator(*args, **kwargs):
            function(*args, **kwargs)

        return decorator

    # noinspection PyUnusedLocal
    @staticmethod
    def __init_reset_args(data: int):
        vs.SetPrefInt(590, 1)      # 590 = enable state eventing, 1 = reset state events.
        vs.SetObjPropVS(18, True)  # 18 = accept states.

    @staticmethod
    def __add_reset_args_state(data: int):
        vs.vsoStateAddCurrent(ActivePlugin().handle, data)  # Only this MUST be called, nothing else!

    # noinspection PyUnusedLocal
    def __resolve_reset_args(self, data: int):
        self.__reset_args = (
            self.__try_get_creation_reset_args() or
            self.__try_get_parameter_change_reset_args() or
            EmptyResetArgs())
        vs.vsoStateClear(ActivePlugin().handle)  # EXTREMELY IMPORTANT to have this!

    # noinspection PyUnusedLocal
    def __execute_callback(self, data: int):
        self.__callback(self.__reset_args)
        
    @staticmethod
    def __try_get_creation_reset_args() -> CreationResetArgs:
        trigger = vs.vsoStateGet(ActivePlugin().handle, 0)  # 0 = creation. (13 and 16 on 2nd round also happens!)
        return CreationResetArgs() if trigger else None

    @staticmethod
    def __try_get_parameter_change_reset_args() -> ParameterChangeResetArgs:
        trigger, widget_id, parameter_index, old_value = vs.vsoStateGetParamChng(ActivePlugin().handle)
        return ParameterChangeResetArgs(parameter_index) if trigger else None


class AbstractWidget(object, metaclass=ABCMeta):
    """Abstract base class for object info-pallet widgets.
    """

    def __init__(self, is_visible: callable=None, is_enabled: callable=None, on_click: callable=None):
        """
        :type is_visible: () -> bool  
        :type is_enabled: () -> bool  
        :type on_click: () -> None
        """
        self.__is_visible = is_visible
        self.__is_enabled = is_enabled
        self.__on_click = on_click
        self._id = 0  # Will be set when added to the info-pallet.

    @property
    def has_custom_visibility(self) -> bool:
        """Returns whether the widget has a visibility check set.
        :rtype: bool
        """
        return self.__is_visible is not None
    
    @property
    def has_custom_enabling(self) -> bool:
        """Returns whether the widget has an enabled check set.
        :rtype: bool
        """
        return self.__is_enabled is not None

    def add(self, widget_id: int):
        """Adds the widget to the object info-pallet with the given id.
        """
        self._id = widget_id
        self._add()

    def update(self):
        """Update the widget visibility and enabled status.
        """
        vs.vsoWidgetSetVisible(self._id, self.__is_visible()) if self.has_custom_visibility else None
        vs.vsoWidgetSetEnable(self._id, self.__is_enabled()) if self.has_custom_enabling else None
        
    def click(self):
        """Execute the user's widget click.
        """
        self.__on_click() if self.__on_click else None

    @abstractmethod
    def _add(self):
        """Adds the widget to the object info-pallet, with the widget specific call.
        """
        pass


class ParameterWidget(AbstractWidget):
    """Represents a widget for the given parameter, VW will use the correct type automatically.
    """

    def __init__(self, parameter: str, is_visible: callable=None, is_enabled: callable=None, on_click: callable=None):
        """
        :type is_visible: () -> bool  
        :type is_enabled: () -> bool
        :type on_click: () -> None
        """
        super().__init__(is_visible, is_enabled, on_click)
        self.__parameter = parameter

    def _add(self):
        vs.vsoAddParamWidget(self._id, self.__parameter, '')  # '' for using the parameter's alternate name.


class ButtonWidget(AbstractWidget):
    """Represents a button on the object info-pallet.
    """

    def __init__(self, label: str, on_click: callable, reset_object: bool=False, is_visible: callable=None,
                 is_enabled: callable=None):
        """
        :type on_click: () -> None  
        :param reset_object: If true, the pio instance will be reset after the on_click handler.  
        :type is_visible: () -> bool  
        :type is_enabled: () -> bool
        """
        super().__init__(is_visible, is_enabled, self._click)
        self.__label = label
        self.__on_click = on_click
        self.__reset_object = reset_object
        
    def _add(self):
        vs.vsoInsertWidget(self._id, 12, self._id, self.__label, 0)  # 12 = Button

    def _click(self):
        self.__on_click()
        vs.ResetObject(ActivePlugin().handle) if self.__reset_object else None


class StaticTextWidget(AbstractWidget):
    """Represents static text on the object info-pallet.
    """

    def __init__(self, label: str, is_visible: callable=None, is_enabled: callable=None, on_click: callable=None):
        """
        :type is_visible: () -> bool  
        :type is_enabled: () -> bool  
        :type on_click: () -> None
        """
        super().__init__(is_visible, is_enabled, on_click)
        self.__label = label

    def _add(self):
        vs.vsoInsertWidget(self._id, 13, self._id, self.__label, 0)  # 13 = Static text.
        
        
class SeparatorWidget(AbstractWidget):
    """Represents a separator on the object info-pallet. Great for grouping parameters.
    """

    def __init__(self, label: str='', is_visible: callable=None, is_enabled: callable=None, on_click: callable=None):
        """
        :type is_visible: () -> bool  
        :type is_enabled: () -> bool  
        :type on_click: () -> None
        """
        super().__init__(is_visible, is_enabled, on_click)
        self.__label = label

    def _add(self):
        vs.vsoInsertWidget(self._id, 100, self._id, self.__label.upper() + ' ', 0)  # 100 = Separator.


class ActivePluginInfoPallet(object):
    """Decorator for setting the object info-pallet for an event-enabled plugin.
    
    The function which we decorate will execute first, to enable extra initialization prior to the callback.
    """

    def __init__(self, widgets: list):
        """
        :type widgets: list[AbstractWidget]
        """
        self.__widgets = widgets

    def __call__(self, function: callable) -> callable:

        @OnActivePluginEvent(ActivePluginEventEnum.VSO_ON_WIDGET_CLICK, self.__on_widget_click)
        @OnActivePluginEvent(ActivePluginEventEnum.VSO_ON_WIDGET_PREP, self.__prepare_widgets)
        @OnActivePluginEvent(ActivePluginEventEnum.VSO_ON_INITIALIZATION, self.__init_info_pallet)
        def decorator(*args, **kwargs):
            function(*args, **kwargs)

        return decorator

    # noinspection PyUnusedLocal
    def __init_info_pallet(self, data: int):
        vs.SetObjPropVS(8, True)  # 8 = Custom Info Palette property; 12 = Custom widget visibility!
        vs.SetObjPropVS(12, True) if any(w.has_custom_visibility for w in self.__widgets) else None
        [widget.add(index) for index, widget in enumerate(self.__widgets)]

    # noinspection PyUnusedLocal
    def __prepare_widgets(self, data: int):
        [widget.update() for widget in self.__widgets]
        vs.vsoSetEventResult(-8)  # -8 = event handled! REQUIRED cleanup!

    def __on_widget_click(self, data: int):
        self.__widgets[data].click()  # data will be the widget index.


class DoubleClickBehaviourEnum(object):
    """Enum for the available options of the double click behaviour for the plugin.
    """
    
    DEFAULT = 0            # The default behaviour for the object type will be used.
    CUSTOM_EVENT = 1       # The VSO_ON_DOUBLE_CLICK event will be thrown.
    PROPERTIES_DIALOG = 2  # Is actually the object info palette that will be shown.
    RESHAPE_MODE = 3       # Go into reshape mode, practical for path shaped objects.


class ActivePluginDoubleClickBehaviour(object):
    """Decorator to set the double click behaviour for an event-enabled plug-in.
    
    The function which we decorate will execute first, to enable extra initialization prior to the callback.
    """

    def __init__(self, behaviour: int, event_handler: callable=None):
        """
        :type behaviour: DoubleClickBehaviourEnum
        :type event_handler: () -> None
        """
        self.__behaviour = behaviour
        self.__event_handler = event_handler

    def __call__(self, function: callable) -> callable:

        @OnActivePluginEvent(ActivePluginEventEnum.VSO_ON_DOUBLE_CLICK, self.__on_double_click)
        @OnActivePluginEvent(ActivePluginEventEnum.VSO_ON_INITIALIZATION, self.__init_double_click_behaviour)
        def decorator(*args, **kwargs):
            function(*args, **kwargs)

        return decorator

    def __init_double_click_behaviour(self):
        vs.SetObjPropCharVS(3, self.__behaviour)  # 3 = Double click behavior!

    # noinspection PyUnusedLocal
    def __on_double_click(self, data: int):
        self.__event_handler()


class ActivePluginFontStyleEnabled(object):
    """Decorator for setting the plugin font style enabled.
    
    The function which we decorate will execute first, to enable extra initialization prior to the callback.
    """

    def __call__(self, function: callable) -> callable:

        # Because of a VW bug, font style enabling has to happen in the reset event for event-enabled plug-ins!
        # For none-event-enabled plugins, the reset event will happen (it's the only), so we have no problem here.
        @OnActivePluginEvent(ActivePluginEventEnum.VSO_ON_RESET, self.__set_font_style_enabled)
        def decorator(*args, **kwargs):
            function(*args, **kwargs)

        return decorator

    # noinspection PyUnusedLocal
    @staticmethod
    def __set_font_style_enabled(data: int):
        vs.SetObjectVariableBoolean(ActivePlugin().handle, 800, True)


class AbstractActivePluginParameters(object, metaclass=ABCMeta):
    """
    
    Vectorworks will always give you the initial values of parameters. So when changing them inside your script,
    you'll still get the initial values. Therefore we'll create some sort of cache to remember the current values.
    """

    def __init__(self):
        self.__parameters = dict()

    def _get_parameter(self, name: str):
        return self.__parameters[name] if name in self.__parameters else self.__store_and_get_parameter(name)

    def __store_and_get_parameter(self, name: str):
        value = getattr(vs, 'P%s' % name)  # Vectorworks puts parameters inside the vs module!
        # For a boolean value, VW return 1 or 0, while we actually want a bool, so we'll convert if needed.
        record = vs.GetParametricRecord(ActivePlugin().handle)
        fields = [vs.GetFldName(record, index) for index in range(1, vs.NumFields(record) + 1)]
        is_bool = vs.GetFldType(record, fields.index(name) + 1) == 2
        self.__parameters[name] = value if not is_bool else value == 1
        return self.__parameters[name]

    def _set_parameter(self, name: str, value):
        self.__parameters[name] = value
        vs.SetRField(ActivePlugin().handle, ActivePlugin().name, name,
                     value if isinstance(value, str) else vs.Num2Str(-2, value))
