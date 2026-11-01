"""R2331 closeout part 2: record the residue renewal and the canon repair.

Two log items only, appended with a predicted byte count, one canonical
atomic write and a read-back proof. Pure ASCII, stdlib only, no network.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")

ITEMS = [
    "R2331 residue renewal (measured, not assumed): with the fold applied the "
    "triage declaration read residue=195 triaged=0 untriaged=195 "
    "verdict=RESIDUE, because every entry carried until=R2330 and the fold "
    "moved whole round blocks into the archive (the fold-creates-residue law "
    "first measured at R2311). src/os/renew_residue_R2331.py builds ONE new "
    "declaration from ONE live stamp_residue reading, importing the R2310 "
    "pinner own entry shape and stable text writer rather than adding a second "
    "generator, with declared_by=R2331 and until=R2350; the write is one "
    "atomic replace with a predicted byte count (33306B equal to measured), no "
    "temp residue, and the file is then re-read through residue_triage itself, "
    "which answers verdict=TRIAGED residue=0 triaged=195 untriaged=0 "
    "expired=0. The renewal is idempotent (a second run reconstructs the same "
    "33306B), so the successor window can re-measure instead of trusting this "
    "line.",
    "R2331 canon repair disclosed: at open state.json measured 78731B with "
    "crlf=0, bare_lf=135 and 63 of 63 log items off the 16-space indent - the "
    "R2330 closeout left it off the write canon, the same class repaired at "
    "R2317, R2299 and R2246. It was repaired through state_io --fix --execute "
    "BEFORE any fold or append (78731B -> 79622B, payload proven equal, "
    "layout_ok=True after), and only then did fold 621 run (log lines 2..9, the "
    "R2310..R2316 blocks, verbatim into logs/state-log-archive-2026-11.md, "
    "predicted 71324B equal to measured 71324B, 56 live log lines, archive "
    "203216B) followed by the four-item append (76639B, margin 1861B under the "
    "78500B gate). Two this-window script defects are also disclosed: the "
    "first fold call passed text where plan_fold wants raw bytes, and the fold "
    "print read result keys the callable does not carry - both were fixed in "
    "the closeout helper after the fold had already applied, and the numbers "
    "above are the post-repair re-readings, never a claim made before the "
    "write.",
]


def main():
    raw = io.open(STATE, encoding="utf-8", newline="").read()
    before = len(raw.encode("utf-8"))
    data = json.loads(raw)
    for item in ITEMS:
        if item in data["log"]:
            raise SystemExit("E_R2331P_ALREADY")
    data["log"].extend(ITEMS)
    canon = SIO.canon(json.dumps(data, ensure_ascii=False, indent=2))
    predicted = len(canon.encode("utf-8"))
    tmp = STATE + ".tmp-r2331p2"
    with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(canon)
    written = os.path.getsize(tmp)
    if written != predicted:
        os.remove(tmp)
        raise SystemExit("E_R2331P_PREDICT %d != %d" % (written, predicted))
    os.replace(tmp, STATE)
    if os.path.exists(tmp):
        raise SystemExit("E_R2331P_TEMP")
    back = json.loads(io.open(STATE, encoding="utf-8", newline="").read())
    layout = SIO.layout(io.open(STATE, encoding="utf-8", newline="").read())
    print("state before=%dB after=%dB log_len=%d tick=%d layout_ok=%r"
          % (before, os.path.getsize(STATE), len(back["log"]), back["tick"],
             layout.get("layout_ok")))


if __name__ == "__main__":
    main()