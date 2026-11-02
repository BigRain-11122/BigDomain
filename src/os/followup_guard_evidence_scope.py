"""followup_guard_evidence_scope (R2380; criteria AC-FGES1..AC-FGES6 were

pinned inside the R2370 seed row of state/queue/tech.md BEFORE this code
existed).

followup_section_foreign_wire (R2370) made the follow-up matrix section ask the
foreign-section reader first, but it asked a FIXED pile: matrix_section took
the evidence path the operator named and then guarded the literal directory
'qa'. A matrix regenerated from any other pile was therefore protected by a
reading of a pile it was not comparing - the refusal spoke about qa while the
doc was built from somewhere else. The wire's own suite passed because the
qa-shaped pile is exactly the one it was handed.

This module owns ONE question: which pile does an evidence path belong to?

  - evidence_dir(evidence)  the immediate directory of the log's own path.

It is deliberately tiny and pure: no log parsing, no matrix rendering, no write,
no clock, no network. followup_section_foreign still owns the READING (this file
imports nothing from it) and battery_followup still owns the matrix core, so
each law keeps exactly one owner and the guard now measures the same pile the
matrix is built from.

The derivation is the seam: the wire asks it at call time, so a patched
derivation moves which pile is read, and a relative and an absolute path for
the same file resolve to the same directory name (AC-FGES4), because only the
basename of the resolved parent is kept.
"""

import os

E_FGES_BAD_ARGS = "E_FGES_BAD_ARGS"

DEFAULT_DIR = "qa"


def evidence_dir(evidence, default=DEFAULT_DIR):
    """AC-FGES1: the pile a log belongs to, derived from its own path.

    A bare filename (no directory part) has no measured pile, so the caller's
    default is returned - the honest reading of "this file names no pile"
    rather than a guess. A relative path and an absolute path for the same
    file both reduce to the same parent basename (AC-FGES4).
    """
    if not isinstance(evidence, str) or not evidence:
        return default
    parent = os.path.dirname(evidence)
    if not parent:
        return default
    return os.path.basename(os.path.abspath(parent))