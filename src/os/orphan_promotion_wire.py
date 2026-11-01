"""orphan_promotion_wire (R2356; criteria AC-OPW1..AC-OPW6 were pre-registered
inside the R2342 seed row of state/queue/tech.md:400 BEFORE this file existed).

orphan_promote can copy a stranded green leg to its canonical name, and
orphan_promotion_ledger can record and judge that act - but the WRITER never
asked the ledger. Its only guard was "does the canonical target exist on disk",
so a round the ledger already claims with no file behind it (a backfilled
record, a lapsed judgement) was invisible: a later promotion of the same round
would copy silently, and the operator would never learn which record it had
just walked over.

This module is that wiring, and it stays narrow:

  * the ledger reading is imported from orphan_promotion_ledger (its
    declaration reader, its entry validator, its canonical file listing and its
    own five-class judgement) and the round, the target name and the plan come
    from orphan_promote, so a patched reading flows straight through and no
    second law is written here (AC-OPW1);
  * the gate runs BEFORE the writer looks at the target at all, and it refuses
    an entry that still holds: a RECORDED canonical target refuses naming the
    round, the canonical name, the declaring round and the round the judgement
    runs until (AC-OPW2), and a STALE entry refuses naming both digests - the
    recorded one and the one on disk (AC-OPW3);
  * an EXPIRED judgement permits the copy and the plan names the lapsed until
    so the operator sees the record it supersedes. The same reading covers the
    shape the gap actually bites in - an entry whose file is gone - because a
    lapsed record can no longer be honoured while a LIVE one can: a claim whose
    file vanished and whose until has not arrived refuses as E_OPW_LIVE_RECORD
    rather than overwrite the name the record still owns (AC-OPW4). An
    UNRECORDED canonical file refuses too, naming that no entry claims it,
    since the ledger cannot say who wrote the bytes it would replace;
  * a refusal happens before a single byte is written, so the evidence
    directory stays listing-identical and digest-identical with no .part
    residue, and the CLI keeps the codes orphan_promote pins: 0 planned or
    performed, 2 refused over live state, 3 evidence or declaration absent or
    unreadable, 5 bad flags (AC-OPW5);
  * pure ASCII source, stdlib only, zero network, no clock, no delete, and the
    module itself never opens a file for writing - the only mutation in this
    path is orphan_promote's own single os.replace, which is why this file
    holds no write primitive at all (AC-OPW6).

The one place this module reads a date for itself is the lapse test on a
MISSING entry: orphan_promotion_ledger.judge() lets the integrity readings
outrank expiry, so a claim whose file is gone always reads MISSING there.
Whether that claim has lapsed is therefore decided here, from the entry's own
`until` through that module's parse_round, and nowhere else.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import evidence_variants as EV
import orphan_promote as OP
import orphan_promotion_ledger as OPL

SUITE_LABEL = "os-orphan-promotion-wire"

NONE = "NONE"
LAPSED = "EXPIRED"

ALLOW = "ALLOW"
REFUSE = "REFUSE"

E_OPW_RECORDED = "E_OPW_RECORDED"
E_OPW_STALE = "E_OPW_STALE"
E_OPW_LIVE_RECORD = "E_OPW_LIVE_RECORD"
E_OPW_UNRECORDED = "E_OPW_UNRECORDED"
E_OPW_NO_DECL = "E_OPW_NO_DECL"
E_OPW_UNREADABLE = "E_OPW_UNREADABLE"
E_OPW_BAD_ARGS = "E_OPW_BAD_ARGS"

REPORT_KEYS = ("action", "round", "ledger", "decision", "detail",
               "declared_by", "until", "recorded_digest", "live_digest",
               "source", "target", "source_bytes", "digest", "standing_in",
               "green_legs", "other_green", "wrote", "verdict")


class OrphanPromotionWireError(Exception):
    """A refusal carrying its own code, and the reading that produced it."""

    def __init__(self, code, detail="", decision=None):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail
        self.decision = decision


def _decode(exc):
    """Ledger refusals keep their own distinction: absent vs unreadable."""
    if getattr(exc, "code", "") == OPL.E_OPL_NO_DECL:
        return E_OPW_NO_DECL
    return E_OPW_UNREADABLE


def _round(value):
    """One round reference, through orphan_promote's own law (AC-OPW1)."""
    try:
        return OP.parse_round(value)
    except OP.OrphanPromoteError:
        raise OrphanPromotionWireError(E_OPW_BAD_ARGS,
                                       "%r is not a round number" % (value,))


