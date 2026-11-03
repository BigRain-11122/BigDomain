"""orphan_promotion_ledger (R2342; criteria AC-OPL1..AC-OPL6 were pre-registered
inside the R2339 seed row of state/queue/tech.md:388 BEFORE this file existed).

orphan_promote can create a canonical evidence name out of a stranded variant
leg, and R2339 performed exactly that for R2136 - but nothing recorded the act.
The canonical log landed in qa/ with no note of which leg it came from, which
digest it carried, which round promoted it or until when that judgement holds,
so a canonical file no window ever promoted reads exactly like one the writer
produced.

This module is that record, and it is narrow:

  * the canonical name law is asked of orphan_promote and the evidence
    directory of orphan_trace (AC-OPL1), so a patched reading flows straight
    through and no second law is written here;
  * every canonical file on disk and every declaration entry lands in EXACTLY
    one of five disjoint readings - MISSING (an entry names a file that is
    gone), STALE (the recorded digest no longer matches the file, with both
    digests named), EXPIRED (the entry's until round has been reached),
    RECORDED (bytes still match the recorded digest) and UNRECORDED (a
    canonical file no entry claims) - and the four file-side readings account
    for every canonical file (AC-OPL2). UNRECORDED is scoped by the
    declaration's own dated `since_round`: a canonical file whose round
    predates the round this ledger came into force cannot have been produced by
    a writer that had a ledger to write to, so it is counted as out_of_scope
    and NAMED rather than accused, while every entry is judged whatever its
    round because a backfilled record is still a claim;
  * the blocker order is pinned and documented: the two integrity readings
    outrank expiry, because a byte change is a fact about the record's own
    claim while expiry is only a date (AC-OPL3);
  * an append is raw text with one atomic replace, a duplicate round refuses
    by naming the recorded entry, and every neighbour entry stays
    byte-identical (AC-OPL4);
  * the reader writes nothing at all - it opens the evidence directory only to
    list and hash - and an absent or malformed declaration fails closed
    instead of reading NOTHING-TO-DO (AC-OPL5);
  * pure ASCII source, stdlib only, zero network, no clock (AC-OPL6).

The recorded bytes and digest are MEASURED from the canonical file at append
time rather than taken from the caller, because a record whose digest the
caller chooses would only ever confirm itself.
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import declaration_writer_dialect_preservation as DWD
import evidence_variants as EV
import followup_history as FH
import orphan_promote as OP
import orphan_trace as OT

DECL_REL = "state/orphan_promotions.json"
SUITE_LABEL = "os-orphan-promotion-ledger"
TEMP_SUFFIX = ".opl.tmp"

RECORDED = "RECORDED"
STALE = "STALE"
EXPIRED = "EXPIRED"
MISSING = "MISSING"
UNRECORDED = "UNRECORDED"
CLASSES = (RECORDED, STALE, EXPIRED, MISSING, UNRECORDED)

REPORT_KEYS = ("decl", "pinned", "since", "round", "entries", "recorded",
               "stale", "expired", "missing", "unrecorded", "out_of_scope",
               "canonical", "rows", "verdict")
ENTRY_KEYS = ("round", "canonical", "source", "bytes", "digest",
              "declared_by", "until", "reason")
PLAN_KEYS = ENTRY_KEYS + ("path", "entry_index", "entry_count_before",
                          "entry_count_after", "before_bytes",
                          "predicted_bytes", "wrote", "read_back_ok")

E_OPL_BAD_ARGS = "E_OPL_BAD_ARGS"
E_OPL_NO_DECL = "E_OPL_NO_DECL"
E_OPL_BAD_DECL = "E_OPL_BAD_DECL"
E_OPL_NO_EVIDENCE = "E_OPL_NO_EVIDENCE"
E_OPL_BAD_ROUND = "E_OPL_BAD_ROUND"
E_OPL_DUP = "E_OPL_DUP"
E_OPL_UNTIL = "E_OPL_UNTIL"
E_OPL_NO_CANONICAL = "E_OPL_NO_CANONICAL"
E_OPL_UNREADABLE = "E_OPL_UNREADABLE"
E_OPL_PREDICT = "E_OPL_PREDICT"
E_OPL_WRITE = "E_OPL_WRITE"
E_OPL_READBACK = "E_OPL_READBACK"
E_OPL_TEMP_RESIDUE = "E_OPL_TEMP_RESIDUE"
E_OPL_NO_ROUND = "E_OPL_NO_ROUND"


class OrphanPromotionLedgerError(Exception):
    """A reading or a refusal that must not guess, carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code + (" " + detail if detail else ""))
        self.code = code
        self.detail = detail


