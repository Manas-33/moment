"""Shared pytest fixtures / setup for the server test suite.

Some modules under Components/ read ANTHROPIC_API_KEY at import time and raise
if it is missing. The unit tests never make a real API call, so we provide a
dummy value before any test module is collected. This keeps imports working in
CI without needing real credentials.
"""

import os
import sys

# Ensure the server package root is importable so `import Components...` works
# regardless of where pytest is invoked from.
SERVER_ROOT = os.path.dirname(os.path.abspath(__file__))
if SERVER_ROOT not in sys.path:
    sys.path.insert(0, SERVER_ROOT)

# Dummy credential so import-time checks pass. Never used for a real request.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-dummy-key")
