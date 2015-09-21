import os
import re
import shutil
from tkinter import filedialog, Tk
import urllib.request
from xml.etree import ElementTree
import sys
import vs

# This installation file can be used for your own plugin. It contains several possible steps you can include. This will
# make it easier for your users to install. To add certain steps/functionality, just (un)comment them at the end.
# An install script must go at the top level of your .zip file in order for Vectorworks to pick it up. For more
# information about install files, see: http://developer.vectorworks.net/index.php/VS:Implementing_Installation_Script


# SOME COMMON METHODS, AS WE CAN'T RELY ON DLIBRARY YET ################################################################
# ----------------------------------------------------------------------------------------------------------------------

major, minor, maintenance, platform = vs.GetVersion()
if platform == 1:
    sys.argv = ['']  # This is needed to make Tkinter happy on mac!


def ask_for_folder(initial_folder: str, message: str) -> str:

    def correct_windows_path(path: str) -> str:
        return path.replace('/', '\\') if os.name == 'nt' else path

    Tk().withdraw()  # To hide the tkinter root window!
    return correct_windows_path(
        filedialog.askdirectory(**{'initialdir': initial_folder, 'mustexist': True, 'title': message}))


def get_folder_path(folder_id: int) -> str:
    """
    Patrick Stanford <patstanford@coviana.com> on the VectorScript Discussion List:
    Since Mac OS 10, as they're rewritten it using UNIX kernel, the mac uses Posix natively.
    Since VW predates that, the old calls use HFS paths and need to be converted for newer APIs.
    You can ask VW to do the conversion, as simply replacing the characters are not enough (Posix uses volume mounting
    instead of drive names). This can be done through vs.ConvertHSF2PosixPath().
    """

    folder_path = vs.GetFolderPath(folder_id)
    if platform == 1:
        _, folder_path = vs.ConvertHSF2PosixPath(folder_path)
    return folder_path


# SET DESTINATION FOLDER ###############################################################################################
# By default, VW will copy all plugin files into the users' plugin folder. This is not always desired. For example when
# more than one user will use your plugin, the office can place them on a network drive and point each VW installation
# to that drive in order for VW to pick up the plugin and be able to use it. Including this step will enable the user to
# select a custom folder so that the files will be copied there, or tell that he already did this, to delete the files
# from the users' plugin folder.
# ----------------------------------------------------------------------------------------------------------------------

def set_destination_folder_for(plugin_folder_name: str):

    def ask_where_to_install() -> int:
        return vs.AlertQuestion(
            'Do you want to install this plugin in your user folder?',
            'If more than one user will use this plugin, you can install it on your network drive once for all.',
            1, 'Yes', 'No, I already placed it on my network', 'No, let me choose a custom folder', '')

    def install_in_user_folder():
        pass

    def install_in_custom_folder():
        user_plugin_folder = get_folder_path(-2)
        directory_path = ask_for_folder(user_plugin_folder, 'Please select the install directory. '
                                                            'Cancelling will install in your user folder.')
        if directory_path != '':  # '' means cancel was chosen!
            if os.path.exists(os.path.join(directory_path, plugin_folder_name)):
                shutil.rmtree(os.path.join(directory_path, plugin_folder_name))
            shutil.move(os.path.join(user_plugin_folder, plugin_folder_name), directory_path)
            vs.AlrtDialog('Don\'t forget to Let Vectorworks know about your custom folder!')

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
            raise
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

    vs.AlrtDialog('This plugin requires the \'dlibrary\' library, version ' + required_version + '. We would like to '
                  'install or update it. Please select its parent directory or the one where we can install it in the '
                  'next dialog. Cancel that dialog to manually install the library.')

    directory_path = ask_for_folder('', 'Please select the directory for dlibrary, make sure VW doesn\'t scan this '
                                        'folder. We need write access to the folder for the installation to succeed!')

    if directory_path != '':  # '' means cancel was chosen!
        if os.path.exists(os.path.join(directory_path, 'dlibrary')):
            if update_dlibrary_needed(directory_path):
                update_dlibrary(directory_path)
        else:
            install_dlibrary(directory_path)
        update_python_search_path(directory_path)
    else:
        vs.AlrtDialog('Don\'t forget to manually install `dlibrary`. It can be found at: '
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

set_destination_folder_for('MyPluginName')
update_to_or_install_dlibrary_version('2015.0.1')
add_plugins_to_workspaces({'Menus': {'MyMenu': ['MyPluginName']}})  # NOT WORKING YET!