def parse_round(value, code=E_OPL_BAD_ROUND):
    """One round reference as R<n>: R2136, 2136 or the int 2136."""
    if isinstance(value, bool):
        raise OrphanPromotionLedgerError(code, "round must be a number")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str):
        text = value.strip()
        if text[:1] in ("R", "r"):
            text = text[1:]
        if not text.isdigit():
            raise OrphanPromotionLedgerError(code,
                                             "%r is not a round" % (value,))
        number = int(text)
    else:
        raise OrphanPromotionLedgerError(code, "%r is not a round" % (value,))
    if number <= 0:
        raise OrphanPromotionLedgerError(code, "round must be positive")
    return "R%d" % number


def render_entry(round_label, canonical, source, size, digest, declared_by,
                 until, reason):
    """The pinned entry shape, keys in one order."""
    return {"round": parse_round(round_label),
            "canonical": canonical,
            "source": source or "",
            "bytes": size,
            "digest": digest,
            "declared_by": parse_round(declared_by),
            "until": parse_round(until) if until else "",
            "reason": reason}


def _validate_entry(entry):
    if not isinstance(entry, dict):
        raise OrphanPromotionLedgerError(E_OPL_BAD_DECL, "entry is not a row")
    keys = tuple(entry.keys())
    if sorted(keys) != sorted(ENTRY_KEYS):
        raise OrphanPromotionLedgerError(
            E_OPL_BAD_DECL,
            "entry keys %s are not the pinned shape" % (",".join(keys),))
    label = parse_round(entry["round"], E_OPL_BAD_DECL)
    canonical = entry["canonical"]
    if canonical != OP.canonical_name(int(label[1:])):
        raise OrphanPromotionLedgerError(
            E_OPL_BAD_DECL,
            "entry %s names %s, which is not the canonical name of that round"
            % (label, canonical))
    if not isinstance(entry["bytes"], int) or entry["bytes"] < 0:
        raise OrphanPromotionLedgerError(E_OPL_BAD_DECL,
                                         "entry %s carries no byte count" % label)
    if not isinstance(entry["digest"], str) or not entry["digest"]:
        raise OrphanPromotionLedgerError(E_OPL_BAD_DECL,
                                         "entry %s carries no digest" % label)
    parse_round(entry["declared_by"], E_OPL_BAD_DECL)
    if entry["until"]:
        parse_round(entry["until"], E_OPL_BAD_DECL)
    for key in ("source", "reason"):
        if not isinstance(entry[key], str):
            raise OrphanPromotionLedgerError(E_OPL_BAD_DECL,
                                             "entry %s field %s is not text"
                                             % (label, key))
    return entry


def declaration_entries(text):
    """Parse the declaration text; every entry validated, order preserved."""
    payload = declaration_payload(text)
    rows = payload["entries"]
    seen = {}
    entries = []
    for row in rows:
        entries.append(_validate_entry(row))
        label = row["round"]
        if label in seen:
            raise OrphanPromotionLedgerError(
                E_OPL_BAD_DECL, "%s is declared twice" % label)
        seen[label] = row
    return entries


def declaration_payload(text):
    """The declaration object: a dated scope plus its entries."""
    try:
        payload = json.loads(text)
    except ValueError as exc:
        raise OrphanPromotionLedgerError(E_OPL_BAD_DECL, str(exc))
    if not isinstance(payload, dict):
        raise OrphanPromotionLedgerError(E_OPL_BAD_DECL,
                                         "declaration is not an object")
    missing = [key for key in ("since_round", "entries")
               if key not in payload]
    if missing:
        raise OrphanPromotionLedgerError(
            E_OPL_BAD_DECL, "declaration carries no %s" % ",".join(missing))
    payload["since_round"] = parse_round(payload["since_round"], E_OPL_BAD_DECL)
    if not isinstance(payload["entries"], list):
        raise OrphanPromotionLedgerError(E_OPL_BAD_DECL,
                                         "entries is not a list")
    return payload


