"""Executable module to create all auto-generated docs for the current version of DLibrary.
"""
import inspect
import os
import pkgutil
import pydoc
import shutil

import dlibrary

DIST_PATH = os.path.abspath(os.path.join('.', 'dist'))
VERSION_PATH = os.path.join(DIST_PATH, dlibrary.__version__.split('.')[0])
API_DOCS_PATH = os.path.join(VERSION_PATH, 'api')
EXAMPLES_PATH = os.path.join(VERSION_PATH, 'examples')


class FileUtil(object):

    @staticmethod
    def write_file(filename: str, content: str):
        os.makedirs(os.path.sep.join(filename.split(os.path.sep)[:-1]), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)


class TextUtil(object):

    @staticmethod
    def first_line(text: str) -> str:
        return text.splitlines()[0] if text is not None else None

    @staticmethod
    def first_word(text: str) -> str:
        return TextUtil.first_line(text).split(' ')[0] if text is not None else None

    @staticmethod
    def strip(text: str) -> str:
        return text.strip() if text is not None else None


class Markdown(object):

    @staticmethod
    def emphasis(text: str) -> str:
        return '*%s*' % text if text is not None else ''

    @staticmethod
    def strong(text: str) -> str:
        return '**%s**' % text if text is not None else ''

    @staticmethod
    def tag(tag: str, text: str) -> str:
        return '<%s>%s</%s>' % (tag, text, tag)

    @staticmethod
    def link(url: str, text: str=None) -> str:
        return '[%s](%s)' % (text or url, url)

    @staticmethod
    def newline() -> str:
        return '\n'

    @staticmethod
    def header(text: str, level: int=1) -> str:
        return '%s %s%s' % ('#' * level, text or '', Markdown.newline())

    @staticmethod
    def paragraph(text: str) -> str:
        return '%s%s' % (text or '', Markdown.newline())

    @staticmethod
    def blockquote(text: str) -> str:
        return '> ' + '> '.join(text.splitlines()) + Markdown.newline() if text is not None else ''

    @staticmethod
    def list_item(text: str) -> str:
        return '- %s%s' % (text or '', Markdown.newline())


class DLibraryMember(object):

    def __init__(self, member, name: str):
        self.__name = name
        self.__doc = TextUtil.strip(inspect.getdoc(member))
        self.__doc_excerpt = TextUtil.first_line(self.__doc)

    @property
    def name(self) -> str:
        return self.__name

    @property
    def doc_excerpt(self) -> str:
        return self.__doc_excerpt

    @property
    def doc(self) -> str:
        return self.__doc


class DLibraryModule(DLibraryMember):

    def __init__(self, module):
        super().__init__(module, module.__name__.replace('dlibrary.', ''))
        self.__pretty_name = self.name.replace('_', ' ').title()

        def in_module(obj) -> bool:
            return obj.__module__ == module.__name__

        all_classes = [cls for _, cls in inspect.getmembers(module, inspect.isclass)]
        self.__classes = [DLibraryClass(cls, self) for cls in all_classes if in_module(cls)]
        self.__enum_classes = [cls for cls in self.__classes if cls.is_enum]
        self.__singleton_classes = [cls for cls in self.__classes if cls.is_singleton]

    @property
    def pretty_name(self) -> str:
        return self.__pretty_name

    @property
    def all_classes(self) -> list:
        """
        :rtype: list[DLibraryClass]
        """
        return self.__classes

    @property
    def enum_classes(self) -> list:
        """
        :rtype: list[DLibraryClass]
        """
        return self.__enum_classes

    @property
    def singleton_classes(self) -> list:
        """
        :rtype: list[DLibraryClass]
        """
        return self.__singleton_classes


class DLibraryModuleMember(DLibraryMember):

    def __init__(self, member, name: str, module: DLibraryModule):
        super().__init__(member, name)
        self.__link = '%s/%s.md' % (module.name, self.name)
        self.__module = module

    @property
    def link(self):
        return self.__link

    @property
    def module(self) -> DLibraryModule:
        return self.__module


class DLibraryClass(DLibraryModuleMember):

    def __init__(self, cls, module: DLibraryModule):
        super().__init__(cls, cls.__name__, module)
        self.__category = TextUtil.first_word(inspect.getdoc(cls))
        self.__constants = [member for member in inspect.getmembers(cls) if member[0].isupper()]

    @property
    def is_enum(self) -> bool:
        return self.__category == 'Enum'

    @property
    def is_singleton(self) -> bool:
        return self.__category == 'Singleton'

    @property
    def constants(self) -> list:
        """
        :rtype: list[(str, str)]
        """
        return self.__constants


def clean_docs():
    shutil.rmtree(DIST_PATH) if os.path.exists(DIST_PATH) else None


def write_api_index(modules: list):
    """
    :type modules: list[DLibraryModule]
    """
    content = ''
    content += Markdown.header('DLibrary', 1)
    for module in modules:
        content += Markdown.header(module.pretty_name, 2)
        content += Markdown.blockquote(module.doc)
        for class_group in [module.enum_classes, module.singleton_classes]:
            content += Markdown.newline()
            for cls in class_group:
                content += Markdown.list_item('%s - %s' % (
                    Markdown.strong(Markdown.link(cls.link, cls.name)),
                    Markdown.tag('small', cls.doc_excerpt)))
            content += Markdown.newline()
    FileUtil.write_file(os.path.join(API_DOCS_PATH, 'index.md'), content)


def write_api_member(member: DLibraryModuleMember, content: str):
    wrapped = ''
    wrapped += Markdown.header(
        '%s \> %s \> %s' % (Markdown.link('../index.md', 'DLibrary'), member.module.pretty_name, member.name), 1)
    wrapped += Markdown.blockquote(member.doc)
    wrapped += content
    FileUtil.write_file(os.path.join(API_DOCS_PATH, member.module.name, '%s.md' % member.name), wrapped)


def write_api_class(cls: DLibraryClass):
    content = ''
    for constant in cls.constants:
        content += Markdown.list_item('%s = %s' % constant)
    write_api_member(cls, content)


def write_api_docs():
    modules = [DLibraryModule(pydoc.resolve(module_name)[0]) for importer, module_name, is_package
               in pkgutil.walk_packages(dlibrary.__path__, '%s.' % dlibrary.__name__)
               if 'libs' not in module_name]  # We don't document libs!
    write_api_index(modules)
    for module in modules:
        for cls in module.all_classes:
            write_api_class(cls)


def write_examples():
    examples_src = os.path.join('.', 'examples')
    for filename in os.listdir(examples_src):
        with open(os.path.join(examples_src, filename)) as src_file:
            with open(os.path.join(EXAMPLES_PATH, '%s.md' % filename), 'w', encoding='utf-8') as dst_file:
                dst_file.write('```\n#!python\n\n%s\n```' % src_file.read())


clean_docs()
write_api_docs()
# write_examples()
