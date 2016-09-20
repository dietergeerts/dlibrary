"""Our own doc formatter class, to have our docs like we want/need them.

This is the old stuff used for the docs, though I'll keep it here as reference.
"""
from collections import deque
import pkgutil

import pydoc
import inspect


class DLibraryDoc(pydoc.Doc):
    """Formatter class to output DLibrary docs.
    """

    __tab = '.' * 8           # Html spaces doesn't work for Bitbucket markdown!
    __newline = '  \n'        # MD needs two extra spaces to see it as an actual new line.
    __rule = '-' * 80 + '\n'

    @classmethod
    def __heading(cls, text: str, level: int=1) -> str:
        return '%s %s%s' % ('#' * level, text, cls.__newline)

    @classmethod
    def __block_quote(cls, text: str) -> str:
        return cls.__newline.join(['> %s' % line for line in (text or '').split('\n')])

    @classmethod
    def __get_clazz_attributes(cls, clazz) -> list:
        return [(name, kind, clz, value)
                for name, kind, clz, value in pydoc.classify_class_attrs(clazz)
                if DLibraryDoc.__show_clazz_attribute(clazz, name, clz)]

    @classmethod
    def __show_clazz_attribute(cls, clazz, name: str, clz) -> bool:
        specials = ['__init__']
        return pydoc.visiblename(name, obj=clazz) and (
            (name in specials and clz == clazz) or not name.startswith('__'))

    @classmethod
    def __doc_class_mro(cls, clazz, mro: deque) -> str:
        mro = [base for base in mro][1:]  # First remove own class name, as we see that.
        return cls.__heading('\> ' + ' > '.join([pydoc.classname(base, clazz.__module__) for base in mro]), 3)

    def docproperty(self, prop, name=None, mod=None, cl=None) -> str:
        """Produces text documentation for a property.
        """
        return self.__heading(('%s `GET%s%s` `%s`' % (
            self.__bold(self.__escape(name)),
            '/SET' if prop.fset is not None else '',
            '/DEL' if prop.fdel is not None else '',
            pydoc.getdoc(prop))).rstrip(), 3)

    def docdata(self, data, name=None, mod=None, cl=None) -> str:
        """Produces text documentation for data.
        """
        return '- %s = %s' % (self.__bold(self.__escape(name)), data)







    @staticmethod
    def __escape(text: str) -> str:
        return text.replace('*', '\*').replace('_', '\_') if text else ''

    @staticmethod
    def __clean(text: str) -> str:
        return text.strip()

    @staticmethod
    def __bold(text: str) -> str:
        return '**%s**' % text  # We use **, as __ has special meaning to Python in names!

    @staticmethod
    def __header_link(link: str, anchor: str) -> str:
        # Bitbucket markdown doesn't support normal html anchor links, so we'll use header links!
        return '[%s](#%s)' % (link, 'markdown-header-%s' % anchor.replace(' ', '-').lower())

    def __indent(self, text: str) -> str:
        # Indent text by prepending the indent sequence to each line.
        return self.__newline.join([self.__tab + line for line in (text or '').split('\n')])

    def _section(self, title: str, contents: str, level: int=1) -> str:
        return '%s%s%s%s' % (self.__heading(title, level), self.__newline, contents, self.__newline * 2)

    def _formattree(self, tree, module, modname, clazz_names: list, parent=None, level=0):
        """Render in text a class tree as returned by inspect.getclasstree().
        """
        result = ''
        for entry in tree:
            clazz = None
            if type(entry) is type(()):
                clazz, bases = entry
                clazz_name = pydoc.classname(clazz, modname)
                if clazz_name in clazz_names:
                    clazz_name = self.__header_link(clazz_name, clazz_name)
                result += self.__tab * level + clazz_name
                if bases and bases != (parent,):
                    parents = (pydoc.classname(c, modname) for c in bases)
                    result += '(%s)' % ', '.join(parents)
                result += self.__newline
            elif type(entry) is type([]):
                result += self._formattree(entry, module, modname, clazz_names, clazz, level + 1)
        return result

    def _create_module_name_heading(self, module_name: str) -> str:
        return self.__bold('MODULE %s' % module_name)

    @staticmethod
    def _create_module_name_content(synopsis: str) -> str:
        return synopsis

    @staticmethod
    def _create_module_doc_loc_heading() -> str:
        return 'MODULE REFERENCE'

    @staticmethod
    def _create_module_doc_loc_content(doc_loc: str) -> str:
        return doc_loc + """
The following documentation is automatically generated from the Python
source files. It may be incomplete, incorrect or include features that
are considered implementation detail and may vary between Python
implementations. When in doubt, consult the module reference at the
location listed above.
"""

    @staticmethod
    def _create_module_description_heading() -> str:
        return 'DESCRIPTION'

    @staticmethod
    def _create_module_description_content(description: str) -> str:
        return description

    @staticmethod
    def _create_module_packages_heading() -> str:
        return 'PACKAGE CONTENTS'

    def _create_module_packages_content(self, packages: list) -> str:
        return self.__newline.join(packages)

    @staticmethod
    def _create_module_submodules_heading() -> str:
        return 'SUBMODULES'

    def _create_module_submodules_content(self, submodules: list) -> str:
        return self.__newline.join(submodules)

    @staticmethod
    def _create_module_classes_heading() -> str:
        return 'CLASSES'

    def _create_module_classes_content(self, module, name: str, classes: list) -> str:
        contents = [self._formattree(inspect.getclasstree([value for key, value in classes], 1),
                                     module, name, [item[0] for item in classes])]
        for key, value in classes:
            contents.append(self.__rule)
            contents.append(self.document(value, key, name, 2))
        return self.__newline.join(contents)

    @staticmethod
    def _create_module_functions_heading() -> str:
        return 'FUNCTIONS'

    def _create_module_functions_content(self, name: str, functions: list) -> str:
        return self.__newline.join([self.document(value, key, name) for key, value in functions])

    @staticmethod
    def _create_module_data_heading() -> str:
        return 'DATA'

    def _create_module_data_content(self, name: str, data: list) -> str:
        return self.__newline.join([self.docother(value, key, name, maxlen=80) for key, value in data])

    @staticmethod
    def _create_module_version_heading() -> str:
        return 'VERSION'

    @staticmethod
    def _create_module_version_content(module) -> str:
        version = str(module.__version__)
        if version[:11] == '$' + 'Revision: ' and version[-1:] == '$':
            version = version[11:-1].strip()
        return version

    @staticmethod
    def _create_module_date_heading() -> str:
        return 'DATE'

    @staticmethod
    def _create_module_date_content(module) -> str:
        return str(module.__date__)

    @staticmethod
    def _create_module_author_heading() -> str:
        return 'AUTHOR'

    @staticmethod
    def _create_module_author_content(module) -> str:
        return str(module.__author__)

    @staticmethod
    def _create_module_credits_heading() -> str:
        return 'CREDITS'

    @staticmethod
    def _create_module_credits_content(module) -> str:
        return str(module.__credits__)

    @staticmethod
    def _create_module_file_heading() -> str:
        return 'FILE'

    @staticmethod
    def _create_module_file_content(module) -> str:
        try:
            file = inspect.getabsfile(module)
        except TypeError:
            file = '(built-in)'
        return file

    # noinspection PyUnusedLocal
    def docmodule(self, module, name=None, *args) -> str:
        """Produce text documentation for a given module object.
        """
        name = name or module.__name__
        synopsis, description = pydoc.splitdoc(pydoc.getdoc(module))
        synopsis = self.__clean(self.__escape(synopsis))
        description = self.__clean(self.__escape(description))
        doc_loc = self.getdocloc(module)
        packages, package_names = self.__get_module_packages(module)
        submodules = self.__get_module_submodules(module, name, package_names)
        classes = self.__get_module_classes(module)
        functions = self.__get_module_functions(module)
        data = self.__get_module_data(module)

        return '%s%s%s%s%s%s%s%s%s%s%s%s%s' % (
            self._section(
                self._create_module_name_heading(name),
                self._create_module_name_content(synopsis)),
            self._section(
                self._create_module_doc_loc_heading(),
                self._create_module_doc_loc_content(doc_loc)) if doc_loc is not None else '',
            self._section(
                self._create_module_description_heading(),
                self._create_module_description_content(description)) if description else '',
            self._section(
                self._create_module_packages_heading(),
                self._create_module_packages_content(packages)) if packages else '',
            self._section(
                self._create_module_submodules_heading(),
                self._create_module_submodules_content(submodules)) if submodules else '',
            self._section(
                self._create_module_classes_heading(),
                self._create_module_classes_content(module, name, classes)) if classes else '',
            self._section(
                self._create_module_functions_heading(),
                self._create_module_functions_content(name, functions)) if functions else '',
            self._section(
                self._create_module_data_heading(),
                self._create_module_data_content(name, data)) if data else '',
            self._section(
                self._create_module_version_heading(),
                self._create_module_version_content(module)) if hasattr(module, '__version__') else '',
            self._section(
                self._create_module_date_heading(),
                self._create_module_date_content(module)) if hasattr(module, '__date__') else '',
            self._section(
                self._create_module_author_heading(),
                self._create_module_author_content(module)) if hasattr(module, '__author__') else '',
            self._section(
                self._create_module_credits_heading(),
                self._create_module_credits_content(module)) if hasattr(module, '__credits__') else '',
            self._section(
                self._create_module_file_heading(),
                self._create_module_file_content(module)))

    @staticmethod
    def __get_module_packages(module) -> (list, set):
        """Returns both the packages and the package names.
        """
        packages = []
        package_names = set()
        if hasattr(module, '__path__'):
            for importer, modname, is_package in pkgutil.iter_modules(module.__path__):
                package_names.add(modname)
                packages.append('%s (package)' % modname if is_package else modname)
            packages.sort()
        return packages, package_names

    @staticmethod
    def __get_module_submodules(module, name, package_names) -> list:
        """Detect submodules as sometimes created by C extensions!
        """
        submodules = []
        for key, value in inspect.getmembers(module, inspect.ismodule):
            if value.__name__.startswith(name + '.') and key not in package_names:
                submodules.append(key)
        submodules.sort()
        return submodules

    @staticmethod
    def __get_module_classes(module) -> list:
        all_things = getattr(module, '__all__', None)
        classes = []
        for key, value in inspect.getmembers(module, inspect.isclass):
            # if __all__ exists, believe it. Otherwise use old heuristic.
            if all_things is not None or (inspect.getmodule(value) or module) is module:
                if pydoc.visiblename(key, all_things, module):
                    classes.append((key, value))
        return classes

    @staticmethod
    def __get_module_functions(module) -> list:
        all_things = getattr(module, '__all__', None)
        functions = []
        for key, value in inspect.getmembers(module, inspect.isroutine):
            # if __all__ exists, believe it.  Otherwise use old heuristic.
            if all_things is not None or inspect.isbuiltin(value) or inspect.getmodule(value) is module:
                if pydoc.visiblename(key, all_things, module):
                    functions.append((key, value))
        return functions

    @staticmethod
    def __get_module_data(module) -> list:
        all_things = getattr(module, '__all__', None)
        data = []
        for key, value in inspect.getmembers(module, pydoc.isdata):
            if pydoc.visiblename(key, all_things, module):
                data.append((key, value))
        return data

    def _create_class_name_heading(self, clazz, name: str) -> str:
        name = self.__escape(name)
        real = self.__escape(clazz.__name__)
        bases = clazz.__bases__
        return '%s%s' % (
            ('class ' + self.__bold(real)) if name == real else (self.__bold(name) + ' = class ' + real),
            '(%s)' % ', '.join(map(lambda c, m=clazz.__module__: pydoc.classname(c, m), bases)) if bases else '')

    def _create_class_name_content(self, synopsis: str, description: str) -> str:
        return synopsis + (self.__newline if description else '') + description

    def docclass(self, clazz, name=None, mod=None, level=1, *args) -> str:
        """Produce text documentation for a given class object.
        """
        name = name or clazz.__name__
        synopsis, description = pydoc.splitdoc(pydoc.getdoc(clazz))
        synopsis = self.__clean(self.__escape(synopsis))
        description = self.__clean(self.__escape(description))
        mro = deque(inspect.getmro(clazz))
        attrs = self.__get_clazz_attributes(clazz)

        return '%s%s%s' % (
            self._section(
                self._create_class_name_heading(clazz, name),
                self._create_class_name_content(synopsis, description),
                level),
            # List the mro, if non-trivial.
            self.__doc_class_mro(clazz, mro) if len(mro) > 2 else '',
            self.__newline.join(
                [self.__docclass_attribute(clazz, mod, attr) for attr in attrs]))

    def _create_class_methods_content(self, clazz, mod, attribute) -> str:
        name = attribute[0]
        value = attribute[3]
        try:
            value = getattr(clazz, name)
        except Exception:
            # Some descriptors may meet a failure in their __get__. (bug #1785)
            return self._docdescriptor(name, value, mod) + self.__newline
        else:
            return self.document(value, name, mod, clazz) + self.__newline

    def _create_class_data_descriptors_content(self, clazz, mod, attribute) -> str:
        if isinstance(attribute[3], property):
            return self.docproperty(attribute[3], attribute[0], mod, clazz) + self.__newline
        name = attribute[0]
        value = attribute[3]
        return self._docdescriptor(name, value, mod) + self.__newline

    def _create_class_data_and_other_attributes_content(self, clazz, mod, attribute) -> str:
        return self.docdata(attribute[3], attribute[0], mod, clazz)

    def __docclass_attribute(self, clazz, mod, attribute) -> str:
        """Produces text documentation for given attributes for the clazz or an inherited class.
        """
        return {
            'method': self._create_class_methods_content,
            'class method': self._create_class_methods_content,
            'static method': self._create_class_methods_content,
            'data descriptor': self._create_class_data_descriptors_content,
            'data': self._create_class_data_and_other_attributes_content
        }.get(attribute[1])(clazz, mod, attribute)

    repr = pydoc.TextRepr().repr

    def formatvalue(self, object):
        """Format an argument default value as text."""
        return '=' + self.repr(object)

    def docroutine(self, object, name=None, mod=None, cl=None):
        """Produce text documentation for a function or method object."""
        realname = object.__name__
        name = name or realname
        note = ''
        skipdocs = 0
        if inspect.ismethod(object):
            imclass = object.__self__.__class__
            if cl:
                if imclass is not cl:
                    note = ' from ' + pydoc.classname(imclass, mod)
            else:
                if object.__self__ is not None:
                    note = ' method of %s instance' % pydoc.classname(
                        object.__self__.__class__, mod)
                else:
                    note = ' unbound %s method' % pydoc.classname(imclass,mod)
            object = object.__func__

        if name == realname:
            title = self.__bold(self.__escape(realname))
        else:
            if (cl and realname in cl.__dict__ and
                        cl.__dict__[realname] is object):
                skipdocs = 1
            title = self.__bold(name) + ' = ' + realname
        if inspect.isfunction(object):
            args, varargs, varkw, defaults, kwonlyargs, kwdefaults, ann = \
                inspect.getfullargspec(object)
            argspec = inspect.formatargspec(
                args, varargs, varkw, defaults, kwonlyargs, kwdefaults, ann,
                formatvalue=self.formatvalue,
                formatannotation=inspect.formatannotationrelativeto(object))
            if realname == '<lambda>':
                title = self.__bold(name) + ' lambda '
                # XXX lambda's won't usually have func_annotations['return']
                # since the syntax doesn't support but it is possible.
                # So removing parentheses isn't truly safe.
                argspec = argspec[1:-1] # remove parentheses
        else:
            argspec = '(...)'
        decl = self.__heading(title + argspec + note, 3)

        if skipdocs:
            return decl + self.__newline
        else:
            doc = pydoc.getdoc(object) or ''
            return '%s%s%s%s%s' % (
                self.__newline,
                decl,
                self.__newline,
                doc and self.__block_quote(self.__clean(self.__escape(doc))),
                self.__newline)

    def _docdescriptor(self, name, value, mod):
        results = []
        push = results.append

        if name:
            push(self.__bold(self.__escape(name)))
            push(self.__newline)
        doc = pydoc.getdoc(value) or ''
        if doc:
            push(self.__indent(doc))
            push(self.__newline)
        return ''.join(results)


    def docother(self, object, name=None, mod=None, parent=None, maxlen=None, doc=None):
        """Produce text documentation for a data object."""
        repr = self.repr(object)
        if maxlen:
            line = (name and self.__escape(name) + ' = ' or '') + repr
            chop = maxlen - len(line)
            if chop < 0: repr = repr[:chop] + '...'
        line = (name and self.__bold(self.__escape(name)) + ' = ' or '') + repr
        if doc is not None:
            line += self.__newline + self.__indent(str(doc))

        return line