def read_declaration(root):
    """The declaration text, its validated entries and its dated scope."""
    path = os.path.join(root, DECL_REL)
    if not os.path.isfile(path):
        raise OrphanPromotionLedgerError(
            E_OPL_NO_DECL,
            "no promotion ledger at %s" % DECL_REL.replace(os.sep, "/"))
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise OrphanPromotionLedgerError(E_OPL_UNREADABLE, "%s (%s)"
                                         % (path, exc))
    return text, declaration_payload(text)


def evidence_dir(root, directory="qa"):
    """The one evidence directory this reader opens, asked of orphan_trace."""
    try:
        return OT.evidence_path(root, directory)
    except OT.OrphanTraceError as exc:
        raise OrphanPromotionLedgerError(E_OPL_NO_EVIDENCE, exc.detail)


def canonical_files(root, directory="qa"):
    """Every canonical evidence file on disk, keyed by its round label.

    The round is read off the shared name law (followup_history.NAME_RE) and
    the name is then REQUIRED to equal orphan_promote.canonical_name of that
    round, so the canonical law still has exactly one owner (AC-OPL1).
    """
    path = evidence_dir(root, directory)
    try:
        names = sorted(os.listdir(path))
    except OSError as exc:
        raise OrphanPromotionLedgerError(E_OPL_NO_EVIDENCE, str(exc))
    files = {}
    for name in names:
        match = FH.NAME_RE.match(name)
        if match is None:
            continue
        label = match.group(1)
        if name != OP.canonical_name(int(label[1:])):
            continue
        files[label] = name
    return path, files


def judge(entries, path, files, round_no, since):
    """The five disjoint readings, with the pinned blocker order (AC-OPL2/3).

    UNRECORDED is scoped by the declaration's own dated `since_round`: a
    canonical file whose round predates the round the ledger came into force
    cannot have been produced by a writer that had a ledger to write to, so it
    is counted as out_of_scope rather than accused. Every entry is judged
    whatever its round, because a backfilled record is still a claim.
    """
    rows = []
    counts = {RECORDED: 0, STALE: 0, EXPIRED: 0, MISSING: 0, UNRECORDED: 0}
    out_of_scope = []
    claimed = set()
    floor = int(parse_round(since)[1:])
    for entry in entries:
        label = entry["round"]
        name = entry["canonical"]
        claimed.add(label)
        if name not in files.values():
            counts[MISSING] += 1
            rows.append({"round": label, "canonical": name, "class": MISSING,
                         "detail": "no such file in the evidence directory"})
            continue
        try:
            live_digest = EV.digest_of(os.path.join(path, name))
        except EV.EvidenceVariantsError:
            raise OrphanPromotionLedgerError(E_OPL_UNREADABLE, name)
        expired = bool(entry["until"]) and \
            int(parse_round(round_no)[1:]) >= int(parse_round(entry["until"])[1:])
        if live_digest != entry["digest"]:
            counts[STALE] += 1
            rows.append({"round": label, "canonical": name, "class": STALE,
                         "detail": "recorded %s, on disk %s"
                                   % (entry["digest"][:12], live_digest[:12])})
        elif expired:
            counts[EXPIRED] += 1
            rows.append({"round": label, "canonical": name, "class": EXPIRED,
                         "detail": "until %s, read at %s"
                                   % (entry["until"], parse_round(round_no))})
        else:
            counts[RECORDED] += 1
            rows.append({"round": label, "canonical": name,
                         "class": RECORDED,
                         "detail": "%d bytes, digest %s"
                                   % (entry["bytes"], entry["digest"][:12])})
    for label in sorted(files, key=lambda item: int(item[1:])):
        if label in claimed:
            continue
        if int(label[1:]) < floor:
            out_of_scope.append({"round": label, "canonical": files[label]})
            continue
        counts[UNRECORDED] += 1
        rows.append({"round": label, "canonical": files[label],
                     "class": UNRECORDED,
                     "detail": "a canonical file no entry claims"})
    return counts, rows, out_of_scope


