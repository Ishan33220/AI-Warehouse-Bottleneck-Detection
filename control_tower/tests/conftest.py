"""
Shared pytest configuration.

Adds the control_tower/ directory to sys.path so that imports like
``from config.settings import ...`` and ``from tools.data_loader import ...``
resolve correctly regardless of where pytest is invoked.
"""

import sys
from pathlib import Path

# control_tower/ is the parent of tests/
CONTROL_TOWER = Path(__file__).resolve().parent.parent
if str(CONTROL_TOWER) not in sys.path:
    sys.path.insert(0, str(CONTROL_TOWER))
