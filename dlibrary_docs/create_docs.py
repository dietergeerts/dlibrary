import os
import pkgutil
import pydoc
import shutil

import dlibrary
from dlibrary_docs.customdoc import DLibraryDoc


# SETTINGS #############################################################################################################
# Make sure the output path references to the api docs folder of the DLibrary wiki! (API) ##############################
# Best to check out the wiki next to this repo, so that the docs will be directly build there, ready for commit. #######

wiki_path = os.path.abspath(os.path.join('..', '..', 'DLibrary wiki'))
api_docs_path = os.path.abspath(os.path.join(wiki_path, 'API', dlibrary.__version__.split('.')[0]))
examples_path = os.path.abspath(os.path.join(wiki_path, 'examples', dlibrary.__version__.split('.')[0]))


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


# CLEAN EXAMPLES #######################################################################################################

def clean_examples():
    shutil.rmtree(examples_path) if os.path.exists(examples_path) else None
    os.mkdir(examples_path)


# WRITE EXAMPLES #######################################################################################################

def write_examples():
    examples_src = os.path.join('.', 'examples')
    for filename in os.listdir(examples_src):
        with open(os.path.join(examples_src, filename)) as src_file:
            with open(os.path.join(examples_path, '%s.md' % filename), 'w', encoding='utf-8') as dst_file:
                dst_file.write('```\n#!python\n\n%s\n```' % src_file.read())


# CREATE DOCS ##########################################################################################################

clean_api_docs()
write_api_docs()
clean_examples()
write_examples()
