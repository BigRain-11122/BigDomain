"""Carry the declaration's own declared_by on a refused check (R2393).

Seed row is state/queue/tech.md line 451 (R2392) and its criteria
AC-RCDF1..AC-RCDF6 were pinned there BEFORE this file existed.

What this proves: `residue_triage_append.py --check` gained the asked round's
live status at R2392, but the machine-readable refusal still answered
declared_by="-" while its own detail line said "declared_by R2391 is later
than the round being checked R1755" - the boundary a check tripped on was
readable in prose and absent from the payload.

This module owns ONE derivation and nothing else:

  * the declaration is read by residue_triage.load_declaration, asked at call
    time so a patched loader flows straight through and this module loads
    without it,
  * nothing is aged here: the live residue is never read, so a declaration
    whose entries would raise a different triage code cannot change the
    refusal code a check already reports (AC-RCDF3),
  * an absent, unreadable or malformed declaration reads the honest unknown
    "-" and never a fabricated round (AC-RCDF2).

Pure read. Stdlib only, ASCII source, no clock, no network.
"""

SUITE_LABEL = "os-refused-check-declaration-face"

# The word a refusal carries when the declaration cannot name a boundary.
UNKNOWN = "-"


def head(root):
    """The declaration's own declared_by, or UNKNOWN (AC-RCDF1, AC-RCDF2)."""
    import residue_triage as RT
    try:
        declaration = RT.load_declaration(root)
    except RT.ResidueTriageError:
        return UNKNOWN
    if declaration is None:
        return UNKNOWN
    return "R%d" % declaration["declared_by"]