def check(root, directory="qa", round_no=None):
    """Read-only: the declaration against the live evidence directory."""
    if round_no is None:
        raise OrphanPromotionLedgerError(
            E_OPL_NO_ROUND,
            "expiry needs the round being read; no clock is consulted")
    label = parse_round(round_no)
    text, payload = read_declaration(root)
    entries = declaration_entries(text)
    since = payload["since_round"]
    path, files = canonical_files(root, directory)
    counts, rows, out_of_scope = judge(entries, path, files, label, since)
    debt = counts[STALE] + counts[EXPIRED] + counts[MISSING] + \
        counts[UNRECORDED]
    return {"decl": DECL_REL.replace(os.sep, "/"), "pinned": True,
            "since": since, "round": label, "entries": len(entries),
            "recorded": counts[RECORDED], "stale": counts[STALE],
            "expired": counts[EXPIRED], "missing": counts[MISSING],
            "unrecorded": counts[UNRECORDED], "out_of_scope": len(out_of_scope),
            "canonical": len(files),
            "rows": rows, "verdict": "LEDGER-DEBT" if debt else "CLEAN"}


def splice(text, entry):
    """Insert one entry before the closing bracket, keeping every prior byte."""
    line = json.dumps(entry, ensure_ascii=True, sort_keys=False)
    marker = "\n  ]"
    pos = text.rfind(marker)
    if pos < 0:
        raise OrphanPromotionLedgerError(
            E_OPL_BAD_DECL, "declaration carries no closing bracket")
    head = text[:pos]
    separator = "\n    " if head.rstrip().endswith("[") else ",\n    "
    return head + separator + line + text[pos:]


def _same_entry(reading, entry):
    for key in ENTRY_KEYS:
        if reading.get(key) != entry.get(key):
            return False
    return True


def payload_bytes(raw, post):
    """The bytes to land: the shared dialect law, asked at CALL time."""
    return DWD.encode(raw, post)[1]


def plan(text, entry, path, files, round_no, raw=None):
    """Validate the entry and the post text; return the report and the post."""
    entries = declaration_entries(text)
    label = entry["round"]
    for existing in entries:
        if existing["round"] == label:
            raise OrphanPromotionLedgerError(
                E_OPL_DUP,
                "%s is already recorded as %s by %s until %s"
                % (label, existing["canonical"], existing["declared_by"],
                   existing["until"] or "-"))
    if entry["until"] and \
            int(parse_round(entry["until"])[1:]) < \
            int(parse_round(entry["declared_by"])[1:]):
        raise OrphanPromotionLedgerError(
            E_OPL_UNTIL,
            "until %s is earlier than declared_by %s"
            % (entry["until"], entry["declared_by"]))
    canonical = files.get(label)
    if canonical is None:
        raise OrphanPromotionLedgerError(
            E_OPL_NO_CANONICAL,
            "%s carries no canonical file in %s; nothing to record"
            % (label, os.path.basename(path)))
    try:
        digest = EV.digest_of(os.path.join(path, canonical))
    except EV.EvidenceVariantsError:
        raise OrphanPromotionLedgerError(E_OPL_UNREADABLE, canonical)
    entry["bytes"] = os.path.getsize(os.path.join(path, canonical))
    entry["digest"] = digest
    entry["canonical"] = canonical
    post = splice(text, entry)
    after = declaration_entries(post)
    if len(after) != len(entries) + 1:
        raise OrphanPromotionLedgerError(
            E_OPL_BAD_DECL, "post text carries %d entries, expected %d"
            % (len(after), len(entries) + 1))
    if not _same_entry(after[-1], entry):
        raise OrphanPromotionLedgerError(E_OPL_BAD_DECL,
                                         "post text did not keep the entry")
    for before, kept in zip(entries, after[:-1]):
        if not _same_entry(before, kept):
            raise OrphanPromotionLedgerError(
                E_OPL_BAD_DECL, "post text moved %s" % before["round"])
    report = {}
    for key in ENTRY_KEYS:
        report[key] = entry[key]
    report["path"] = DECL_REL.replace(os.sep, "/")
    report["entry_index"] = len(after)
    report["entry_count_before"] = len(entries)
    report["entry_count_after"] = len(after)
    report["before_bytes"] = len(text.encode("utf-8"))
    report["predicted_bytes"] = len(payload_bytes(
        post.encode("utf-8") if raw is None else raw, post))
    report["wrote"] = False
    report["read_back_ok"] = None
    return report, post


