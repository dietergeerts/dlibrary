"""Executable module to create all auto-generated docs for the current version of DLibrary.
"""
import inspect
import os
import pkgutil
import pydoc
import re
import shutil
from abc import ABCMeta

import dlibrary


class FileUtil(object):

    @staticmethod
    def write_file(filename: str, content: str):
        os.makedirs(os.path.sep.join(filename.split(os.path.sep)[:-1]), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)


class TextUtil(object):

    @staticmethod
    def strip(text: str) -> str:
        return text.strip() if text else ''

    @staticmethod
    def first_line(text: str) -> str:
        return text.splitlines()[0] if text else ''

    @staticmethod
    def for_each_line(text: str, handler: callable) -> str:
        """:type handler: (str) -> str"""
        return '\n'.join(handler(l) for l in text.splitlines()) if text else ''


class MD(object):

    @staticmethod
    def escape(text: str) -> str:
        return text.replace('*', '\*').replace('_', '\_') if text else ''

    @staticmethod
    def emphasis(text: str) -> str:
        return re.sub(r'  \*', '*  ',
                      TextUtil.for_each_line(text, lambda t: '*%s*' % t if TextUtil.strip(t) else ''))

    @staticmethod
    def strong(text: str) -> str:
        return re.sub(r'  \*\*', '**  ',
                      TextUtil.for_each_line(text, lambda t: '**%s**' % t if TextUtil.strip(t) else ''))

    @staticmethod
    def tag(tag: str, text: str) -> str:
        return '<%s>%s</%s>' % (tag, text or '', tag)

    @staticmethod
    def link(url: str, text: str=None) -> str:
        return '[%s](%s)' % (text or url, url)

    @staticmethod
    def newline() -> str:
        return '  \n'

    @staticmethod
    def header(text: str, level: int=1) -> str:
        return '%s %s%s%s' % ('#' * level, text or '', MD.newline(), MD.newline())

    @staticmethod
    def paragraph(text: str) -> str:
        return '%s%s%s' % (text or '', MD.newline(), MD.newline())

    @staticmethod
    def blockquote(text: str) -> str:
        return '%s%s%s' % (TextUtil.for_each_line(text, lambda t: '> %s' % t), MD.newline(), MD.newline())

    @staticmethod
    def list_item(text: str) -> str:
        return '- %s%s' % (text or '', MD.newline())

    @staticmethod
    def ruler() -> str:
        return '\n---\n\n'


class DLMember(object, metaclass=ABCMeta):

    def __init__(self, name: str, member: object):
        self.__name = name
        self.__pretty_name = MD.tag('small', '.'.join(name.split('.')[:-1]) + '.') + name.split('.')[-1]
        docs = [TextUtil.strip(l) for l in TextUtil.strip(inspect.getdoc(member)).splitlines()]
        self.__doc_types = [l for l in docs if l.startswith((':type', ':rtype'))]
        self.__doc = self.__pretty_info([l for l in docs if l not in self.__doc_types])
        self.__doc_excerpt = TextUtil.first_line(self.__doc)

    @staticmethod
    def __pretty_info(docs: list) -> str:
        return re.sub(re.compile(r'\n(:[^ ])', re.MULTILINE), MD.newline() + r'\1', '\n'.join(docs))

    @property
    def name(self) -> str:
        return self.__name

    @property
    def pretty_name(self) -> str:
        return self.__pretty_name

    @property
    def doc_types(self) -> list:
        """:rtype: list[str]"""
        return self.__doc_types

    @property
    def doc(self) -> str:
        return self.__doc

    @property
    def doc_excerpt(self) -> str:
        return self.__doc_excerpt

    def generate_excerpt(self) -> str:
        return '%s - %s' % (MD.strong(self.name), self.doc_excerpt)


class DLConstant(DLMember):

    def __init__(self, name: str, member: object):
        super().__init__(name, member)
        self.__value = member

    @property
    def value(self) -> object:
        return self.__value

    def generate_excerpt(self) -> str:
        return '%s %s' % (MD.strong(self.name), MD.tag('small', '(%s)' % self.value))


