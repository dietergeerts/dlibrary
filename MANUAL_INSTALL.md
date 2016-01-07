VW DLibrary
========================================================================================================================

Common library for VW plug-ins.

## REMARK ##############################################################################################################

Please prefer to use the automatic install, which is way easier, though because of a bug in VW, the script in the 
install.vwx file needs te be ran first, which includes a pre-install step to prepare VW for the installation.

## MANUAL INSTALL ######################################################################################################

Only install if you have no or an older version of this library and the plugin needs this version.

**TIP**: The version number can always be found in the `__init__.py` file in the `dlibrary` folder.

To manually install this library in order for Vectorworks to use, follow these steps:
 
- Copy the `dlibrary` folder to a folder of your chose.
- Add that folder, where the `dlibrary` folder resides, to the Python Script Settings in Vectorworks.
- Restart Vectorworks.

If done right, Vectorworks will now pick up the library for your plugins to use.
