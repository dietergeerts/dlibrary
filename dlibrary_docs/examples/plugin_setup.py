"""Examples on how you can setup your plugin through configuration, without needing to know the specifics of VW.

Vectorworks has many specifics you need to know when setting up your plugin, especially for event-enabled plugins. This
process of setting things up can be very tedious and time consuming, more so when you don't really know this part of VW
inside-out. DLibrary solves this by providing decorators you can use around your main executing function. This will
help you setup your plugin very fast, so you can concentrate on the actual functional logic your plugin is providing.

One thing you need to know is that even if your plugin isn't event-enabled, you can still work the same way, as
eventing will always happen, though only the reset event will be thrown and executed. This provides us with a generic,
standard way of setting up the plugin and it's code paths. You'll find many examples below, each of them representing
the plugin main executing function. Using this concept, the only thing you need to do in your plugin file (.vso, .vst,
.vsm) is:


from your.plugin.package import run

run()


Then this run method, which is the main executing function, can be decorated in order to set things up. All provided
setup decorators are done in a way that the run function will always execute first, then the decorator. This provides a
way to do some stuff first before the actual setup code is run, if you would have a need for that. Just keep in mind
that the only exception to this is the VectorworksSecurity decorator, which stops execution of the decorator chain if
access is denied. So make sure that decorators that need to be ran, like for setting up the OIP, are placed before the
security one, so the user doesn't experience any strange things because of this.
"""
from dlibrary.vectorworks import VectorworksSecurity, OnActivePluginEvent, ActivePluginEventEnum, OnActivePluginReset, \
    AbstractResetArgs, ActivePluginInfoPallet, ParameterWidget, StaticTextWidget, SeparatorWidget, ButtonWidget, \
    ActivePluginDoubleClickBehaviour, DoubleClickBehaviourEnum, ActivePluginFontStyleEnabled


# noinspection PyUnusedLocal
def reset(arg: int):
    """This is an example reset function, which will be executed on the reset event.
    """
    pass


@OnActivePluginEvent(event=ActivePluginEventEnum.VSO_ON_RESET, callback=reset)
def run():
    """Main function, with minimal plugin setup.

    You always need a main function, where you can do some stuff before the actual setup decorators run. What you do in
    it is up to you, though the need to do things before all setup is rarely needed.

    Even when your plugin isn't event-enabled, the reset event will always happen, so you will need to have at least
    the basic on-event decorator added to your main function, handling that reset event with the given callback. You
    can ignore the argument, but the function will need to expect it to avoid errors being thrown.
    """
    pass


# noinspection PyUnusedLocal
def minimal_reset(arg: str):
    """Example function for a minimal reset, when access is denied.
    """
    pass


@VectorworksSecurity(version='2017', user_ids='123ABC', on_version_denied=minimal_reset)
def secured_run():
    """You can secure your plugin with this decorator, by version and/or by user id's.

    This decorator also let you optionally set two functions, which will be ran when the criteria isn't met, and thus
    access is denied. In these callbacks, you can let the user know why he has no access to your plugin, and that he
    probably should close the drawing without saving to have no data loss. You could also execute some drawing routines
    so that something is being drawn, though not the exact thing then when he would have access. So these callbacks
    enable you to do the stuff that's minimal needed for the working of your plugin, but what this is, is up to you.

    ! Keep in mind that all decorators below this one will not be executed, as the chain will stop. So all decorators
    that need to happen, like OIP setup, must be defined before this one !
    """
    pass


@ActivePluginFontStyleEnabled()
def font_style_enabled_run():
    """Make your plugin font style aware with this decorator, so users can set font style through the VW font menus.
    """
    pass


# So a typical none-event-enabled plugin would have a main executing function that looks like this: --------------------

@ActivePluginFontStyleEnabled()
@VectorworksSecurity(version='2017', on_version_denied=minimal_reset)
@OnActivePluginEvent(event=ActivePluginEventEnum.VSO_ON_RESET, callback=reset)
def none_event_enabled_run():
    pass


# ----------------------------------------------------------------------------------------------------------------------
# From here on, all decorators requires your plugin to be event-enabled. All decorators above will still work though.
# ----------------------------------------------------------------------------------------------------------------------

# noinspection PyUnusedLocal
def reset_with_reset_args(reset_args: AbstractResetArgs):
    """This is an example reset function, which will be executed on the reset event.

    The reset args will depend on what triggered the reset. For example, when a parameter has been changed, you'll get
    ParameterChangeResetArgs, and within the name of the parameter that had been changed. This way, you can react in
    other ways, depending on what triggered the reset, or do some extra stuff, like checking parameter values, or
    setting default values, or doing some transformations etc....
    """
    pass


@OnActivePluginReset(callback=reset_with_reset_args)
def event_args_run():
    """If event-enabled, you can get reset args into your reset function by using this reset event decorator.

    Enabling reset args requires more Vectorworks setup, and it's more costly, so only use this if you really need the
    reset args, otherwise, you the standard on-event decorator, like described for none event-enabled plugins above.
    """
    pass


def on_button_click():
    """Example function which will be executed on a OIP button click.
    """
    pass


@ActivePluginInfoPallet(widgets=[
    ParameterWidget('PMyParameter1'),
    StaticTextWidget(''),
    SeparatorWidget('Group of parameters'),
    ParameterWidget('PMyParameter2'),
    ParameterWidget('PMyParameter3'),
    ButtonWidget('Settings...', on_button_click)
])
def custom_info_pallet_run():
    """You can have a custom info pallet, with the widgets you want, instead of the default all-parameters one.

    Using this decorator will setup a custom OIP, where all given widgets will be placed on in their defined order.
    Each widget can have custom visibility and enabling, and can have a click handler. Make your OIP as pretty as you
    want.
    """
    pass


@ActivePluginDoubleClickBehaviour(behaviour=DoubleClickBehaviourEnum.RESHAPE_MODE)
def double_click_behaviour_run():
    """You can set the double click behaviour to something else than the default for the plugin type.

    Sometimes you want something else happening on double-click on your plugin then the default action. You can set
    this with this decorator. For some path plugins, it would be the most valuable option to go into reshape mode, or
    if you want a custom event happening, you can.
    """
    pass


# So a typical event-enabled plugin would have a main executing function that looks like this: -------------------------

@ActivePluginFontStyleEnabled()
@ActivePluginInfoPallet(widgets=[
    ParameterWidget('PMyParameter1'),
    ButtonWidget('Settings...', on_button_click)])
@VectorworksSecurity(version='2017', on_version_denied=minimal_reset)
@OnActivePluginReset(callback=reset_with_reset_args)
def event_enabled_run():
    pass
