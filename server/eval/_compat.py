"""
Compatibility shim: provide a stub `lzma` module when the interpreter lacks it.

This project's pyenv Python 3.12.0 was built without the `_lzma` C extension.
Several deps (pooch via librosa, joblib) `import lzma` and reference names like
`lzma.LZMAFile` at import time, even though we never use lzma (de)compression
here. A stub whose attributes resolve to harmless dummies lets those imports
succeed. If the real lzma is available, we use it and this shim is a no-op.

Import this module FIRST, before librosa / joblib / pooch.
"""
from __future__ import annotations

import sys
import types


def _install_lzma_stub() -> bool:
    try:
        import lzma  # noqa: F401  (real one exists -> nothing to do)
        return False
    except Exception:
        pass

    stub = types.ModuleType("lzma")

    class _Dummy:  # placeholder for LZMACompressor/etc. (never called)
        def __init__(self, *a, **k):
            raise RuntimeError("lzma is not available in this interpreter")

    class _StubLZMAFile:
        """File-like placeholder. joblib interface-checks read/write/seek/tell
        at registration; it is never instantiated (we never use lzma)."""
        def __init__(self, *a, **k):
            raise RuntimeError("lzma is not available in this interpreter")

        def read(self, *a, **k): ...
        def write(self, *a, **k): ...
        def seek(self, *a, **k): ...
        def tell(self, *a, **k): ...
        def close(self, *a, **k): ...
        def flush(self, *a, **k): ...

    # Names commonly referenced at import time by joblib / pooch / pandas.
    _known = {
        "LZMAFile": _StubLZMAFile, "LZMACompressor": _Dummy, "LZMADecompressor": _Dummy,
        "LZMAError": type("LZMAError", (Exception,), {}),
        "CHECK_NONE": 0, "CHECK_CRC32": 1, "CHECK_CRC64": 4, "CHECK_SHA256": 10,
        "FORMAT_XZ": 1, "FORMAT_ALONE": 2, "FORMAT_RAW": 3, "FORMAT_AUTO": 0,
    }
    for name, val in _known.items():
        setattr(stub, name, val)

    def _open(*a, **k):
        raise RuntimeError("lzma is not available in this interpreter")

    stub.open = _open
    stub.compress = _open
    stub.decompress = _open

    # Unknown non-dunder names -> a dummy class, so unexpected lzma attribute
    # refs still resolve. Dunders (e.g. __file__) must raise AttributeError so
    # module introspection (inspect, importlib) keeps working.
    def _getattr(name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        return type(name, (), {})

    stub.__getattr__ = _getattr  # type: ignore[attr-defined]

    sys.modules["lzma"] = stub
    return True


STUBBED = _install_lzma_stub()
