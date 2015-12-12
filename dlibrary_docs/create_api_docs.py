import os
import pkgutil
import pydoc
import shutil

import dlibrary
from dlibrary_docs.customdoc import DLibraryDoc


# SETTINGS #############################################################################################################
# Make sure the output path references to the api docs folder of the DLibrary wiki! (API) ##############################
# Best to check out the wiki next to this repo, so that the docs will be directly build there, ready for commit. #######

api_docs_path = os.path.abspath(os.path.join('..', '..', 'DLibrary wiki', 'API', dlibrary.__version__.split('.')[0]))


# CLEAN API DOCS #######################################################################################################

def clean_api_docs():
    shutil.rmtree(api_docs_path) if os.path.exists(api_docs_path) else None
    os.mkdir(api_docs_path)


# WRITE API DOCS #######################################################################################################

def write_api_module(module, module_name: str):
    with open(os.path.join(api_docs_path, '%s.md' % module_name), 'w', encoding='utf-8') as file:
        file.write(DLibraryDoc().docmodule(module))


def write_api_docs():
    for importer, module_name, is_package in pkgutil.walk_packages(dlibrary.__path__, '%s.' % dlibrary.__name__):
        if 'libs' not in module_name:  # We don't document libs!
            module, module_name = pydoc.resolve(module_name)
            write_api_module(module, '.'.join(module_name.split('.')[1:]))  # Removing `dlibrary.` from module name!


# CREATE DOCS ##########################################################################################################

clean_api_docs()
write_api_docs()
