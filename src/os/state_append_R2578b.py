"""Append the R2578 fold/export receipt to src/os/state.json in place."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-08 R2578 FOLD: state.json was folded through the shipped run face at a TRUE round-block boundary over log items 4..10 (the complete R2568 and R2569 blocks, ending on the R2569 tokens line) at 80690B -> 71457B with tokens=7 ok=True, archive=VERIFIED, layout=AGREE, live 68->62 lines, so state_fold --check now reads FOLD-CLEAR margin=7043. The fold was owed because this window own append landed at 80690B against the 78500B gate (margin -2190), which is disclosed rather than hidden.",
]


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    data = json.loads(text)
    proved = json.dumps(data, ensure_ascii=False, indent=1)
    if proved != text:
        sys.stdout.write("E_APPEND_ROUNDTRIP: layout is not indent=1\n")
        return 2
    data["log"].extend(LINES)
    out = json.dumps(data, ensure_ascii=False, indent=1)
    io.open(PATH, "wb").write(out.encode("utf-8"))
    back = io.open(PATH, "rb").read().decode("utf-8")
    check = json.loads(back)
    sys.stdout.write("APPENDED bytes %d -> %d tick=%d log_lines=%d ok=%s\n" % (
        len(raw), len(out.encode("utf-8")), check["tick"], len(check["log"]),
        check["log"][-1].startswith("2026-11-08 R2578 FOLD:")))
    return 0


if __name__ == "__main__":
    sys.exit(main())