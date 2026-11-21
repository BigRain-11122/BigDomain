"""state.json write canon as one callable (R2246).

Why this exists: the live state file has drifted to bare LF with its log items
off the canonical 16-space indent twice now (R2243 repaired it by hand with
logs_toolkit, the R2245 closeout reintroduced it). The repair was never the
problem - the unnamed writer was. This module owns both sides: it measures the
layout from real bytes (layout), it rewrites the file to the canon while
proving the JSON payload did not move (canon), and it writes atomically with a
read-back proof while refusing any payload change (write_canon).

Canon as measured on the file at HEAD 2026-10-29: CRLF line endings, top-level
keys at two spaces, every element of the "log" array at exactly sixteen spaces,
the closing bracket at two and the object brace at column zero.

Stdlib only, ASCII source, zero network, zero subprocess.

CLI:
  python state_io.py [--root ROOT] [--check | --fix [--execute]] [--json]
Exit: 0 = canonical, 2 = drift (dry run) or bad flags, 3 = unreadable.
"""

import json
import os
import sys
import tempfile

EOL = "\r\n"
# The writer target is the LIVE canon (sixteen spaces), not the two-space form
# this constant carried until R3179: the shipped carrier gate reads the live
# file clean while this module called it drifted, and a repair through this
# module would have rewritten the file into a shape that gate flags (R3179).
ITEM_INDENT = 16
# Both uniform indents are healthy per the carrier gate (R2747); anything else
# is disease. Measured from the document, never hardcoded per file.
LOG_ITEM_CALIBERS = (2, 16)
PINS = ("bytes", "crlf", "bare_lf", "lone_cr", "eol_ok", "log_items",
        "log_len", "items_off_indent", "indent_ok", "count_ok", "layout_ok")


class StateIOError(Exception):
    """A refused operation. The code is stable and part of the contract."""

    def __init__(self, code, message):
        Exception.__init__(self, "%s: %s" % (code, message))
        self.code = code
        self.message = message


def read_raw(path):
    with open(path, "rb") as handle:
        return handle.read()


def decode(raw):
    if raw.startswith(b"\xef\xbb\xbf"):
        raise StateIOError("E_SIO_BOM", "byte order mark present")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StateIOError("E_SIO_UTF8", str(exc))


def parse(text):
    try:
        return json.loads(text)
    except ValueError as exc:
        raise StateIOError("E_SIO_JSON", str(exc))


def _lf_lines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _log_block(lines):
    start = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('"log": [') or stripped.startswith('"log":['):
            start = index
            break
    if start is None:
        raise StateIOError("E_SIO_LAYOUT", "no log block in the state file")
    end = None
    for index in range(start + 1, len(lines)):
        if lines[index].strip() in ("]", "],"):
            end = index
            break
    if end is None:
        raise StateIOError("E_SIO_LAYOUT", "unterminated log block")
    return start, end


def _item_lines(lines, start, end):
    """Every line inside the log block that carries an entry (R3181).

    The detector used to accept only lines starting with a quote, so a payload
    whose log holds an object or a number was written one-per-line and then
    read back as zero items: the writer landed a document its own reader called
    drifted, and canon() could not repair it either. The bracket lines that
    bound the block are the only non-item lines.
    """
    return [index for index in range(start + 1, end)
            if lines[index].strip() not in ("", "]", "],")]


def layout(text):
    """Measure the layout of a state document from its own bytes."""
    lines = _lf_lines(text)
    data = parse(text)
    start, end = _log_block(lines)
    log = data.get("log") if isinstance(data, dict) else None
    if not isinstance(log, list):
        raise StateIOError("E_SIO_LAYOUT", "state.json has no log array")
    items = _item_lines(lines, start, end)
    indents = set(len(lines[index]) - len(lines[index].lstrip(" "))
                  for index in items)
    caliber = next(iter(indents)) if len(indents) == 1 else None
    if caliber not in LOG_ITEM_CALIBERS:
        caliber = None
    off = [index for index in items
           if caliber is None
           or len(lines[index]) - len(lines[index].lstrip(" ")) != caliber]
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    lone_cr = text.count("\r") - crlf
    eol_ok = crlf > 0 and lf == 0 and lone_cr == 0
    count_ok = len(items) == len(log)
    indent_ok = not off
    return {
        "bytes": len(text.encode("utf-8")),
        "crlf": crlf,
        "bare_lf": lf,
        "lone_cr": lone_cr,
        "eol_ok": eol_ok,
        "log_items": len(items),
        "log_len": len(log),
        "items_off_indent": len(off),
        "indent_ok": indent_ok,
        "count_ok": count_ok,
        "layout_ok": eol_ok and count_ok and indent_ok,
    }