class DLMethod(DLMember):

    def __init__(self, name: str, member: object):
        method = member if inspect.isfunction(member) else member.__func__
        super().__init__(name, method)
        self.__is_static_method = isinstance(member, staticmethod)
        self.__is_class_method = isinstance(member, classmethod)
        self.__is_constructor = self.name == '__init__'
        self.__is_method = inspect.isfunction(member) and not self.__is_constructor
        self.__signature = self.__update_signature_from_docs(inspect.signature(method), self.doc_types)

    @staticmethod
    def __update_signature_from_docs(sig: inspect.Signature, docs: list) -> inspect.Signature:
        """:type docs: list[str]"""
        rtype = next((l[8:] for l in docs if l.startswith(':rtype')), None)
        ptypes = {t[0]: t[1] for t in [p.split(': ') for p in [l[6:] for l in docs if l.startswith(':type')]]}
        parameters = [p.replace(annotation=ptypes.get(n, p.annotation)) for n, p in sig.parameters.items()]
        return sig.replace(parameters=parameters, return_annotation=rtype if rtype else sig.return_annotation)

    @property
    def is_static_method(self) -> bool:
        return self.__is_static_method

    @property
    def is_class_method(self) -> bool:
        return self.__is_class_method

    @property
    def is_constructor(self) -> bool:
        return self.__is_constructor

    @property
    def is_method(self) -> bool:
        return self.__is_method

    @property
    def signature(self) -> inspect.Signature:
        return self.__signature

    def generate_signature(self) -> str:
        return '%s%s' % (
            MD.strong(MD.escape(self.name)),
            str(self.signature).replace(':', ': ').replace('->', '`->`'))

    def generate_excerpt(self) -> str:
        return self.generate_signature()

    def generate_docs(self) -> str:
        return '%s%s%s' % (self.generate_signature(), MD.newline()*2, MD.blockquote(self.doc))


class DLProperty(DLMethod):

    def __init__(self, name: str, member: property):
        super().__init__(name, member.fget)
        self.__has_setter = member.fset is not None

    @property
    def has_setter(self) -> bool:
        return self.__has_setter

    def generate_excerpt(self) -> str:
        return '%s %s %s' % (
            MD.tag('small', '(get%s)' % ('/set' if self.has_setter else '')),
            re.sub(r'\(.*\)', '', super().generate_excerpt()),
            MD.tag('small', '-- %s' % self.doc_excerpt) if self.doc_excerpt else '')


class DLClass(DLMember):

    def __init__(self, name: str, member: object):
        super().__init__(name, member)
        self.__module = member.__module__
        self.__link = os.path.join(self.__module, '%s.md' % self.name) if 'dlibrary' in self.__module else ''
        self.__base_classes = [DLClass(m.__name__, m) for m in member.__bases__]
        members = [m for m in inspect.getmembers(member) if self.__is_visible(m[0])]
        methods = [DLMethod(m[0], m[1]) for m in members if self.__is_method(m[1])]
        self.__constants = [DLConstant(m[0], m[1]) for m in members if m[0].isupper()]
        self.__static_methods = [m for m in methods if m.is_static_method]
        self.__class_methods = [m for m in methods if m.is_class_method]
        self.__constructors = [m for m in methods if m.is_constructor]
        self.__properties = [DLProperty(m[0], m[1]) for m in members if isinstance(m[1], property)]
        self.__methods = [m for m in methods if m.is_method]

    @staticmethod
    def __is_visible(name: str) -> bool:
        return pydoc.visiblename(name) and name != '__call__'

    @staticmethod
    def __is_method(member: object) -> bool:
        return inspect.isfunction(member) or isinstance(member, (staticmethod, classmethod))

    @property
    def module(self) -> str:
        return self.__module

    @property
    def link(self) -> str:
        return self.__link

    @property
    def base_classes(self) -> list:
        """:rtype: list[DLClass]"""
        return self.__base_classes

    @property
    def constants(self) -> list:
        """:rtype: list[DLConstant]"""
        return self.__constants

    @property
    def static_methods(self) -> list:
        """:rtype: list[DLMethod]"""
        return self.__static_methods

    @property
    def class_methods(self) -> list:
        """:rtype: list[DLMethod]"""
        return self.__class_methods

    @property
    def constructors(self) -> list:
        """:rtype: list[DLMethod]"""
        return self.__constructors

    @property
    def properties(self) -> list:
        """:rtype: list[DLProperty]"""
        return self.__properties

    @property
    def methods(self) -> list:
        """:rtype: list[DLMethod]"""
        return self.__methods

    def generate(self, path: str):
        FileUtil.write_file(os.path.join(path, '%s.md' % self.name), self.generate_docs())

    def generate_excerpt(self) -> str:
        return '%s %s' % (
            MD.strong(MD.link(self.link, self.name) if self.link else self.name),
            MD.tag('small', self.doc_excerpt))

    def generate_docs(self) -> str:
        return '%s'*9 % (
            MD.header('%s%s' % (MD.tag('small', self.module + '.'), self.name), 1),
            MD.blockquote(MD.strong(self.doc)),
            self.generate_docs_for_members('Base classes', self.base_classes).replace('](', '](..%s' % os.path.sep),
            self.generate_docs_for_members('Constants', self.constants),
            self.generate_docs_for_methods('Static methods', self.static_methods),
            self.generate_docs_for_methods('Class methods', self.class_methods),
            self.generate_docs_for_methods('Constructor', self.constructors),
            self.generate_docs_for_members('Properties', self.properties),
            self.generate_docs_for_methods('Methods', self.methods))

    def generate_docs_for_members(self, name: str, items: list) -> str:
        """:type items: list[DLMember]"""
        return self.__generate_docs_for_section(name, ''.join(MD.list_item(i.generate_excerpt()) for i in items))

    def generate_docs_for_methods(self, name: str, methods: list) -> str:
        """:type methods: list[DLMethod]"""
        return self.__generate_docs_for_section(name, ''.join(m.generate_docs() for m in methods))

    @staticmethod
    def __generate_docs_for_section(name: str, content: str) -> str:
        return '%s%s%s' % (MD.header(name, 2), content, MD.newline()) if content else ''


