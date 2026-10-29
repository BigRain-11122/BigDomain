# export_derived_R2250.py - re-apply only the derived self_drive block.
# The seed row landed after the first export refresh, so the stored
# queue_tech_open count fell one behind the live queue. This writer touches
# nothing but the checker's own recompute() keys: no row is inserted, no
# face line is rewritten, and the tick row is left exactly as it is.
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_export_consistency as cec  # noqa: E402

EXPORT = os.path.join(ROOT, "docs", "status-export.json")


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
    with open(EXPORT, "r", encoding="utf-8", newline="") as handle:
        raw = handle.read()
    if raw.count("\r\n") != raw.count("\n"):
        raise SystemExit("mixed line endings - refusing to edit")
    text = raw.replace("\r\n", "\n")
    derived, state, export, pat = cec.recompute()
    for key, want in sorted(derived.items()):
        text = replace_line(text, key, want)
    data = json.loads(text)
    assert data["self_drive"] == dict(data["self_drive"], **derived)
    with open(EXPORT, "w", encoding="utf-8", newline="") as handle:
        handle.write(text.replace("\n", "\r\n"))
    print("EXPORT derived=%d tick_row=%s bytes=%d"
          % (len(derived), state["tick"], len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())