def dump_canon(data):
    """Emit the canonical text for a payload, preserving key order (R2738).

    Why this exists: a minified document carries no log block, so the shipped
    indentation-only rewrite has nothing to re-indent and refuses. A drift the
    repair path cannot even measure is a drift nothing can fix, which is how a
    one-line writer poisoned this file unnoticed. This rebuilds the document
    from its own payload instead of from its broken layout.
    """
    if not isinstance(data, dict):
        raise StateIOError("E_SIO_LAYOUT", "state document is not an object")
    log = data.get("log")
    if not isinstance(log, list):
        raise StateIOError("E_SIO_LAYOUT", "state.json has no log array")
    keys = list(data.keys())
    lines = ["{"]
    for index, key in enumerate(keys):
        tail = "" if index == len(keys) - 1 else ","
        if key == "log":
            lines.append('  "log": [')
            for item_index, item in enumerate(log):
                item_tail = "" if item_index == len(log) - 1 else ","
                lines.append(" " * ITEM_INDENT
                             + json.dumps(item, ensure_ascii=False)
                             + item_tail)
            lines.append("  ]" + tail)
        else:
            lines.append("  " + json.dumps(key, ensure_ascii=False) + ":"
                         + json.dumps(data[key], ensure_ascii=False) + tail)
    lines.append("}")
    return EOL.join(lines) + EOL


def canon(text):
    """Return the canonical text. Refuses rather than guesses."""
    try:
        measured = layout(text)
    except StateIOError as exc:
        if exc.code != "E_SIO_LAYOUT":
            raise
        rebuilt = dump_canon(parse(text))
        if parse(rebuilt) != parse(text):
            raise StateIOError("E_SIO_JSON", "canon moved the payload")
        return rebuilt
    if not measured["count_ok"]:
        raise StateIOError("E_SIO_LAYOUT",
                           "%d item lines for a log of %d entries"
                           % (measured["log_items"], measured["log_len"]))
    lines = _lf_lines(text)
    start, end = _log_block(lines)
    for index in _item_lines(lines, start, end):
        lines[index] = " " * ITEM_INDENT + lines[index].strip()
    out = EOL.join(lines)
    if parse(out) != parse(text):
        raise StateIOError("E_SIO_JSON", "canon moved the payload")
    return out


def write_canon(path, new_text):
    """Atomic canonical write that can never change the JSON payload."""
    new_bytes = new_text.encode("utf-8")
    previous = None
    if os.path.exists(path):
        previous = read_raw(path)
        if parse(decode(previous)) != parse(new_text):
            raise StateIOError("E_SIO_JSON",
                               "refusing a write that changes the payload")
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_io_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(new_bytes)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = read_raw(path)
    if back != new_bytes:
        raise StateIOError("E_SIO_BACK", "read-back does not match the write")
    return {"written": len(new_bytes),
            "previous": None if previous is None else len(previous),
            "carrier": carrier_face(back)}


def write_document(path, payload):
    """Atomic canonical write of a NEW payload (the round closeout path).

    write_canon deliberately refuses any payload change, so the rounds that do
    have to move the tick had no canonical writer and reached for a bare
    json.dump - which is exactly how the one-line form arrived. This is that
    missing writer: it dumps the canon, proves the dump round-trips, writes
    atomically and refuses to return unless the file reads back canonical.
    """
    text = dump_canon(payload)
    if parse(text) != payload:
        raise StateIOError("E_SIO_JSON", "dump_canon moved the payload")
    # Ask the same measurement BEFORE the bytes can land (R3181): the check
    # used to run after os.replace, so a divergent indent or an entry the
    # reader could not see left the bad shape on disk and then refused - a
    # document the writer itself calls drifted is worse than no write at all.
    planned = layout(text)
    if not planned["layout_ok"]:
        raise StateIOError("E_SIO_LAYOUT",
                           "document would not read clean (%d item lines for "
                           "a log of %d entries); nothing written"
                           % (planned["log_items"], planned["log_len"]))
    new_bytes = text.encode("utf-8")
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".state_io_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(new_bytes)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = read_raw(path)
    if back != new_bytes:
        raise StateIOError("E_SIO_BACK", "read-back does not match the write")
    after = report(path)
    if not after["layout_ok"]:
        raise StateIOError("E_SIO_LAYOUT", "document write did not read clean")
    return {"written": len(new_bytes), "after": after,
            "carrier": carrier_face(back)}


def report(path):
    return layout(decode(read_raw(path)))