def add(root, round_value, declared_by, until=None, directory="qa",
        source=None, reason="", execute=False):
    """Plan (and optionally perform) one append under root."""
    label = parse_round(round_value)
    text, _payload = read_declaration(root)
    path, files = canonical_files(root, directory)
    entry = render_entry(label, "", source, 0, "", declared_by, until, reason)
    try:
        with io.open(os.path.join(root, DECL_REL), "rb") as handle:
            raw = handle.read()
    except (IOError, OSError) as exc:
        raise OrphanPromotionLedgerError(E_OPL_UNREADABLE,
                                         "%s (%s)" % (DECL_REL, exc))
    report, post = plan(text, entry, path, files, label, raw=raw)
    if not execute:
        return report
    data = payload_bytes(raw, post)
    if len(data) != report["predicted_bytes"]:
        raise OrphanPromotionLedgerError(
            E_OPL_PREDICT, "payload is %d bytes, predicted %d"
            % (len(data), report["predicted_bytes"]))
    target = os.path.join(root, DECL_REL)
    temp = target + TEMP_SUFFIX
    if os.path.exists(temp):
        raise OrphanPromotionLedgerError(
            E_OPL_TEMP_RESIDUE, "%s is already present" % TEMP_SUFFIX)
    try:
        with io.open(temp, "wb") as handle:
            handle.write(data)
        os.replace(temp, target)
    except (IOError, OSError) as exc:
        try:
            if os.path.exists(temp):
                os.remove(temp)
        except (IOError, OSError):
            pass
        raise OrphanPromotionLedgerError(E_OPL_WRITE, "%s (%s)" % (target, exc))
    try:
        with io.open(target, "rb") as back:
            landed = back.read()
    except (IOError, OSError) as exc:
        raise OrphanPromotionLedgerError(E_OPL_READBACK, str(exc))
    if landed != data:
        raise OrphanPromotionLedgerError(
            E_OPL_READBACK, "%s landed %d bytes against %d planned"
            % (target, len(landed), len(data)))
    if os.path.exists(temp):
        raise OrphanPromotionLedgerError(E_OPL_TEMP_RESIDUE, temp)
    report["wrote"] = True
    report["read_back_ok"] = True
    return report