def _claim(root, label, directory):
    """The ledger's reading of one round: class, entry, and both digests."""
    try:
        text, payload = OPL.read_declaration(root)
        entries = OPL.declaration_entries(text)
        path, files = OPL.canonical_files(root, directory)
        _counts, rows, _out_of_scope = OPL.judge(
            entries, path, files, label, payload["since_round"])
    except OPL.OrphanPromotionLedgerError as exc:
        raise OrphanPromotionWireError(_decode(exc), exc.detail or exc.code)
    entry = None
    for item in entries:
        if item["round"] == label:
            entry = item
    claimed = None
    for item in rows:
        if item["round"] == label and item["class"] != OPL.UNRECORDED:
            claimed = item
    unclaimed = None
    for item in rows:
        if item["round"] == label and item["class"] == OPL.UNRECORDED:
            unclaimed = item
    live = None
    if entry is not None and entry["canonical"] in files.values():
        try:
            live = EV.digest_of(os.path.join(path, entry["canonical"]))
        except EV.EvidenceVariantsError:
            raise OrphanPromotionWireError(E_OPW_UNREADABLE,
                                           entry["canonical"])
    return {"entry": entry, "claimed": claimed, "unclaimed": unclaimed,
            "live": live}


def _blank(number):
    return {"round": number, "ledger": NONE, "decision": ALLOW,
            "detail": "no ledger entry claims R%d" % number,
            "declared_by": "-", "until": "-", "recorded_digest": "-",
            "live_digest": "-"}


def _filled(number, entry, ledger, decision, detail, live):
    return {"round": number, "ledger": ledger, "decision": decision,
            "detail": detail,
            "declared_by": entry["declared_by"] if entry else "-",
            "until": (entry["until"] or "-") if entry else "-",
            "recorded_digest": entry["digest"] if entry else "-",
            "live_digest": live or "-"}


def _lapsed(number, entry):
    """The entry's own until, read through the ledger's parse_round."""
    if not entry["until"]:
        return False
    return number >= int(OPL.parse_round(entry["until"])[1:])


def audit(root, round_value, directory="qa"):
    """Read-only: what the ledger says about this round's canonical name."""
    number = _round(round_value)
    label = "R%d" % number
    claim = _claim(root, label, directory)
    entry = claim["entry"]
    claimed = claim["claimed"]
    unclaimed = claim["unclaimed"]
    live = claim["live"]
    if entry is None:
        if unclaimed is not None:
            return _filled(
                number, None, OPL.UNRECORDED, REFUSE,
                "%s exists in %s and no ledger entry claims it; the ledger "
                "cannot say who wrote the bytes a copy would replace"
                % (unclaimed["canonical"], directory), None)
        return _blank(number)
    canonical = entry["canonical"]
    if claimed is None:
        # A claim the judge did not place: the entry was scoped out of the
        # unrecorded sweep but still names this round, so it is judged here
        # by the same rule the judge uses for every entry.
        return _filled(number, entry, OPL.MISSING, REFUSE,
                       "R%d is recorded as %s by %s until %s and the ledger "
                       "cannot judge it"
                       % (number, canonical, entry["declared_by"],
                          entry["until"] or "-"), live)
    kind = claimed["class"]
    if kind == OPL.RECORDED:
        return _filled(
            number, entry, OPL.RECORDED, REFUSE,
            "R%d is recorded as %s by %s until %s; nothing is copied"
            % (number, canonical, entry["declared_by"], entry["until"] or "-"),
            live)
    if kind == OPL.STALE:
        return _filled(
            number, entry, OPL.STALE, REFUSE,
            "R%d is recorded with digest %s and %s/%s reads %s; the record no "
            "longer describes the file"
            % (number, entry["digest"], directory, canonical, live or "-"),
            live)
    if kind == OPL.MISSING:
        if _lapsed(number, entry):
            return _filled(
                number, entry, LAPSED, ALLOW,
                "the record of R%d lapsed at %s (declared by %s) and %s is "
                "absent; the copy supersedes it"
                % (number, entry["until"], entry["declared_by"], canonical),
                live)
        return _filled(
            number, entry, OPL.MISSING, REFUSE,
            "R%d is recorded as %s by %s until %s and that file is absent; a "
            "live record outranks the copy"
            % (number, canonical, entry["declared_by"], entry["until"] or "-"),
            live)
    if kind == OPL.EXPIRED:
        return _filled(
            number, entry, LAPSED, ALLOW,
            "the record of R%d lapsed at %s (declared by %s); the copy "
            "supersedes it"
            % (number, entry["until"], entry["declared_by"]), live)
    raise OrphanPromotionWireError(
        E_OPW_UNREADABLE, "ledger class %r is not one this wire knows" % kind)


def gate(root, round_value, directory="qa"):
    """The audit, raising with its own code when the copy must not happen."""
    decision = audit(root, round_value, directory)
    if decision["decision"] != ALLOW:
        code = {OPL.RECORDED: E_OPW_RECORDED, OPL.STALE: E_OPW_STALE,
                OPL.MISSING: E_OPW_LIVE_RECORD,
                OPL.UNRECORDED: E_OPW_UNRECORDED}.get(decision["ledger"],
                                                     E_OPW_LIVE_RECORD)
        raise OrphanPromotionWireError(code, decision["detail"], decision)
    return decision