class DLModule(DLMember):

    def __init__(self, name: str, module: object):
        super().__init__(name, module)
        self.__classes = [DLClass(m[0], m[1]) for m in inspect.getmembers(module, inspect.isclass)]
        self.__classes = [cls for cls in self.__classes if cls.module == self.name]

    @property
    def classes(self) -> list:
        """":rtype: list[DLClass]"""
        return self.__classes

    def generate(self, path: str):
        [c.generate(os.path.join(path, self.name)) for c in self.classes]

    def generate_index(self) -> str:
        return '%s'*4 % (
            MD.header(self.pretty_name, 2),
            MD.blockquote(self.doc),
            MD.newline().join(MD.list_item(c.generate_excerpt()) for c in self.classes),
            MD.newline())


class ApiDocs(object):

    def __init__(self):
        self.__modules = [
            DLModule(name, pydoc.resolve(name)[0])
            for _, name, _ in pkgutil.walk_packages(dlibrary.__path__, '%s.' % dlibrary.__name__)
            if 'libs' not in name]  # We don't document libs!

    @property
    def modules(self) -> list:
        """:rtype: list[DLModule]"""
        return self.__modules

    def generate(self, path: str):
        FileUtil.write_file(os.path.join(path, 'index.md'), self.generate_index())
        [m.generate(path) for m in self.modules]

    def generate_index(self) -> str:
        return '%s'*7 % (
            MD.header('dlibrary', 1),
            MD.blockquote(MD.strong(TextUtil.first_line(TextUtil.strip(inspect.getdoc(dlibrary))))),
            MD.list_item('%s %s' % (MD.strong('Author:'), dlibrary.__author__)),
            MD.list_item('%s %s' % (MD.strong('Version:'), dlibrary.__version__)),
            MD.list_item('%s %s' % (MD.strong('License:'), dlibrary.__license__)),
            MD.newline(),
            ''.join('%s%s' % (MD.ruler(), m.generate_index()) for m in self.modules))


class ExampleDocs(object):

    def generate(self, path: str):
        examples_src = os.path.join('.', 'examples')
        for filename in os.listdir(examples_src):
            with open(os.path.join(examples_src, filename)) as src:
                FileUtil.write_file(os.path.join(path, '%s.md' % filename), '```\n#!python\n\n%s\n```' % src.read())


# Setup paths.
DIST_PATH = os.path.abspath(os.path.join('.', 'dist'))
VERSION_PATH = os.path.join(DIST_PATH, dlibrary.__version__.split('.')[0])
API_DOCS_PATH = os.path.join(VERSION_PATH, 'api')
EXAMPLES_PATH = os.path.join(VERSION_PATH, 'examples')

# Clean dist directory.
shutil.rmtree(DIST_PATH) if os.path.exists(DIST_PATH) else None

# Write api docs.
ApiDocs().generate(API_DOCS_PATH)

# Write example docs.
ExampleDocs().generate(EXAMPLES_PATH)
