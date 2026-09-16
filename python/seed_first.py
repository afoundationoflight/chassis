"""Make the flat names resolvable BEFORE the bundle builds `local`.

local.py does `from pacing import Pacing`, `from tongue2 import Tongue`,
etc. — flat, not core.*. Those aliases are added AFTER _boot() in the
bundle, so during local.py's own import they do not exist yet and every
one falls into its except branch and becomes None. The modules are
fine; the ordering is wrong.
"""
import sys, types, importlib.abc, importlib.machinery

FLAT = ("pacing", "tongue2", "compose", "broadcast", "transcriptome")

class _Alias(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, name, path=None, target=None):
        if name in FLAT and f"core.{name}" in sys.modules:
            return importlib.machinery.ModuleSpec(name, self)
        return None
    def create_module(self, spec):
        return sys.modules[f"core.{spec.name}"]
    def exec_module(self, module):
        pass

sys.meta_path.insert(0, _Alias())
