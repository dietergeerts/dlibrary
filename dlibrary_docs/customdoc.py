"""To be able to customize documentation with pydoc and to have other types of formatter classes.

The MarkdownDoc formatter is based on the one from Patrick Laban and Geremy Condra,
found on http://code.activestate.com/recipes/576733-autogenerate-api-docs-in-markdown.
"""
from collections import deque
import pkgutil

import pydoc
import inspect
import builtins


class CustomDoc(pydoc.Doc):
    """Formatter base class to enable customization of generated documentation.
    Based on pydoc.TextDoc. (Actually started from a copy of TextDoc.)
    """

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

    def formattree(self, tree, modname, parent=None, prefix=''):
        """Render in text a class tree as returned by inspect.getclasstree()."""
        result = ''
        for entry in tree:
            if type(entry) is type(()):
                c, bases = entry
                result = result + prefix + pydoc.classname(c, modname)
                if bases and bases != (parent,):
                    parents = (pydoc.classname(c, modname) for c in bases)
                    result = result + '(%s)' % ', '.join(parents)
                result = result + '\n'
            elif type(entry) is type([]):
                result = result + self.formattree(
                    entry, modname, c, prefix + '    ')
        return result

    def docmodule(self, object, name=None, mod=None):
        """Produce text documentation for a given module object."""
        name = object.__name__ # ignore the passed-in name
        synop, desc = pydoc.splitdoc(pydoc.getdoc(object))
        result = self.section('NAME', name + (synop and ' - ' + synop))
        all = getattr(object, '__all__', None)
        docloc = self.getdocloc(object)
        if docloc is not None:
            result = result + self.section('MODULE REFERENCE', docloc + """

The following documentation is automatically generated from the Python
source files.  It may be incomplete, incorrect or include features that
are considered implementation detail and may vary between Python
implementations.  When in doubt, consult the module reference at the
location listed above.
""")

        if desc:
            result = result + self.section('DESCRIPTION', desc)

        classes = []
        for key, value in inspect.getmembers(object, inspect.isclass):
            # if __all__ exists, believe it.  Otherwise use old heuristic.
            if (all is not None
                or (inspect.getmodule(value) or object) is object):
                if pydoc.visiblename(key, all, object):
                    classes.append((key, value))
        funcs = []
        for key, value in inspect.getmembers(object, inspect.isroutine):
            # if __all__ exists, believe it.  Otherwise use old heuristic.
            if (all is not None or
                    inspect.isbuiltin(value) or inspect.getmodule(value) is object):
                if pydoc.visiblename(key, all, object):
                    funcs.append((key, value))
        data = []
        for key, value in inspect.getmembers(object, pydoc.isdata):
            if pydoc.visiblename(key, all, object):
                data.append((key, value))

        modpkgs = []
        modpkgs_names = set()
        if hasattr(object, '__path__'):
            for importer, modname, ispkg in pkgutil.iter_modules(object.__path__):
                modpkgs_names.add(modname)
                if ispkg:
                    modpkgs.append(modname + ' (package)')
                else:
                    modpkgs.append(modname)

            modpkgs.sort()
            result = result + self.section(
                'PACKAGE CONTENTS', '\n'.join(modpkgs))

        # Detect submodules as sometimes created by C extensions
        submodules = []
        for key, value in inspect.getmembers(object, inspect.ismodule):
            if value.__name__.startswith(name + '.') and key not in modpkgs_names:
                submodules.append(key)
        if submodules:
            submodules.sort()
            result = result + self.section(
                'SUBMODULES', '\n'.join(submodules))

        if classes:
            classlist = [value for key, value in classes]
            contents = [self.formattree(
                inspect.getclasstree(classlist, 1), name)]
            for key, value in classes:
                contents.append(self.document(value, key, name))
            result = result + self.section('CLASSES', '\n'.join(contents))

        if funcs:
            contents = []
            for key, value in funcs:
                contents.append(self.document(value, key, name))
            result = result + self.section('FUNCTIONS', '\n'.join(contents))

        if data:
            contents = []
            for key, value in data:
                contents.append(self.docother(value, key, name, maxlen=70))
            result = result + self.section('DATA', '\n'.join(contents))

        if hasattr(object, '__version__'):
            version = str(object.__version__)
            if version[:11] == '$' + 'Revision: ' and version[-1:] == '$':
                version = version[11:-1].strip()
            result = result + self.section('VERSION', version)
        if hasattr(object, '__date__'):
            result = result + self.section('DATE', str(object.__date__))
        if hasattr(object, '__author__'):
            result = result + self.section('AUTHOR', str(object.__author__))
        if hasattr(object, '__credits__'):
            result = result + self.section('CREDITS', str(object.__credits__))
        try:
            file = inspect.getabsfile(object)
        except TypeError:
            file = '(built-in)'
        result = result + self.section('FILE', file)
        return result

    def docclass(self, object, name=None, mod=None, *ignored):
        """Produce text documentation for a given class object."""
        realname = object.__name__
        name = name or realname
        bases = object.__bases__

        def makename(c, m=object.__module__):
            return pydoc.classname(c, m)

        if name == realname:
            title = 'class ' + self.bold(realname)
        else:
            title = self.bold(name) + ' = class ' + realname
        if bases:
            parents = map(makename, bases)
            title = title + '(%s)' % ', '.join(parents)

        doc = pydoc.getdoc(object)
        contents = doc and [doc + '\n'] or []
        push = contents.append

        # List the mro, if non-trivial.
        mro = deque(inspect.getmro(object))
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
                        value = getattr(object, name)
                    except Exception:
                        # Some descriptors may meet a failure in their __get__.
                        # (bug #1785)
                        push(self._docdescriptor(name, value, mod))
                    else:
                        push(self.document(value,
                                           name, mod, object))
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
                    push(self.docother(getattr(object, name),
                                       name, mod, maxlen=70, doc=doc) + '\n')
            return attrs

        attrs = [(name, kind, cls, value)
                 for name, kind, cls, value in pydoc.classify_class_attrs(object)
                 if pydoc.visiblename(name, obj=object)]

        while attrs:
            if mro:
                thisclass = mro.popleft()
            else:
                thisclass = attrs[0][2]
            attrs, inherited = pydoc._split_list(attrs, lambda t: t[2] is thisclass)

            if thisclass is builtins.object:
                attrs = inherited
                continue
            elif thisclass is object:
                tag = "defined here"
            else:
                tag = "inherited from %s" % pydoc.classname(thisclass,
                                                      object.__module__)

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


