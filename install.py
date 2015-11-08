import os
import re
import shutil
import urllib.request
from xml.etree import ElementTree

import vs


# This installation file can be used for your own plugin. It contains several possible steps you can include. This will
# make it easier for your users to install. To add certain steps/functionality, just (un)comment them at the end.
# An install script must go at the top level of your .zip file in order for Vectorworks to pick it up. For more
# information about install files, see: http://developer.vectorworks.net/index.php/VS:Implementing_Installation_Script


# SOME COMMON METHODS, AS WE CAN'T RELY ON DLIBRARY YET ################################################################
# ----------------------------------------------------------------------------------------------------------------------

def get_os_independent_path(path: str) -> str:
    """
    Patrick Stanford <patstanford@coviana.com> on the VectorScript Discussion List:
    Since Mac OS 10, as they're rewritten it using UNIX kernel, the mac uses Posix natively.
    Since VW predates that, the old calls use HFS paths and need to be converted for newer APIs.
    You can ask VW to do the conversion, as simply replacing the characters are not enough (Posix uses volume mounting
    instead of drive names). This can be done through vs.ConvertHSF2PosixPath().
    """
    major, minor, maintenance, platform = vs.GetVersion()
    if platform == 1:
        succeeded, path = vs.ConvertHSF2PosixPath(path)
    return path


def get_folder(initial_folder: str, message: str) -> str:
    closed_with, chosen_folder = vs.GetFolder(message)
    return get_os_independent_path(chosen_folder) if closed_with == 0 else initial_folder


def get_folder_path(folder_id: int) -> str:
    return get_os_independent_path(vs.GetFolderPath(folder_id))


# SET DESTINATION FOLDER ###############################################################################################
# VW initial installation step is to copy the plugin files to the users' plugin folder. This is not always desired.
# For example when more than one user will use your plugin, the office can place them on a network drive and point each
# VW installation to that drive in order for VW to pick up the plugin and be able to use it. Including this step will
# enable the user to select a custom folder so that the files will be copied there, or tell that he already did this,
# to delete the files from the users' plugin folder.
# ----------------------------------------------------------------------------------------------------------------------

def choose_custom_folder_for(plugin_folder_name: str):

    def ask_where_to_install() -> int:
        return vs.AlertQuestion(
            'Vectorworks installed the plugin in your user folder, is this ok?', '',
            1, 'Yes', 'No, it\'s already installed elsewhere', 'No, I want to choose a folder', '')

    def install_in_user_folder():
        pass  # Standard VW behaviour.

    def install_in_custom_folder():
        user_plugin_folder = get_folder_path(-2)
        directory_path = get_folder(user_plugin_folder, 'Please select the installation folder.')
        if directory_path != user_plugin_folder:  # Only if another folder was chosen, or not cancelled!
            if os.path.exists(os.path.join(directory_path, plugin_folder_name)):
                shutil.rmtree(os.path.join(directory_path, plugin_folder_name))
            shutil.move(os.path.join(user_plugin_folder, plugin_folder_name), directory_path)
            vs.AlrtDialog('Don\'t forget to tell Vectorworks about your custom folder!')

    def already_installed_in_custom_folder():
        user_plugin_folder = get_folder_path(-2)
        shutil.rmtree(os.path.join(user_plugin_folder, plugin_folder_name))

    {
        1: install_in_user_folder,
        2: install_in_custom_folder,
        0: already_installed_in_custom_folder
    }.get(ask_where_to_install())()


# DLIBRARY INSTALL #####################################################################################################
# When your plugin uses this library, it also needs to be installed and added to the Python search paths. Off course we
# need to check the version that could be already installed, and only install if a newer version is required.
# ----------------------------------------------------------------------------------------------------------------------

