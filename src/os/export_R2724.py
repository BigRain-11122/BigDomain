"""export_R2724 - refresh docs/status-export.json for the R2724 round.

The three CEO lines and the derived faces are composed by export_R2431.main(),
which derives every value from the live tree rather than from constants.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

if __name__ == "__main__":
    sys.exit(base.main())
