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


class CustomDoc(pydoc.Doc, metaclass=ABCMeta):
    """Formatter base class to enable customization of generated documentation.
    Based on pydoc.TextDoc. (Actually started from a copy of TextDoc.)
    """

    def __init__(self):
        self.__indent_sequence = self._get_indent_sequence('    ')
        self.__newline_sequence = self._get_newline_sequence('\n')

    # ------------------------------------------- text formatting utilities

    _repr_instance = pydoc.TextRepr()
    repr = _repr_instance.repr

    def bold(self, text):
        """Format a string in bold by overstriking."""
        return ''.join(ch + '\b' + ch for ch in text)

    def indent(self, text, prefix='    '):
        """Indent text by prepending a given prefix to each line."""
        if not text: return ''
        lines = [prefix + line for line in text.split('\n')]
        if lines: lines[-1] = lines[-1].rstrip()
        return '\n'.join(lines)

    def section(self, title, contents):
        """Format a section with a given heading."""
        clean_contents = self.indent(contents).rstrip()
        return self.bold(title) + '\n' + clean_contents + '\n\n'

    # ---------------------------------------------- type-specific routines

    def formattree(self, tree, module, modname, parent=None, prefix='', first_level=True):
        """Render in text a class tree as returned by inspect.getclasstree()."""

        module_classes = [key for key, value
                          in inspect.getmembers(module, inspect.isclass)
                          if inspect.getmodule(value) is module]
        result = ''
        for entry in tree:
            clazz = None
            if type(entry) is type(()):
                clazz, bases = entry
                clazz_name = pydoc.classname(clazz, modname)
                if clazz_name in module_classes:
                    clazz_name = self._create_anchor_link(clazz_name, clazz_name)
                result += prefix + clazz_name
                if bases and bases != (parent,):
                    parents = (pydoc.classname(c, modname) for c in bases)
                    result += '(%s)' % ', '.join(parents)
                result += self.__newline_sequence
            elif type(entry) is type([]):
                result += self.formattree(entry, module, modname, clazz, prefix + self.__indent_sequence, False)
        return result

    def docmodule(self, module, *ignored):
        """Produce text documentation for a given module object."""

        name = module.__name__
        synopsis, description = pydoc.splitdoc(pydoc.getdoc(module))
        docs = self.section(
            self._create_name_section_header('NAME', name),
            self._create_name_section_content(name + (synopsis and ' - %s' % synopsis), name, synopsis))

        all = getattr(module, '__all__', None)
        docloc = self.getdocloc(module)
        if docloc is not None:
            docs += self.section('MODULE REFERENCE', docloc + """

The following documentation is automatically generated from the Python
source files.  It may be incomplete, incorrect or include features that
are considered implementation detail and may vary between Python
implementations.  When in doubt, consult the module reference at the
location listed above.
""")

        if description:
            docs += self.section('DESCRIPTION', description)

        classes = []
        for key, value in inspect.getmembers(module, inspect.isclass):
            # if __all__ exists, believe it. Otherwise use old heuristic.
            if (all is not None
                or (inspect.getmodule(value) or module) is module):
                if pydoc.visiblename(key, all, module):
                    classes.append((key, value))
        funcs = []
        for key, value in inspect.getmembers(module, inspect.isroutine):
            # if __all__ exists, believe it.  Otherwise use old heuristic.
            if (all is not None or
                    inspect.isbuiltin(value) or inspect.getmodule(value) is module):
                if pydoc.visiblename(key, all, module):
                    funcs.append((key, value))
        data = []
        for key, value in inspect.getmembers(module, pydoc.isdata):
            if pydoc.visiblename(key, all, module):
                data.append((key, value))

        modpkgs = []
        modpkgs_names = set()
        if hasattr(module, '__path__'):
            for importer, modname, ispkg in pkgutil.iter_modules(module.__path__):
                modpkgs_names.add(modname)
                if ispkg:
                    modpkgs.append(modname + ' (package)')
                else:
                    modpkgs.append(modname)

            modpkgs.sort()
            docs += self.section('PACKAGE CONTENTS', '\n'.join(modpkgs))

        # Detect submodules as sometimes created by C extensions
        submodules = []
        for key, value in inspect.getmembers(module, inspect.ismodule):
            if value.__name__.startswith(name + '.') and key not in modpkgs_names:
                submodules.append(key)
        if submodules:
            submodules.sort()
            docs += self.section('SUBMODULES', '\n'.join(submodules))

        if classes:
            contents = [self.formattree(inspect.getclasstree([value for key, value in classes], 1), module, name)]
            for key, value in classes:
                contents.append(self.document(value, key, name))
            docs += self.section('CLASSES', '\n'.join(contents))

        if funcs:
            contents = []
            for key, value in funcs:
                contents.append(self.document(value, key, name))
            docs += self.section('FUNCTIONS', '\n'.join(contents))

        if data:
            contents = []
            for key, value in data:
                contents.append(self.docother(value, key, name, maxlen=70))
            docs += self.section('DATA', '\n'.join(contents))

        if hasattr(module, '__version__'):
            version = str(module.__version__)
            if version[:11] == '$' + 'Revision: ' and version[-1:] == '$':
                version = version[11:-1].strip()
            docs += self.section('VERSION', version)
        if hasattr(module, '__date__'):
            docs += self.section('DATE', str(module.__date__))
        if hasattr(module, '__author__'):
            docs += self.section('AUTHOR', str(module.__author__))
        if hasattr(module, '__credits__'):
            docs += self.section('CREDITS', str(module.__credits__))
        try:
            file = inspect.getabsfile(module)
        except TypeError:
            file = '(built-in)'
        docs += self.section('FILE', file)
        return docs

    def docclass(self, clazz, name=None, mod=None, *ignored):
        """Produce text documentation for a given class object."""

        real_name = clazz.__name__
        name = name or real_name
        bases = clazz.__bases__

        def makename(c, m=clazz.__module__):
            return pydoc.classname(c, m)

        title = self._create_anchor(real_name)
        title += ('class ' + self.bold(real_name)) if name == real_name else (self.bold(name) + ' = class ' + real_name)
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
            def __init__(self):
                self.needone = 0
            def maybe(self):
                if self.needone:
                    push('-' * 70)
                self.needone = 1
        hr = HorizontalRule()

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
        return title + '\n' + self.indent(contents.rstrip(), ' |  ') + '\n'

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
            title = self.bold(realname)
        else:
            if (cl and realname in cl.__dict__ and
                        cl.__dict__[realname] is object):
                skipdocs = 1
            title = self.bold(name) + ' = ' + realname
        if inspect.isfunction(object):
            args, varargs, varkw, defaults, kwonlyargs, kwdefaults, ann = \
                inspect.getfullargspec(object)
            argspec = inspect.formatargspec(
                args, varargs, varkw, defaults, kwonlyargs, kwdefaults, ann,
                formatvalue=self.formatvalue,
                formatannotation=inspect.formatannotationrelativeto(object))
            if realname == '<lambda>':
                title = self.bold(name) + ' lambda '
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
            return decl + '\n' + (doc and self.indent(doc).rstrip() + '\n')

    def _docdescriptor(self, name, value, mod):
        results = []
        push = results.append

        if name:
            push(self.bold(name))
            push('\n')
        doc = pydoc.getdoc(value) or ''
        if doc:
            push(self.indent(doc))
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
        line = (name and self.bold(name) + ' = ' or '') + repr
        if doc is not None:
            line += '\n' + self.indent(str(doc))
        return line

    @abstractmethod
    def _get_indent_sequence(self, default_indent_sequence: str) -> str:
        pass

    @abstractmethod
    def _get_newline_sequence(self, default_newline_sequence: str) -> str:
        pass

    @abstractmethod
    def _create_anchor(self, anchor: str) -> str:
        pass

    @abstractmethod
    def _create_anchor_link(self, link: str, anchor: str) -> str:
        pass

    @abstractmethod
    def _create_name_section_header(self, default_header: str, name: str) -> str:
        pass

    @abstractmethod
    def _create_name_section_content(self, default_content: str, name: str, synopsis: str) -> str:
        pass