def _merge(decision, base):
    report = {}
    for key in REPORT_KEYS:
        if key in base:
            report[key] = base[key]
    report["round"] = base["round"]
    report["ledger"] = decision["ledger"]
    report["decision"] = decision["decision"]
    report["detail"] = decision["detail"]
    report["declared_by"] = decision["declared_by"]
    report["until"] = decision["until"]
    report["recorded_digest"] = decision["recorded_digest"]
    report["live_digest"] = decision["live_digest"]
    return report


def plan(root, round_value, directory="qa", source=None):
    """The ledger gate, then orphan_promote's own plan."""
    decision = gate(root, round_value, directory)
    return _merge(decision, OP.plan(root, round_value, directory, source))


def promote(root, round_value, directory="qa", source=None, execute=False):
    """The ledger gate, then orphan_promote's own single copy."""
    decision = gate(root, round_value, directory)
    return _merge(decision,
                  OP.promote(root, round_value, directory, source, execute))


def render(report):
    """One line for the act, one for the ledger reading behind it."""
    out = ["ORPHAN PROMOTION WIRE action=%s round=R%d ledger=%s decision=%s "
           "source=%s target=%s bytes=%d wrote=%s verdict=%s"
           % (report["action"], report["round"], report["ledger"],
              report["decision"], report["source"], report["target"],
              report["source_bytes"], "yes" if report["wrote"] else "no",
              report["verdict"])]
    out.append("  declared_by=%s until=%s detail=%s"
               % (report["declared_by"], report["until"], report["detail"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: orphan_promotion_wire.py (--plan|--promote) ROUND [DIR]\n"
         "                                  [--root PATH] [--src LEG] [--json]\n"
         "  DIR defaults to qa; --promote is the only writing mode and it\n"
         "  asks state/orphan_promotions.json before orphan_promote runs\n"
         "  exit 0 = planned, or one promotion performed\n"
         "  exit 2 = refused over live state (recorded, stale, a live record\n"
         "           whose file is gone, an unrecorded canonical file, or a\n"
         "           refusal of orphan_promote itself) and nothing was written\n"
         "  exit 3 = declaration or evidence absent, unreadable or undecodable\n"
         "  exit 5 = bad flags\n")


def parse_args(argv):
    """Flags only, mirroring orphan_promote's surface."""
    request = {"mode": None, "as_json": False, "directory": "qa",
               "root": os.path.dirname(os.path.dirname(os.path.dirname(
                   os.path.abspath(__file__)))),
               "source": None, "operands": []}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--plan", "--promote"):
            if request["mode"] is not None:
                raise OrphanPromotionWireError(E_OPW_BAD_ARGS,
                                               "one mode only")
            request["mode"] = "promote" if arg == "--promote" else "plan"
        elif arg == "--json":
            request["as_json"] = True
        elif arg in ("--root", "--src"):
            index += 1
            if index >= len(argv):
                raise OrphanPromotionWireError(E_OPW_BAD_ARGS,
                                               "%s needs a value" % arg)
            request["root" if arg == "--root" else "source"] = argv[index]
        elif arg in ("--help", "-h"):
            request["mode"] = "help"
        elif arg.startswith("-"):
            raise OrphanPromotionWireError(E_OPW_BAD_ARGS,
                                           "unknown flag %s" % arg)
        else:
            request["operands"].append(arg)
        index += 1
    if request["mode"] in (None, "help"):
        return request
    if not request["operands"]:
        raise OrphanPromotionWireError(E_OPW_BAD_ARGS, "a round is required")
    if len(request["operands"]) > 2:
        raise OrphanPromotionWireError(E_OPW_BAD_ARGS, "too many operands")
    if len(request["operands"]) == 2:
        request["directory"] = request["operands"][1]
    return request


def main(argv):
    try:
        request = parse_args(argv)
    except OrphanPromotionWireError as exc:
        sys.stdout.write("%s\n" % str(exc))
        sys.stdout.write(USAGE)
        return 5
    if request["mode"] in (None, "help"):
        sys.stdout.write(USAGE)
        return 5 if request["mode"] is None else 0
    try:
        report = promote(request["root"], request["operands"][0],
                         request["directory"], request["source"],
                         execute=(request["mode"] == "promote"))
    except OrphanPromotionWireError as exc:
        sys.stdout.write("%s\n" % str(exc))
        if exc.code in (E_OPW_NO_DECL, E_OPW_UNREADABLE):
            return 3
        if exc.code == E_OPW_BAD_ARGS:
            return 5
        return 2
    except OP.OrphanPromoteError as exc:
        sys.stdout.write("%s\n" % str(exc))
        if exc.code in ("E_OTP_NO_EVIDENCE", "E_OTP_UNREADABLE",
                        "E_OTP_BAD_NAME", "E_OTP_UNDECODABLE"):
            return 3
        if exc.code == "E_OTP_BAD_ARGS":
            return 5
        return 2
    if request["as_json"]:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))