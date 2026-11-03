# closeout_export_R2418.py - re-apply the checker's own derived keys AND the
# tick row in the document's OWN line-ending dialect.
#
# Two defects met here, both measured rather than assumed: (a) the historical
# export_derived_R2250 writer refuses a pure-LF document with "mixed line
# endings" because it compares CRLF count against LF count (0 != 292 on an
# LF file), and then writes CRLF regardless - so on an LF document it either
# refuses or flips the whole file's transport; (b) the tick row lives in
# results, which that writer deliberately leaves alone. This writer touches
# nothing but those two faces and preserves the dialect it found.
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(BASE, "..", ".."))
sys.path.insert(0, BASE)
import check_export_consistency as cec  # noqa: E402

EXPORT = os.path.join(ROOT, "docs", "status-export.json")
PATTERNS = os.path.join(BASE, "export_consistency_patterns.json")


def dialect(raw):
    crlf = raw.count("\r\n")
    lf = raw.count("\n")
    if crlf == lf:
        return "\r\n"
    if crlf == 0:
        return "\n"
    raise SystemExit("mixed line endings - refusing to edit")


def replace_line(text, key, value):
    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines)
            if line.strip().startswith(json.dumps(key) + ": ")]
    if len(hits) != 1:
        raise SystemExit("line anchor not unique: %s (%d)" % (key, len(hits)))
    line = lines[hits[0]]
    indent = line[:len(line) - len(line.lstrip())]
    tail_comma = line.rstrip().endswith(",")
    lines[hits[0]] = (indent + json.dumps(key) + ": "
                      + json.dumps(value, ensure_ascii=True)
                      + ("," if tail_comma else ""))
    return "\n".join(lines)


def main():
    with io.open(EXPORT, "r", encoding="utf-8", newline="") as handle:
        raw = handle.read()
    eol = dialect(raw)
    text = raw.replace("\r\n", "\n")
    derived, state, export, pat = cec.recompute()
    for key, want in sorted(derived.items()):
        text = replace_line(text, key, want)
    data = json.loads(text)
    assert data["self_drive"] == dict(data["self_drive"], **derived)
    label = pat["tick_row_label"]
    tick = str(state["tick"])
    rows = [row for row in data["results"]
            if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(rows) != 1:
        raise SystemExit("E_TICK ROW count=%d" % len(rows))
    old = rows[0][0]
    rows[0][0] = tick
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with io.open(EXPORT, "w", encoding="utf-8", newline="") as handle:
        handle.write(text.replace("\n", eol))
    with io.open(EXPORT, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    again = dialect(back)
    ok = (again == eol
          and json.loads(back)["self_drive"] == data["self_drive"]
          and str(json.loads(back)["results"][0][0]) == tick)
    print("EXPORT derived=%d tick_row %s -> %s eol=%r unchanged=%s bytes=%d"
          % (len(derived), old, tick, eol, ok,
             os.path.getsize(EXPORT)))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())