class MarkdownDoc(CustomDoc, metaclass=ABCMeta):
    """Formatter base class to produce markdown documentation.
    """

    underline = "*" * 40

    def _get_indent_sequence(self, default_indent_sequence: str) -> str:
        return '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'

    def _get_newline_sequence(self, default_newline_sequence: str) -> str:
        return '  \n'

    def _create_anchor(self, anchor: str) -> str:
        return '<a name="%s"></a>' % anchor

    def _create_anchor_link(self, link: str, anchor: str) -> str:
        return '[%s](#%s)' % (link, anchor)

    def process_docstring(self, obj):
        """Get the docstring and turn it into a list."""
        docstring = pydoc.getdoc(obj)
        if docstring:
            return docstring + "\n\n"
        return ""

    def process_class_name(self, name, bases, module):
        """Format the class's name and bases."""
        title = "## %s%s" % (self._create_anchor(name), self.bold(name))
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

    def docclass(self, clazz, name=None, mod=None, *ignored):
        """Produce text documentation for the class object clazz."""

        # the overall document, as a line-delimited list
        document = []

        # get the object's actual name, defaulting to the passed in name
        name = name or clazz.__name__

        # get the object's bases
        bases = clazz.__bases__

        # get the object's module
        mod = clazz.__module__

        # get the object's MRO
        mro = [pydoc.classname(base, mod) for base in inspect.getmro(clazz)]

        # get the object's classname, which should be printed
        classtitle = self.process_class_name(name, bases, mod)
        document.append(classtitle)
        document.append(self.underline)

        # get the object's docstring, which should be printed
        docstring = self.process_docstring(clazz)
        document.append(docstring)

        # get all the attributes of the class
        attrs = []
        for name, kind, classname, value in pydoc.classify_class_attrs(clazz):
            if pydoc.visiblename(name):
                attrs.append((name, kind, classname, value))

        # sort them into categories
        data, descriptors, methods = [], [], []
        for attr in attrs:
            if attr[1] == "data" and not attr[0].startswith("_"):
                data.append(attr)
            elif attr[1] == "data descriptor" and not attr[0].startswith("_"):
                descriptors.append(attr)
            elif "method" in attr[1] and not attr[2] is builtins.object:
                methods.append(attr)

        if data:
            # start the data section
            document.append(self.process_subsection(self.bold("data")))
            document.append(self.underline)

            # process your attributes
            for name, kind, classname, value in data:
                if hasattr(value, '__call__') or inspect.isdatadescriptor(value):
                    doc = pydoc.getdoc(value)
                else:
                    doc = None
                document.append(self.docother(getattr(clazz, name), name, mod, maxlen=70, doc=doc) + '\n')

        if descriptors:
            # start the descriptors section
            document.append(self.process_subsection(self.bold("descriptors")))
            document.append(self.underline)

            # process your descriptors
            for name, kind, classname, value in descriptors:
                document.append(self._docdescriptor(name, value, mod))

        if methods:
            # start the methods section
            document.append(self.process_subsection(self.bold("methods")))
            document.append(self.underline)

            # process your methods
            for name, kind, classname, value in methods:
                document.append(self.document(getattr(clazz, name), name, mod, clazz))

        return "\n".join(document)

    def bold(self, text):
        """ Formats text as bold in markdown. """
        if text.startswith('_') and text.endswith('_'):
            return "__\%s\__" % text
        elif text.startswith('_'):
            return "__\%s__" % text
        elif text.endswith('_'):
            return "__%s\__" % text
        else:
            return "__%s__" % text

    def indent(self, text, prefix=''):
        """Indent text by prepending a given prefix to each line."""
        return text

    def section(self, title, contents):
        """Format a section with a given heading."""
        clean_contents = self.indent(contents).rstrip()
        return '# %s\n\n%s\n\n' % (self.bold(title), clean_contents)

    def docroutine(self, object, name=None, mod=None, cl=None):
        """Produce text documentation for a function or method object."""
        realname = object.__name__
        name = name or realname
        note = ''
        skipdocs = 0
        if inspect.ismethod(object):
            object = object.__func__
        if name == realname:
            title = self.bold(realname)
        else:
            if (cl and realname in cl.__dict__ and cl.__dict__[realname] is object):
                skipdocs = 1
            title = self.bold(name) + ' = ' + realname
        if inspect.isfunction(object):
            args, varargs, varkw, defaults, kwonlyargs, kwdefaults, ann = inspect.getfullargspec(object)
            argspec = inspect.formatargspec(
                args, varargs, varkw, defaults, kwonlyargs, kwdefaults, ann,
                formatvalue=self.formatvalue,
                formatannotation=inspect.formatannotationrelativeto(object))
            if realname == '<lambda>':
                title = self.bold(name) + ' lambda '
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
            return decl + '\n' + (doc and self.indent(doc).rstrip() + '\n')

    def docother(self, object, name=None, mod=None, parent=None, maxlen=None, doc=None):
        """Produce text documentation for a data object."""
        line = "#### " + object.__name__ + "\n"
        line += super().docother(object, name, mod, parent, maxlen, doc)
        return line + "\n"

    def _docdescriptor(self, name, value, mod):
        results = ""
        if name: results += "#### " + self.bold(name) + "\n"
        doc = pydoc.getdoc(value) or ""
        if doc: results += doc + "\n"
        return results


class BitbucketMarkdownDoc(MarkdownDoc):

    def _get_indent_sequence(self, default_indent_sequence: str) -> str:
        return '........'  # Using html space sequence doesn't work!

    def _create_anchor(self, anchor: str):
        return ''  # The standard markdown html anchor doesn't work!

    def _create_anchor_link(self, link: str, anchor: str):
        return super()._create_anchor_link(link, 'markdown-header-%s' % anchor.replace(' ', '-').lower())
