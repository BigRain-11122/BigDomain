"""export_R2723 - refresh docs/status-export.json for the R2723 round.

The three CEO lines and the derived faces are composed by export_R2431.main(),
which derives every value from the live tree (state tick, the log tail, the
queue_floor and debt gate faces, this round own evidence on disk) rather than
from constants.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

if __name__ == "__main__":
    sys.exit(base.main())