def render(report):
    """One summary line, then one line per row."""
    if "rows" in report:
        out = ["ORPHAN PROMOTION LEDGER decl=%s since=%s entries=%d "
               "canonical=%d recorded=%d stale=%d expired=%d missing=%d "
               "unrecorded=%d out_of_scope=%d verdict=%s"
               % (report["decl"], report["since"], report["entries"],
                  report["canonical"], report["recorded"], report["stale"],
                  report["expired"], report["missing"], report["unrecorded"],
                  report["out_of_scope"], report["verdict"])]
        for row in report["rows"]:
            out.append("  %s %s class=%s %s"
                       % (row["round"], row["canonical"], row["class"],
                          row["detail"]))
        return "\n".join(out)
    out = ["ORPHAN PROMOTION PLAN round=%s canonical=%s source=%s bytes=%d "
           "digest=%s declared_by=%s until=%s"
           % (report["round"], report["canonical"], report["source"] or "-",
              report["bytes"], (report["digest"] or "-")[:12],
              report["declared_by"], report["until"] or "-")]
    out.append("  entries %d -> %d bytes %d -> %d wrote=%s read_back=%s"
               % (report["entry_count_before"], report["entry_count_after"],
                  report["before_bytes"], report["predicted_bytes"],
                  "yes" if report["wrote"] else "no",
                  report["read_back_ok"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    keys = REPORT_KEYS if "rows" in report else PLAN_KEYS
    ordered = {}
    for key in keys:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: orphan_promotion_ledger.py --check [DIR] --round R\n"
         "       orphan_promotion_ledger.py --add ROUND --declared-by R\n"
         "                                   [--until R] [DIR] [--source LEG]\n"
         "                                   [--reason TEXT] [--execute]\n"
         "  DIR defaults to qa; --check writes nothing at all\n"
         "  exit 0 = clean, or a plan/appended record\n"
         "  exit 2 = debt (stale, expired, missing, unrecorded) or a refused\n"
         "           append over live state, and nothing was written\n"
         "  exit 3 = declaration absent or malformed, evidence absent or\n"
         "           undecodable\n"
         "  exit 5 = bad flags\n")


def parse_args(argv):
    """Flags only; returns the parsed request or raises on bad flags."""
    request = {"mode": None, "as_json": False, "directory": "qa",
               "root": os.path.dirname(os.path.dirname(os.path.dirname(
                   os.path.abspath(__file__)))),
               "round": None, "declared_by": None, "until": None,
               "source": None, "reason": "", "execute": False,
               "operands": []}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--check", "--add"):
            if request["mode"] is not None:
                raise OrphanPromotionLedgerError(E_OPL_BAD_ARGS,
                                                 "one mode only")
            request["mode"] = "check" if arg == "--check" else "add"
        elif arg == "--json":
            request["as_json"] = True
        elif arg == "--execute":
            request["execute"] = True
        elif arg in ("--round", "--declared-by", "--until", "--source",
                     "--reason", "--root"):
            index += 1
            if index >= len(argv):
                raise OrphanPromotionLedgerError(E_OPL_BAD_ARGS,
                                                 "%s needs a value" % arg)
            key = {"--round": "round", "--declared-by": "declared_by",
                   "--until": "until", "--source": "source",
                   "--reason": "reason", "--root": "root"}[arg]
            request[key] = argv[index]
        elif arg in ("--help", "-h"):
            request["mode"] = "help"
        elif arg.startswith("-"):
            raise OrphanPromotionLedgerError(E_OPL_BAD_ARGS,
                                             "unknown flag %s" % arg)
        else:
            request["operands"].append(arg)
        index += 1
    if request["mode"] in (None, "help"):
        return request
    if request["mode"] == "add" and request["round"] is None and \
            request["operands"]:
        request["round"] = request["operands"].pop(0)
    if len(request["operands"]) > 1:
        raise OrphanPromotionLedgerError(E_OPL_BAD_ARGS, "too many operands")
    if request["operands"]:
        request["directory"] = request["operands"][0]
    if request["mode"] == "check":
        if request["round"] is None:
            raise OrphanPromotionLedgerError(
                E_OPL_BAD_ARGS, "--check needs --round")
        if request["execute"]:
            raise OrphanPromotionLedgerError(E_OPL_BAD_ARGS,
                                             "--check writes nothing")
    else:
        if request["round"] is None:
            raise OrphanPromotionLedgerError(E_OPL_BAD_ARGS,
                                             "--add needs a round")
        if request["declared_by"] is None:
            raise OrphanPromotionLedgerError(E_OPL_BAD_ARGS,
                                             "--add needs --declared-by")
    return request


def main(argv):
    try:
        request = parse_args(argv)
    except OrphanPromotionLedgerError as exc:
        sys.stdout.write("%s\n" % exc)
        sys.stdout.write(USAGE)
        return 5
    if request["mode"] in (None, "help"):
        sys.stdout.write(USAGE)
        return 5 if request["mode"] is None else 0
    try:
        if request["mode"] == "check":
            report = check(request["root"], request["directory"],
                           request["round"])
        else:
            report = add(request["root"], request["round"],
                         request["declared_by"], request["until"],
                         request["directory"], request["source"],
                         request["reason"], request["execute"])
    except OrphanPromotionLedgerError as exc:
        sys.stdout.write("%s\n" % exc)
        if exc.code in (E_OPL_NO_DECL, E_OPL_BAD_DECL, E_OPL_NO_EVIDENCE,
                        E_OPL_UNREADABLE):
            return 3
        if exc.code in (E_OPL_BAD_ARGS, E_OPL_BAD_ROUND, E_OPL_NO_ROUND):
            return 5
        return 2
    if request["as_json"]:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report.get("verdict") == "LEDGER-DEBT":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))