"""To be able to customize documentation with pydoc and to have other types of formatter classes.

The MarkdownDoc formatter is based on the one from Patrick Laban and Geremy Condra,
found on http://code.activestate.com/recipes/576733-autogenerate-api-docs-in-markdown.
"""
from abc import abstractmethod, ABCMeta
from collections import deque
import pkgutil

import pydoc
import inspect
import builtins


class AbstractCustomDoc(pydoc.Doc, metaclass=ABCMeta):
    """Formatter base class to enable customization of generated documentation.
    Based on pydoc.TextDoc. (Actually started from a copy of TextDoc.)
    """

    @staticmethod
    @abstractmethod
    def _get_indent() -> str:
        pass

    @staticmethod
    @abstractmethod
    def _get_tree_indent() -> str:
        pass

    @staticmethod
    @abstractmethod
    def _get_newline() -> str:
        pass

    @staticmethod
    @abstractmethod
    def _get_rule() -> str:
        pass

    @staticmethod
    @abstractmethod
    def _escape(text: str) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _clean(text: str) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _bold(text: str) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _anchor_link(link: str, anchor: str) -> str:
        pass

    @abstractmethod
    def _indent(self, text: str) -> str:
        pass

    @abstractmethod
    def _heading(self, text: str, level: int=1) -> str:
        pass

    @abstractmethod
    def _section(self, title: str, contents: str) -> str:
        pass

    @abstractmethod
    def _formattree(self, tree, module, modname, clazz_names, parent=None, level=0):
        """Render a class tree as returned by inspect.getclasstree().
        """
        pass

    @abstractmethod
    def _create_module_name_heading(self, module_name: str) -> str:
        pass

    @abstractmethod
    def _create_module_name_content(self, module_name: str, synopsis: str) -> str:
        pass

    @abstractmethod
    def _create_module_doc_loc_heading(self, doc_loc: str) -> str:
        pass

    @abstractmethod
    def _create_module_doc_loc_content(self, doc_loc: str) -> str:
        pass

    @abstractmethod
    def _create_module_description_heading(self) -> str:
        pass

    @abstractmethod
    def _create_module_description_content(self, description: str) -> str:
        pass

    @abstractmethod
    def _create_module_packages_heading(self) -> str:
        pass

    @abstractmethod
    def _create_module_packages_content(self, packages: list) -> str:
        pass

    @abstractmethod
    def _create_module_submodules_heading(self) -> str:
        pass

    @abstractmethod
    def _create_module_submodules_content(self, submodules: list) -> str:
        pass

    @abstractmethod
    def _create_module_classes_heading(self) -> str:
        pass

    @abstractmethod
    def _create_module_classes_content(self, module, name: str, classes: list) -> str:
        pass

    @abstractmethod
    def _create_module_functions_heading(self) -> str:
        pass

    @abstractmethod
    def _create_module_functions_content(self, name: str, functions: list) -> str:
        pass

    @abstractmethod
    def _create_module_data_heading(self) -> str:
        pass

    @abstractmethod
    def _create_module_data_content(self, name: str, data: list) -> str:
        pass

    @abstractmethod
    def _create_module_version_heading(self) -> str:
        pass

    @abstractmethod
    def _create_module_version_content(self, module) -> str:
        pass

    @abstractmethod
    def _create_module_date_heading(self) -> str:
        pass

    @abstractmethod
    def _create_module_date_content(self, module) -> str:
        pass

    @abstractmethod
    def _create_module_author_heading(self) -> str:
        pass

    @abstractmethod
    def _create_module_author_content(self, module) -> str:
        pass

    @abstractmethod
    def _create_module_credits_heading(self) -> str:
        pass

    @abstractmethod
    def _create_module_credits_content(self, module) -> str:
        pass

    @abstractmethod
    def _create_module_file_heading(self) -> str:
        pass

    @abstractmethod
    def _create_module_file_content(self, module) -> str:
        pass

    # noinspection PyUnusedLocal
    def docmodule(self, module, name=None, *args) -> str:
        """Produce text documentation for a given module object.
        """
        name = name or module.__name__
        synopsis, description = pydoc.splitdoc(pydoc.getdoc(module))
        synopsis = self._clean(self._escape(synopsis))
        description = self._clean(self._escape(description))
        doc_loc = self.getdocloc(module)
        packages, package_names = self.__get_module_packages(module)
        submodules = self.__get_module_submodules(module, name, package_names)
        classes = self.__get_module_classes(module)
        functions = self.__get_module_functions(module)
        data = self.__get_module_data(module)

        return '%s%s%s%s%s%s%s%s%s%s%s%s%s' % (
            self._section(
                self._create_module_name_heading(name),
                self._create_module_name_content(name, synopsis)),
            self._section(
                self._create_module_doc_loc_heading(doc_loc),
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

    def docclass(self, clazz, name=None, mod=None, *args):
        """Produce text documentation for a given class object.
        """

        real_name = clazz.__name__
        name = name or real_name
        bases = clazz.__bases__

        def makename(c, m=clazz.__module__):
            return pydoc.classname(c, m)

        title = self._create_anchor(real_name)
        title += ('class ' + self._bold(real_name)) if name == real_name else (self._bold(name) + ' = class ' + real_name)
        if bases:
            parents = map(makename, bases)
            title += '(%s)' % ', '.join(parents)

        doc = pydoc.getdoc(clazz)
        contents = doc and [doc + '\n'] or []
        push = contents.append

        # List the mro, if non-trivial.
        mro = deque(inspect.getmro(clazz))
        if len(mro) > 2:
            push("Method resolution order:")
            for base in mro:
                push('    ' + makename(base))
            push('')

        # Cute little class to pump out a horizontal rule between sections.
        class HorizontalRule:

            def __init__(self, horizontal_rule: str):
                self.__need_one = 0
                self._horizontal_rule = horizontal_rule

            def maybe(self):
                if self.__need_one:
                    push(self._horizontal_rule)
                self.__need_one = 1

        hr = HorizontalRule(self._get_rule())

        def spill(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                hr.maybe()
                push(msg)
                for name, kind, homecls, value in ok:
                    try:
                        value = getattr(clazz, name)
                    except Exception:
                        # Some descriptors may meet a failure in their __get__.
                        # (bug #1785)
                        push(self._docdescriptor(name, value, mod))
                    else:
                        push(self.document(value,
                                           name, mod, clazz))
            return attrs

        def spilldescriptors(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                hr.maybe()
                push(msg)
                for name, kind, homecls, value in ok:
                    push(self._docdescriptor(name, value, mod))
            return attrs

        def spilldata(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                hr.maybe()
                push(msg)
                for name, kind, homecls, value in ok:
                    if callable(value) or inspect.isdatadescriptor(value):
                        doc = pydoc.getdoc(value)
                    else:
                        doc = None
                    push(self.docother(getattr(clazz, name),
                                       name, mod, maxlen=70, doc=doc) + '\n')
            return attrs

        attrs = [(name, kind, cls, value)
                 for name, kind, cls, value in pydoc.classify_class_attrs(clazz)
                 if pydoc.visiblename(name, obj=clazz)]

        while attrs:
            if mro:
                thisclass = mro.popleft()
            else:
                thisclass = attrs[0][2]
            attrs, inherited = pydoc._split_list(attrs, lambda t: t[2] is thisclass)

            if thisclass is builtins.object:
                attrs = inherited
                continue
            elif thisclass is clazz:
                tag = "defined here"
            else:
                tag = "inherited from %s" % pydoc.classname(thisclass,
                                                            clazz.__module__)

            # Sort attrs by name.
            attrs.sort()

            # Pump out the attrs, segregated by kind.
            attrs = spill("Methods %s:\n" % tag, attrs,
                          lambda t: t[1] == 'method')
            attrs = spill("Class methods %s:\n" % tag, attrs,
                          lambda t: t[1] == 'class method')
            attrs = spill("Static methods %s:\n" % tag, attrs,
                          lambda t: t[1] == 'static method')
            attrs = spilldescriptors("Data descriptors %s:\n" % tag, attrs,
                                     lambda t: t[1] == 'data descriptor')
            attrs = spilldata("Data and other attributes %s:\n" % tag, attrs,
                              lambda t: t[1] == 'data')
            assert attrs == []
            attrs = inherited

        contents = '\n'.join(contents)
        if not contents:
            return title + '\n'
        return title + '\n' + self._indent(contents.rstrip()) + '\n'
        # return title + '\n' + self._indent(contents.rstrip(), ' |  ') + '\n'


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
            title = self._bold(realname)
        else:
            if (cl and realname in cl.__dict__ and
                        cl.__dict__[realname] is object):
                skipdocs = 1
            title = self._bold(name) + ' = ' + realname
        if inspect.isfunction(object):
            args, varargs, varkw, defaults, kwonlyargs, kwdefaults, ann = \
                inspect.getfullargspec(object)
            argspec = inspect.formatargspec(
                args, varargs, varkw, defaults, kwonlyargs, kwdefaults, ann,
                formatvalue=self.formatvalue,
                formatannotation=inspect.formatannotationrelativeto(object))
            if realname == '<lambda>':
                title = self._bold(name) + ' lambda '
                # XXX lambda's won't usually have func_annotations['return']
                # since the syntax doesn't support but it is possible.
                # So removing parentheses isn't truly safe.
                argspec = argspec[1:-1] # remove parentheses
        else:
            argspec = '(...)'
        decl = title + argspec + note

        if skipdocs:
            return decl + '\n'
        else:
            doc = pydoc.getdoc(object) or ''
            return decl + '\n' + (doc and self._indent(doc).rstrip() + '\n')

    def _docdescriptor(self, name, value, mod):
        results = []
        push = results.append

        if name:
            push(self._bold(name))
            push('\n')
        doc = pydoc.getdoc(value) or ''
        if doc:
            push(self._indent(doc))
            push('\n')
        return ''.join(results)

    def docproperty(self, object, name=None, mod=None, cl=None):
        """Produce text documentation for a property."""
        return self._docdescriptor(name, object, mod)

    def docdata(self, object, name=None, mod=None, cl=None):
        """Produce text documentation for a data descriptor."""
        return self._docdescriptor(name, object, mod)

    def docother(self, object, name=None, mod=None, parent=None, maxlen=None, doc=None):
        """Produce text documentation for a data object."""
        repr = self.repr(object)
        if maxlen:
            line = (name and name + ' = ' or '') + repr
            chop = maxlen - len(line)
            if chop < 0: repr = repr[:chop] + '...'
        line = (name and self._bold(name) + ' = ' or '') + repr
        if doc is not None:
            line += '\n' + self._indent(str(doc))
        return line

    def _create_anchor(self, anchor: str) -> str:
        return ''


class TextDoc(AbstractCustomDoc):
    """Formatter class to produce text documentation.
    """

    @staticmethod
    def _get_indent() -> str:
        return '    '

    @staticmethod
    def _get_tree_indent() -> str:
        return '    '

    @staticmethod
    def _get_newline() -> str:
        return '\n'

    @staticmethod
    def _get_rule() -> str:
        return '-' * 80 + '\n'

    @staticmethod
    def _escape(text: str) -> str:
        return text

    @staticmethod
    def _clean(text: str) -> str:
        return text.strip()

    @staticmethod
    def _bold(text: str) -> str:
        return ''.join(ch + '\b' + ch for ch in text)  # Using over-striking.

    @staticmethod
    def _anchor_link(link: str, anchor: str) -> str:
        return ''  # Plain text can't have anchor links!

    def _indent(self, text: str) -> str:
        # Indent text by prepending the indent sequence to each line.
        return self._get_newline().join([self._get_indent() + line for line in (text or '').split(self._get_newline())])

    def _heading(self, text: str, level: int=1) -> str:
        return self._bold('%s %s' % ('-' * level, text.upper()))

    def _section(self, title: str, contents: str) -> str:
        return self._heading(title) + self._get_newline() + self._indent(contents) + self._get_newline() * 2

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
                    clazz_name = self._anchor_link(clazz_name, clazz_name)
                result += self._get_tree_indent() * level + clazz_name
                if bases and bases != (parent,):
                    parents = (pydoc.classname(c, modname) for c in bases)
                    result += '(%s)' % ', '.join(parents)
                result += self._get_newline()
            elif type(entry) is type([]):
                result += self._formattree(entry, module, modname, clazz_names, clazz, level + 1)
        return result

    def _create_module_name_heading(self, module_name: str) -> str:
        return 'NAME'

    def _create_module_name_content(self, module_name: str, synopsis: str) -> str:
        return module_name + (synopsis and ' - %s' % synopsis)

    def _create_module_doc_loc_heading(self, doc_loc: str) -> str:
        return 'MODULE REFERENCE'

    def _create_module_doc_loc_content(self, doc_loc: str) -> str:
        return doc_loc + """
The following documentation is automatically generated from the Python
source files. It may be incomplete, incorrect or include features that
are considered implementation detail and may vary between Python
implementations. When in doubt, consult the module reference at the
location listed above.
"""

    def _create_module_description_heading(self) -> str:
        return 'DESCRIPTION'

    def _create_module_description_content(self, description: str) -> str:
        return description

    def _create_module_packages_heading(self) -> str:
        return 'PACKAGE CONTENTS'

    def _create_module_packages_content(self, packages: list) -> str:
        return self._get_newline().join(packages)

    def _create_module_submodules_heading(self) -> str:
        return 'SUBMODULES'

    def _create_module_submodules_content(self, submodules: list) -> str:
        return self._get_newline().join(submodules)

    def _create_module_classes_heading(self) -> str:
        return 'CLASSES'

    def _create_module_classes_content(self, module, name: str, classes: list) -> str:
        contents = [self._formattree(inspect.getclasstree([value for key, value in classes], 1),
                                     module, name, [item[0] for item in classes])]
        for key, value in classes:
            contents.append(self._get_rule())
            contents.append(self.document(value, key, name))
        return self._get_newline().join(contents)

    def _create_module_functions_heading(self) -> str:
        return 'FUNCTIONS'

    def _create_module_functions_content(self, name: str, functions: list) -> str:
        return self._get_newline().join([self.document(value, key, name) for key, value in functions])

    def _create_module_data_heading(self) -> str:
        return 'DATA'

    def _create_module_data_content(self, name: str, data: list) -> str:
        return self._get_newline().join([self.docother(value, key, name, maxlen=80) for key, value in data])

    def _create_module_version_heading(self) -> str:
        return 'VERSION'

    def _create_module_version_content(self, module) -> str:
        version = str(module.__version__)
        if version[:11] == '$' + 'Revision: ' and version[-1:] == '$':
            version = version[11:-1].strip()
        return version

    def _create_module_date_heading(self) -> str:
        return 'DATE'

    def _create_module_date_content(self, module) -> str:
        return str(module.__date__)

    def _create_module_author_heading(self) -> str:
        return 'AUTHOR'

    def _create_module_author_content(self, module) -> str:
        return str(module.__author__)

    def _create_module_credits_heading(self) -> str:
        return 'CREDITS'

    def _create_module_credits_content(self, module) -> str:
        return str(module.__credits__)

    def _create_module_file_heading(self) -> str:
        return 'FILE'

    def _create_module_file_content(self, module) -> str:
        try:
            file = inspect.getabsfile(module)
        except TypeError:
            file = '(built-in)'
        return file


class MarkdownDoc(TextDoc):
    """Formatter class to produce markdown documentation.
    """

    @staticmethod
    def _get_indent() -> str:
        return ''  # We don'tuse indents in markdown.

    @staticmethod
    def _get_tree_indent() -> str:
        return '&nbsp;' * 8  # Simulate indents so the tree displays correctly.

    @staticmethod
    def _get_newline() -> str:
        return '  \n'  # Markdown needs two extra spaces to see it as an actual new line.

    @staticmethod
    def _escape(text: str) -> str:
        return text.replace('*', '\*').replace('_', '\_') if text else ''

    @staticmethod
    def _bold(text: str) -> str:
        return '**%s**' % text  # We use **, as __ has special meaning to Python in names!

    @staticmethod
    def _anchor_link(link: str, anchor: str) -> str:
        return '[%s](#%s)' % (link, anchor)

    def _heading(self, text: str, level: int=1) -> str:
        """Format the text as heading.
        """
        return '%s %s' % ('#' * level, text)










    def _create_anchor(self, anchor: str) -> str:
        return '<a name="%s"></a>' % anchor


    def process_docstring(self, obj):
        """Get the docstring and turn it into a list."""
        docstring = pydoc.getdoc(obj)
        if docstring:
            return docstring + "\n\n"
        return ""

    def process_class_name(self, name, bases, module):
        """Format the class's name and bases."""
        title = "## %s%s" % (self._create_anchor(name), self._bold(name))
        if bases:
            # get the names of each of the bases
            base_titles = [pydoc.classname(base, module) for base in bases]
            # if its not just object
            if len(base_titles) > 1:
                # append the list to the title
                title += "(%s)" % ", ".join(base_titles)
        return title

    def process_subsection(self, name):
        """format the subsection as a header"""
        return "### " + name

    # def docclass(self, clazz, name=None, mod=None, *ignored):
    #     """Produce text documentation for a giveen class object.
    #     """
    #
    #     # the overall document, as a line-delimited list
    #     document = []
    #
    #     # get the object's actual name, defaulting to the passed in name
    #     name = name or clazz.__name__
    #
    #     # get the object's bases
    #     bases = clazz.__bases__
    #
    #     # get the object's module
    #     mod = clazz.__module__
    #
    #     # get the object's MRO
    #     mro = [pydoc.classname(base, mod) for base in inspect.getmro(clazz)]
    #
    #     # get the object's classname, which should be printed
    #     classtitle = self.process_class_name(name, bases, mod)
    #     document.append(classtitle)
    #
    #     # get the object's docstring, which should be printed
    #     docstring = self.process_docstring(clazz)
    #     document.append(docstring)
    #
    #     # get all the attributes of the class
    #     attrs = []
    #     for name, kind, classname, value in pydoc.classify_class_attrs(clazz):
    #         if pydoc.visiblename(name):
    #             attrs.append((name, kind, classname, value))
    #
    #     # sort them into categories
    #     data, descriptors, methods = [], [], []
    #     for attr in attrs:
    #         if attr[1] == "data" and not attr[0].startswith("_"):
    #             data.append(attr)
    #         elif attr[1] == "data descriptor" and not attr[0].startswith("_"):
    #             descriptors.append(attr)
    #         elif "method" in attr[1] and not attr[2] is builtins.object:
    #             methods.append(attr)
    #
    #     if data:
    #         # start the data section
    #         document.append(self.process_subsection(self._bold("data")))
    #
    #         # process your attributes
    #         for name, kind, classname, value in data:
    #             if hasattr(value, '__call__') or inspect.isdatadescriptor(value):
    #                 doc = pydoc.getdoc(value)
    #             else:
    #                 doc = None
    #             document.append(self.docother(getattr(clazz, name), name, mod, maxlen=70, doc=doc) + '\n')
    #
    #     if descriptors:
    #         # start the descriptors section
    #         document.append(self.process_subsection(self._bold("descriptors")))
    #
    #         # process your descriptors
    #         for name, kind, classname, value in descriptors:
    #             document.append(self._docdescriptor(name, value, mod))
    #
    #     if methods:
    #         # start the methods section
    #         document.append(self.process_subsection(self._bold("methods")))
    #
    #         # process your methods
    #         for name, kind, classname, value in methods:
    #             document.append(self.document(getattr(clazz, name), name, mod, clazz))
    #
    #     return "\n".join(document)

    def docroutine(self, object, name=None, mod=None, cl=None):
        """Produce text documentation for a function or method object."""
        realname = object.__name__
        name = name or realname
        note = ''
        skipdocs = 0
        if inspect.ismethod(object):
            object = object.__func__
        if name == realname:
            title = self._bold(realname)
        else:
            if (cl and realname in cl.__dict__ and cl.__dict__[realname] is object):
                skipdocs = 1
            title = self._bold(name) + ' = ' + realname
        if inspect.isfunction(object):
            args, varargs, varkw, defaults, kwonlyargs, kwdefaults, ann = inspect.getfullargspec(object)
            argspec = inspect.formatargspec(
                args, varargs, varkw, defaults, kwonlyargs, kwdefaults, ann,
                formatvalue=self.formatvalue,
                formatannotation=inspect.formatannotationrelativeto(object))
            if realname == '<lambda>':
                title = self._bold(name) + ' lambda '
                # XXX lambda's won't usually have func_annotations['return']
                # since the syntax doesn't support but it is possible.
                # So removing parentheses isn't truly safe.
                argspec = argspec[1:-1]  # remove parentheses
        else:
            argspec = '(...)'
        decl = "#### " + "def " + title + argspec + ':' + '\n' + note

        if skipdocs:
            return decl + '\n'
        else:
            doc = pydoc.getdoc(object) or ''
            return decl + '\n' + (doc and self._indent(doc).rstrip() + '\n')

    def docother(self, object, name=None, mod=None, parent=None, maxlen=None, doc=None):
        """Produce text documentation for a data object."""
        line = "#### " + object.__name__ + "\n"
        line += super().docother(object, name, mod, parent, maxlen, doc)
        return line + "\n"

    def _docdescriptor(self, name, value, mod):
        results = ""
        if name: results += "#### " + self._bold(name) + "\n"
        doc = pydoc.getdoc(value) or ""
        if doc: results += doc + "\n"
        return results


class BitbucketMarkdownDoc(MarkdownDoc):

    @staticmethod
    def _get_tree_indent() -> str:
        return '.' * 8  # Html spaces doesn't work for Bitbucket!

    @staticmethod
    def _anchor_link(link: str, anchor: str) -> str:
        # Bitbucket markdown doesn't support normal html anchor links, so we'll use header links!
        return MarkdownDoc._anchor_link(link, 'markdown-header-%s' % anchor.replace(' ', '-').lower())







    def _create_anchor(self, anchor: str):
        return ''  # The standard markdown html anchor doesn't work!

