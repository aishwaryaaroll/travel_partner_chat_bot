"""travel_partner backend.

The agent package lives in ``travel_partner/agents`` (a sibling of ``backend``),
so the project root is put on ``sys.path`` once here.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