class MarkdownDoc(CustomDoc):
    underline = "*" * 40

    def process_docstring(self, obj):
        """Get the docstring and turn it into a list."""
        docstring = pydoc.getdoc(obj)
        if docstring:
            return docstring + "\n\n"
        return ""

    def process_class_name(self, name, bases, module):
        """Format the class's name and bases."""
        title = "## class " + self.bold(name)
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

    def docclass(self, cls, name=None, mod=None):
        """Produce text documentation for the class object cls."""

        # the overall document, as a line-delimited list
        document = []

        # get the object's actual name, defaulting to the passed in name
        name = name or cls.__name__

        # get the object's bases
        bases = cls.__bases__

        # get the object's module
        mod = cls.__module__

        # get the object's MRO
        mro = [pydoc.classname(base, mod) for base in inspect.getmro(cls)]

        # get the object's classname, which should be printed
        classtitle = self.process_class_name(name, bases, mod)
        document.append(classtitle)
        document.append(self.underline)

        # get the object's docstring, which should be printed
        docstring = self.process_docstring(cls)
        document.append(docstring)

        # get all the attributes of the class
        attrs = []
        for name, kind, classname, value in pydoc.classify_class_attrs(cls):
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
                document.append(self.docother(getattr(cls, name), name, mod, maxlen=70, doc=doc) + '\n')

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
                document.append(self.document(getattr(cls, name), name, mod, cls))

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
