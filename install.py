import os
import re
import shutil
import urllib.request

import vs

# DLIBRARY INSTALL FILE ################################################################################################
# You can use this installation file for your own plugins, just fill in the variables in the SETUP part. ###############
# An install script must go at the top level of your .zip file in order for Vectorworks to pick it up. For more ########
# information about install files, see: http://developer.vectorworks.net/index.php/VS:Implementing_Installation_Script #
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! #
# VW has a bug, when just started, some vs functions aren't available yet, like vs.GetFolder. To overcome this, the    #
# script in the install.vwx file has to be run first, and then the user have to install the plugin without restarting  #
# Vectorworks.                                                                                                         #
########################################################################################################################


# SETUP ################################################################################################################

plugin_name = 'MyPluginNameAndFolderNameInZipFile'
dlibrary_version = '2016.4.0'
include_choose_custom_install_folder = True
include_update_or_install_dlibrary = True


# SOME COMMON METHODS, AS WE CAN'T RELY ON DLIBRARY YET ################################################################

def get_os_independent_path(path: str) -> str:
    """
    Patrick Stanford <patstanford@coviana.com> on the VectorScript Discussion List:
    Since Mac OS 10, as they're rewritten it using UNIX kernel, the mac uses Posix natively.
    Since VW predates that, the old calls use HFS paths and need to be converted for newer APIs.
    You can ask VW to do the conversion, as simply replacing the characters are not enough (Posix uses volume mounting
    instead of drive names). This can be done through vs.ConvertHSF2PosixPath().
    """
    major, minor, maintenance, platform = vs.GetVersion()
    succeeded, path = vs.ConvertHSF2PosixPath(path) if platform == 1 else (False, path)
    return path


def get_folder(initial_folder: str, message: str) -> str:
    closed_with, chosen_folder = vs.GetFolder(message)
    return get_os_independent_path(chosen_folder) if closed_with == 0 else initial_folder


def get_user_plugin_folder_path() -> str:
    return get_os_independent_path(vs.GetFolderPath(-2))


# SET DESTINATION FOLDER ###############################################################################################

def choose_custom_install_folder(plugin_folder_name: str):

    def ask_where_to_install() -> int:
        return vs.AlertQuestion(
            'Vectorworks installed %s in your user folder, is this ok?' % plugin_name, '', 1, 'Yes',
            'No, it\'s already installed elsewhere, delete from user folder',
            'No, I want to choose a folder to copy %s to.' % plugin_name, '')

    def copy_to_custom_folder():
        user_plugin_folder = get_user_plugin_folder_path()
        custom_folder_path = get_folder(user_plugin_folder, 'Please select your custom installation folder.')
        if custom_folder_path != user_plugin_folder:  # Only if another folder was chosen, or not cancelled!
            custom_folder = os.path.join(custom_folder_path, plugin_folder_name)
            shutil.rmtree(custom_folder) if os.path.exists(custom_folder) else None
            shutil.move(os.path.join(user_plugin_folder, plugin_folder_name), custom_folder_path)
            vs.AlrtDialog('Don\'t forget to tell Vectorworks about your custom folder!')

    def delete_from_user_folder():
        shutil.rmtree(os.path.join(get_user_plugin_folder_path(), plugin_folder_name))

    {
        1: lambda : None,           # We don't need to do anything if the default is ok.
        2: copy_to_custom_folder,   # If user want to install in custom folder.
        0: delete_from_user_folder  # If user already installed the plugin somewhere.
    }.get(ask_where_to_install())()


# DLIBRARY INSTALL #####################################################################################################
# Update or install DLibrary and ad it to the Python search paths. Off course we need to check the version that could ##
# be already installed, and only install if a newer version is required. ###############################################

