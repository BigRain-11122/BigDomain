"""Append the R2579 FOLD line to src/os/state.json in place."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-08 R2579 FOLD: state.json was folded through the shipped run face at a TRUE round-block boundary over log items 4..6 (the complete R2570 block, ending on the R2570 tokens line) with fold-no 654 at 81361B -> 78110B, tokens=4 ok=True, archive=VERIFIED, layout=AGREE, live 72->70 lines, so state_fold --check now reads FOLD-CLEAR margin=390. The fold was owed because this window own append landed at 81361B against the 78500B gate (margin -2861), which is disclosed rather than hidden. A first window 1..7 and a bare 5..7 were REFUSED by the shipped predicate with token-missing and wrote nothing; the token list of the folded items was measured from the live log rather than guessed and carried verbatim in the summary line.",
]


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    data = json.loads(text)
    if json.dumps(data, ensure_ascii=False, indent=1) != text:
        sys.stdout.write("E_APPEND_ROUNDTRIP: layout is not indent=1\n")
        return 2
    data["log"].extend(LINES)
    out = json.dumps(data, ensure_ascii=False, indent=1)
    io.open(PATH, "wb").write(out.encode("utf-8"))
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    sys.stdout.write("APPENDED bytes %d -> %d log_lines=%d ok=%s\n" % (
        len(raw), len(out.encode("utf-8")), len(back["log"]),
        back["log"][-1].startswith("2026-11-08 R2579 FOLD:")))
    return 0


if __name__ == "__main__":
    sys.exit(main())