def update_to_or_install_dlibrary_version(required_version: str):

    def update_dlibrary_needed(libraries_folder: str) -> bool:
        with open(os.path.join(libraries_folder, 'dlibrary', '__init__.py')) as package_file:
            pkg_info = package_file.read()

        version_info = [int(info) for info in re.search(r'__version__ = \'.+?\'', pkg_info).group(0)[15:-1].split('.')]
        version_info_needed = [int(info) for info in required_version.split('.')]

        # Version info like [2015, 0, 0]
        if version_info[0] > version_info_needed[0]:
            return False
        elif version_info[0] < version_info_needed[0]:
            return True
        elif version_info[1] > version_info_needed[1]:
            return False
        elif version_info[1] < version_info_needed[1]:
            return True
        elif version_info[2] > version_info_needed[2]:
            return False
        elif version_info[2] < version_info_needed[2]:
            return True
        else:
            return False

    def update_dlibrary(libraries_folder: str):
        shutil.rmtree(os.path.join(libraries_folder, 'dlibrary'))
        install_dlibrary(libraries_folder)

    def install_dlibrary(libraries_folder: str):
        dlibrary_url = 'https://bitbucket.org/dieterdworks/vw-dlibrary/get/v' + required_version + '.zip'
        dlibrary_zip = os.path.join(libraries_folder, 'dlibrary_repo.zip')
        # noinspection PyBroadException
        try:
            # vs.ProgressDlgOpen('DLibrary installation', False)
            # vs.ProgressDlgSetMeter('Installing dlibrary v' + required_version + '...')
            vs.AlrtDialog('We\'ll start installing `dlibrary`. This can take a while.')
            urllib.request.urlretrieve(dlibrary_url, dlibrary_zip)
            urllib.request.urlretrieve(dlibrary_url, dlibrary_zip)
            shutil.unpack_archive(dlibrary_zip, libraries_folder)
            unzipped_dir = get_unzipped_dir(libraries_folder)
            shutil.move(os.path.join(libraries_folder, unzipped_dir, 'dlibrary'), libraries_folder)
        except:
            vs.AlrtDialog('The library \'dlibrary\' couldn\'t be downloaded. Please install it manually.')
        finally:
            unzipped_dir = get_unzipped_dir(libraries_folder)
            if unzipped_dir != '':
                shutil.rmtree(os.path.join(libraries_folder, unzipped_dir))
            if os.path.exists(dlibrary_zip):
                os.remove(dlibrary_zip)
            # vs.ProgressDlgClose()

    def get_unzipped_dir(libraries_folder: str):
        unzipped_repo_folders = [f for f in os.listdir(libraries_folder) if f.startswith('dieterdworks-vw-dlibrary')]
        return unzipped_repo_folders[0] if len(unzipped_repo_folders) > 0 else ''

    def update_python_search_path(libraries_folder: str):
        search_path = vs.PythonGetSearchPath()
        library_path = os.path.join(libraries_folder, '')
        if library_path not in search_path.split(';'):
            vs.PythonSetSearchPath('%s%s' % (search_path, library_path))

    directory_path = get_folder('', 'This plugin depends on the \'dlibrary\' library, version '
                                    + required_version + '. Please select its parent directory.')

    if directory_path != '':  # If a folder was chosen!
        if os.path.exists(os.path.join(directory_path, 'dlibrary')):
            if update_dlibrary_needed(directory_path):
                update_dlibrary(directory_path)
        else:
            install_dlibrary(directory_path)
        update_python_search_path(directory_path)
    else:
        vs.AlrtDialog('You\'ll have to manually install `dlibrary`. It can be found at: '
                      'https://bitbucket.org/dieterdworks/vw-dlibrary/get/v' + required_version + '.zip')


# ADD TO WORKSPACES ####################################################################################################
# In most cases, we also want to add our plugins to the users' workspace, so he doesn't have to go through that. This
# will get him started immediately.
# ----------------------------------------------------------------------------------------------------------------------
# REMARK: This doesn't work, yet. We'll just show a message to the user he has to do it until we find out how to do it!
# ----------------------------------------------------------------------------------------------------------------------

def add_plugins_to_workspaces(plugins_structure: dict):

    def get_or_create_and_get_user_workspace_path():
        user_workspace_path = get_folder_path(-4)
        if not os.path.exists(os.path.join(user_workspace_path)):
            os.makedirs(os.path.join(user_workspace_path))
        return user_workspace_path

    def get_all_user_workspaces():
        user_workspace_path = get_or_create_and_get_user_workspace_path()
        return [os.path.join(user_workspace_path, ws) for ws in os.listdir(user_workspace_path) if ws.endswith('.vww')]

    def add_plugins_to_workspace(workspace_path: str):
        workspace_tree = ElementTree.parse(workspace_path)
        for _, _ in plugins_structure.items():
            pass
        workspace_tree.write(workspace_path)

    for workspace in get_all_user_workspaces():
        add_plugins_to_workspace(workspace)

    vs.AlrtDialog(
        'After you restarted Vectorworks, you just have to add the plugin(s) to your workspace to be able to use them.')


# INSTALLATION STEPS ###################################################################################################

# VW always copies the plugin folder, which is inside the zip file, to the users' plugin folder = initial install step!
choose_custom_folder_for('MyPluginName')
update_to_or_install_dlibrary_version('2015.0.1')
add_plugins_to_workspaces({'Menus': {'MyMenu': ['MyPluginName']}})  # NOT WORKING YET!
