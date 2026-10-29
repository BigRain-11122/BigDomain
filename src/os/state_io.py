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
ITEM_INDENT = 16
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
        if line.strip().startswith('"log": ['):
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


def layout(text):
    """Measure the layout of a state document from its own bytes."""
    lines = _lf_lines(text)
    data = parse(text)
    start, end = _log_block(lines)
    log = data.get("log") if isinstance(data, dict) else None
    if not isinstance(log, list):
        raise StateIOError("E_SIO_LAYOUT", "state.json has no log array")
    items = [index for index in range(start + 1, end)
             if lines[index].strip().startswith('"')]
    off = [index for index in items
           if len(lines[index]) - len(lines[index].lstrip(" ")) != ITEM_INDENT]
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


def canon(text):
    """Return the canonical text. Refuses rather than guesses."""
    measured = layout(text)
    if not measured["count_ok"]:
        raise StateIOError("E_SIO_LAYOUT",
                           "%d item lines for a log of %d entries"
                           % (measured["log_items"], measured["log_len"]))
    lines = _lf_lines(text)
    start, end = _log_block(lines)
    for index in range(start + 1, end):
        stripped = lines[index].strip()
        if stripped.startswith('"'):
            lines[index] = " " * ITEM_INDENT + stripped
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
            "previous": None if previous is None else len(previous)}


def report(path):
    return layout(decode(read_raw(path)))


def fix(path, execute=False):
    """Plan (or perform) the canonical rewrite of one state file."""
    raw = read_raw(path)
    text = decode(raw)
    before = layout(text)
    if before["layout_ok"]:
        return {"verdict": "CANON-CLEAN", "before": before,
                "predicted_bytes": len(raw), "written": 0,
                "execute": bool(execute)}
    planned = canon(text)
    predicted = len(planned.encode("utf-8"))
    out = {"verdict": "CANON-DRIFT", "before": before,
           "predicted_bytes": predicted, "written": 0,
           "execute": bool(execute)}
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