def update_or_install_dlibrary(required_version: str):

    class DLibraryProgressBar(object):

        def __init__(self, required_version: str):
            self.__required_version = required_version

        def start(self):
            vs.AlrtDialog('We\'ll start installing `dlibrary`. This can take a while.')
            vs.ProgressDlgOpen('DLibrary installation', False)
            vs.ProgressDlgSetMeter('Installing dlibrary v%s...' % self.__required_version)

        def report(self, block_nr, read_size, total_size):
            vs.ProgressDlgStart(98, total_size/read_size) if block_nr == 0 else None
            vs.ProgressDlgYield(1) if block_nr > 0 else None

        def end(self):
            vs.ProgressDlgClose()

    def get_unzipped_dir(libraries_folder: str):
        unzipped_repo_folders = [f for f in os.listdir(libraries_folder) if f.startswith('dieterdworks-vw-dlibrary')]
        return unzipped_repo_folders[0] if len(unzipped_repo_folders) > 0 else ''

    def install_dlibrary(libraries_folder: str):
        dlibrary_url = 'https://bitbucket.org/dieterdworks/vw-dlibrary/get/%s.zip' % required_version
        dlibrary_zip = os.path.join(libraries_folder, 'dlibrary_repo.zip')
        progress_bar = DLibraryProgressBar(required_version)
        # noinspection PyBroadException
        try:
            progress_bar.start()
            urllib.request.urlretrieve(dlibrary_url, dlibrary_zip, progress_bar.report)
            shutil.unpack_archive(dlibrary_zip, libraries_folder)
            unzipped_dir = get_unzipped_dir(libraries_folder)
            shutil.move(os.path.join(libraries_folder, unzipped_dir, 'dlibrary'), libraries_folder)
        except:
            vs.AlrtDialog('The library `dlibrary` couldn\'t be downloaded. Please install it manually.')
        finally:
            unzipped_dir = get_unzipped_dir(libraries_folder)
            shutil.rmtree(os.path.join(libraries_folder, unzipped_dir)) if unzipped_dir != '' else None
            os.remove(dlibrary_zip) if os.path.exists(dlibrary_zip) else None
            progress_bar.end()

    def update_dlibrary(libraries_folder: str):
        shutil.rmtree(os.path.join(libraries_folder, 'dlibrary'))
        install_dlibrary(libraries_folder)

    def update_dlibrary_needed(libraries_folder: str) -> bool:
        with open(os.path.join(libraries_folder, 'dlibrary', '__init__.py')) as package_file:
            pkg_info = package_file.read()

        version_info = [int(info) for info in re.search(r'__version__ = \'.+?\'', pkg_info).group(0)[15:-1].split('.')]
        version_info_needed = [int(info) for info in required_version.split('.')]

        # Version info like [2015, 0, 0]
        return False if version_info[0] > version_info_needed[0] else (
            True if version_info[0] < version_info_needed[0] else (
                False if version_info[1] > version_info_needed[1] else (
                    True if version_info[1] < version_info_needed[1] else (
                        False if version_info[2] > version_info_needed[2] else (
                            True if version_info[2] < version_info_needed[2] else False)))))

    def try_update(install_path: str):
        update_dlibrary(install_path) if update_dlibrary_needed(install_path) else None

    def update_or_install(install_path: str):
        update = os.path.exists(os.path.join(install_path, 'dlibrary'))
        try_update(install_path) if update else install_dlibrary(install_path)

    def update_python_search_path(libraries_folder: str):
        search_path = vs.PythonGetSearchPath()
        library_path = os.path.join(libraries_folder, '')
        if library_path not in search_path.split(';'):
            vs.PythonSetSearchPath('%s%s' % (search_path, library_path))

    # The alert dialog is here because this message in the title of the get folder modal isn't very clear!
    vs.AlrtDialog('%s depends on the `dlibrary` library, vesion %s. Please select '
                  'its parent folder in the next dialog.' % (plugin_name, required_version))
    dlibrary_path = get_folder('', '%s depends on the `dlibrary` library, vesion %s. Please select '
                                   'its parent folder.' % (plugin_name, required_version))
    # If a folder was chosen or not cancelled!
    if dlibrary_path != '':
        update_or_install(dlibrary_path)
        update_python_search_path(dlibrary_path)


# INSTALLATION STEPS ###################################################################################################
# VW always copies the plugin folder, which is inside the zip file, to the users' plugin folder = initial install step!#

choose_custom_install_folder(plugin_name) if include_choose_custom_install_folder else None
update_or_install_dlibrary(dlibrary_version) if include_update_or_install_dlibrary else None