def carrier_face(raw):
    """Publish every shipped reading of the same bytes by name (R3180).

    This module can only speak for itself: a writer that publishes one verdict
    lets its consumer believe a document is foldable when the fold door reads
    it otherwise, which is exactly how the R3176/R3178 carrier debt was born.
    Both answers are named rather than merged (a two-space document is healthy
    here while the fold door reads only its own caliber), and a document this
    face cannot measure is reported as an error instead of refused - a reading
    must never change the write contract.

    The name `layout_ok` means three different things across the shipped tree
    (R3182 measured): in logs_toolkit.eol_profile it is the EOL face ONLY, in
    this module it is EOL plus count plus indent, and in the closeout gate
    CARRIER row it is the conjunction of the first two. Publishing the gate
    EOL face under the name `gate_layout_ok` therefore invited a reader to
    compare two different concepts and see a split that does not exist on the
    composite: a uniform eight-space file reads EOL-clean and indent-dirty on
    the gate, exactly as this module reads it un-clean, so both refuse it.
    The EOL face is published as `gate_eol_ok` and the composite the closeout
    gate actually uses is published as `gate_health`; `agree` compares like
    with like.
    """
    import logs_toolkit  # lazy: the gate imports nothing from this module
    try:
        text = decode(raw)
        mine = layout(text)
        payload = parse(text)
        log_len = (len(payload.get("log") or [])
                   if isinstance(payload, dict) else 0)
        prof = logs_toolkit.eol_profile(raw)
        gate_eol = bool(prof.get("layout_ok"))
        gate_indent = bool(prof.get("indent_ok"))
        gate_health = gate_eol and gate_indent
        return {
            "bytes": len(raw),
            "layout_ok": mine["layout_ok"],
            "indent_ok": mine["indent_ok"],
            "gate_eol_ok": gate_eol,
            "gate_indent_ok": gate_indent,
            "gate_health": gate_health,
            "fold_readable": (logs_toolkit.split_ps_layout(text, log_len)
                              is not None),
            "agree": mine["layout_ok"] == gate_health,
        }
    except StateIOError as exc:
        return {"bytes": len(raw), "error": exc.code, "agree": False}
    except Exception as exc:  # a reading never masks the writer contract
        return {"bytes": len(raw), "error": type(exc).__name__,
                "agree": False}


def fix(path, execute=False):
    """Plan (or perform) the canonical rewrite of one state file."""
    raw = read_raw(path)
    text = decode(raw)
    try:
        before = layout(text)
    except StateIOError as exc:
        if exc.code != "E_SIO_LAYOUT":
            raise
        before = {"bytes": len(raw), "crlf": text.count("\r\n"),
                  "bare_lf": text.count("\n") - text.count("\r\n"),
                  "lone_cr": 0,
                  "eol_ok": False,
                  "log_items": 0,
                  "log_len": len(parse(text).get("log") or []),
                  "items_off_indent": 0,
                  "indent_ok": False,
                  "count_ok": False,
                  "layout_ok": False}
    if before["layout_ok"]:
        return {"verdict": "CANON-CLEAN", "before": before,
                "predicted_bytes": len(raw), "written": 0,
                "execute": bool(execute), "carrier": carrier_face(raw)}
    planned = canon(text)
    predicted = len(planned.encode("utf-8"))
    out = {"verdict": "CANON-DRIFT", "before": before,
           "predicted_bytes": predicted, "written": 0,
           "execute": bool(execute), "carrier": carrier_face(raw)}
    if not execute:
        return out
    written = write_canon(path, planned)
    after = report(path)
    out["written"] = written["written"]
    out["after"] = after
    if out["written"] != predicted:
        raise StateIOError("E_SIO_PREDICT",
                           "post bytes %d != predicted %d"
                           % (out["written"], predicted))
    if not after["layout_ok"]:
        raise StateIOError("E_SIO_LAYOUT", "canon write did not read clean")
    out["verdict"] = "CANON-FIXED"
    out["carrier"] = carrier_face(read_raw(path))
    return out


def _default_root():
    return os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))


def main(argv):
    root = _default_root()
    mode = "check"
    execute = False
    as_json = False
    rest = list(argv)
    while rest:
        flag = rest.pop(0)
        if flag == "--root":
            if not rest:
                return 2
            root = rest.pop(0)
        elif flag == "--check":
            mode = "check"
        elif flag == "--fix":
            mode = "fix"
        elif flag == "--execute":
            execute = True
        elif flag == "--json":
            as_json = True
        else:
            return 2
    path = os.path.join(root, "src", "os", "state.json")
    try:
        if mode == "fix":
            out = fix(path, execute=execute)
        else:
            measured = report(path)
            out = {"verdict": "CANON-CLEAN" if measured["layout_ok"]
                   else "CANON-DRIFT", "before": measured,
                   "predicted_bytes": measured["bytes"], "written": 0,
                   "execute": False}
    except StateIOError as exc:
        out = {"error": exc.code, "message": exc.message}
        if as_json:
            print(json.dumps(out, sort_keys=True))
        else:
            print("STATE IO ERROR %s" % exc.code)
        return 3
    except (IOError, OSError) as exc:
        out = {"error": "E_SIO_READ", "message": str(exc)}
        if as_json:
            print(json.dumps(out, sort_keys=True))
        else:
            print("STATE IO ERROR E_SIO_READ")
        return 3
    if as_json:
        print(json.dumps(out, sort_keys=True))
    else:
        before = out["before"]
        print("STATE IO %s bytes=%d crlf=%d bare_lf=%d lone_cr=%d "
              "log_items=%d off_indent=%d predicted=%d written=%d"
              % (out["verdict"], before["bytes"], before["crlf"],
                 before["bare_lf"], before["lone_cr"], before["log_items"],
                 before["items_off_indent"], out["predicted_bytes"],
                 out["written"]))
    return 0 if out["verdict"] in ("CANON-CLEAN", "CANON-FIXED") else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))