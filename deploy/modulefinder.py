"""Find modules used by a script, using introspection."""

import dis
import os
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore', DeprecationWarning)
    import imp

LOAD_CONST = dis.opmap['LOAD_CONST']
IMPORT_NAME = dis.opmap['IMPORT_NAME']
STORE_NAME = dis.opmap['STORE_NAME']
STORE_GLOBAL = dis.opmap['STORE_GLOBAL']
STORE_OPS = STORE_NAME, STORE_GLOBAL
EXTENDED_ARG = dis.EXTENDED_ARG


class ModuleFinder:

    def __init__(self, encoding=None, root_path=None):
        self.encoding = encoding
        self.paths = []
        self.root_path = root_path

    def scan_opcodes(self, co):
        # Scan the code, and yield 'interesting' opcode combinations
        code = co.co_code
        names = co.co_names
        consts = co.co_consts
        opargs = [(op, arg) for _, op, arg in dis._unpack_opargs(code)
                  if op != EXTENDED_ARG]
        for i, (op, oparg) in enumerate(opargs):
            if op in STORE_OPS:
                yield "store", (names[oparg],)
                continue
            if (op == IMPORT_NAME and i >= 2
                    and opargs[i-1][0] == opargs[i-2][0] == LOAD_CONST):
                level = consts[opargs[i-2][1]]
                fromlist = consts[opargs[i-1][1]]
                if level == 0: # absolute import
                    yield "absolute_import", (fromlist, names[oparg])
                else: # relative import
                    yield "relative_import", (level, fromlist, names[oparg])
                continue

    def load_file(self, pathname):
        fp = open(pathname, encoding=self.encoding)
        if pathname == 'D:\\code\\MindgoIncrementalFramework\\styles\\parse_style.py':
            pass
        co = compile(fp.read() + '\n', pathname, 'exec')
        if pathname in self.paths:
            self.paths.remove(pathname)
        self.paths.append(pathname)
        self.scan_code(co)
        fp.close()


    def add_file(self, fromlist, name):
        path = os.path.join(self.root_path, os.sep.join(name.split('.')) + '.py')
        if path == 'D:\\code\\MindgoIncrementalFramework\\styles\\parse_style.py':
            pass
        if os.path.exists(path):
            self.load_file(path)
        else:
            if fromlist is not None:
                for f in fromlist:
                    path = os.path.join(self.root_path, os.sep.join(name.split('.') + [f]) + '.py')
                    if os.path.exists(path):
                        self.load_file(path)
            else:
                pass

    def scan_code(self, co):
        code = co.co_code
        scanner = self.scan_opcodes
        for what, args in scanner(co):
            if what == "store":
                name, = args
            elif what == "absolute_import":
                fromlist, name = args
                self.add_file(fromlist, name)
            elif what == "relative_import":
                level, fromlist, name = args
            else:
                # We don't expect anything else from the generator.
                raise RuntimeError(what)

        # for c in co.co_consts:
        #     if isinstance(c, type(co)):
        #         self.scan_code_1(c)
