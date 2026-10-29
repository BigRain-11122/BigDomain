"""R2248 queue closeout: mark the claimed tech-head row done, then
recompute the export's derived faces (the queue counts move when a row
closes, and the export must be flushed on the same caliber the checker
recomputes with)."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402

P_TECH = os.path.join(ROOT, "state", "queue", "tech.md")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")

OLD = "- [ ] P2 tech seed (R2240 c): `state/debt.md` plus a checker"
NEW = ("- [x] [done 2026-10-29 R2248] P2 tech seed (R2240 c): "
       "`state/debt.md` plus a checker")


def main():
    with io.open(P_TECH, "r", encoding="utf-8") as handle:
        text = handle.read()
    if NEW in text:
        print("QUEUE row already closed")
    else:
        if OLD not in text:
            print("E_QROW_NOT_FOUND")
            return 1
        text = text.replace(OLD, NEW, 1)
        data = text.encode("utf-8")
        with io.open(P_TECH, "wb") as handle:
            handle.write(data)
        print("QUEUE closed one tech row (%d bytes)" % len(data))

    with io.open(P_EXPORT, "r", encoding="utf-8") as handle:
        export = json.loads(handle.read())
    self_drive, _state, _export, _patterns = CEC.recompute()
    export["self_drive"] = self_drive
    body = json.dumps(export, indent=2, ensure_ascii=False)
    if not body.endswith("\n"):
        body += "\n"
    data = body.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
    with io.open(P_EXPORT, "wb") as handle:
        handle.write(data)
    print("EXPORT self_drive=%s" % json.dumps(self_drive))
    return 0


if __name__ == "__main__":
    sys.exit(main())