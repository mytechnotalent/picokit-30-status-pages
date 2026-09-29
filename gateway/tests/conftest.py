"""Expose the gateway modules on sys.path for the pytest suite.

Parameters
----------
None

Returns
-------
None
"""

import os
import sys

_GATEWAY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _GATEWAY not in sys.path:
    sys.path.insert(0, _GATEWAY)
