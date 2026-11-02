"""Ask the single-append status face BEFORE the triage read (R2392).

The seed row is state/queue/tech.md line 449 (R2385) and its criteria
AC-ACSP1..AC-ACSP6 were pinned there BEFORE this file existed.

What this proves: `residue_triage_append.py --check` used to ask
residue_triage FIRST, so exactly when that read refused (measured at R2385 on
the real tree: `--check --round R1755` answered E_RTA_UNREADABLE /
E_RTR_DECL_FUTURE while the status face alone read R1755 DELIVERED at exit 0)
the operator got no status at all for the one round they were asking about.

This module owns the ORDER and nothing else:

  * the status reading stays single_append_status_face (asked at call time, so
    a patched face flows straight through and this module loads without it),
  * the triage reading stays residue_triage.read,
  * the refusal is returned, not raised here, so residue_triage_append keeps
    the one law that maps a triage code onto its own E_RTA_* vocabulary.

No second residue scan is written: the live residue is read once, by
residue_triage, through the face's own channel.

Pure read. Stdlib only, ASCII source, no clock, no network.
"""

SUITE_LABEL = "os-append-check-status-precedence"

# The label single_append_status_face reports for a round the live residue does
# not carry. The READING is that module's; this constant is only the word this
# note is keyed on, and the suite pins the two equal.
NOT_RESIDUE = "NOT-RESIDUE"

NOTE_STATUS_ON_REFUSAL = "E_ACSP_STATUS_ON_REFUSAL"

NOTE_NOT_RESIDUE = "E_SASF_NOT_RESIDUE"

FACE_CODE = "E_ACSP_BAD_STATE"


class AppendCheckStatusPrecedenceError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _face(root, requested):
    """The status face's reading, asked at call time (AC-ACSP1)."""
    import single_append_status_face as SASF
    try:
        return SASF.reading(root, requested)
    except SASF.SingleAppendStatusFaceError as exc:
        raise AppendCheckStatusPrecedenceError(
            FACE_CODE, "%s: %s" % (exc.code, exc.detail))


def asked(root, requested):
    """The face first, then the triage read; one outcome, no raise for a
    triage refusal (AC-ACSP1, AC-ACSP2)."""
    face = _face(root, requested)
    import residue_triage as RT
    try:
        report = RT.read(root, requested)
    except RT.ResidueTriageError as exc:
        return {
            "requested": requested,
            "status": face["requested_status"],
            "found": face["found"],
            "report": None,
            "refusal": {"code": exc.code, "detail": exc.detail},
        }
    return {
        "requested": requested,
        "status": face["requested_status"],
        "found": face["found"],
        "report": report,
        "refusal": None,
    }


def status_line(outcome):
    """The one status field a refused check gains (AC-ACSP2)."""
    return "STATUS %s %s" % (outcome["requested"], outcome["status"])


def note_line(outcome):
    """The one NOTE line a refused check gains (AC-ACSP3, AC-ACSP4)."""
    if outcome["status"] == NOT_RESIDUE:
        return ("NOTE %s: %s is not in the live residue"
                % (NOTE_NOT_RESIDUE, outcome["requested"]))
    return ("NOTE %s: the status face answers even when the triage read "
            "refuses" % NOTE_STATUS_ON_REFUSAL)


def refusal_lines(outcome):
    """Both added lines, in the order an operator reads them."""
    return [status_line(outcome), note_line(outcome)]