# closeout_R2264.py - textual append of this window's log items.
# Keeps the canonical layout (CRLF, 16-space items) by splicing before
# the closing bracket instead of re-serializing the whole document.
# Pure stdlib, pure ASCII source.
import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "state.json")

ITEMS = [
    "R2264 verification window on the debt register first item"
    " (product-face-R2264 = reconcile battery): the register named the"
    " battery first=yes because R2263 changed src/os, so this window"
    " changed zero product code (the R2168 mixed-tree rule) and ran the"
    " full battery on the committed tree. RUNNER PASS 436/436 suites"
    " green plus reconcile controls 7/7 in 856.5s with birth-site TMP"
    " RECLAIM 932/932 worlds 326.57 MiB busy=0 failed=0"
    " (qa/reconcile-all-R2264.log, single-writer utf-8 LF through"
    " src/os/battery_stream.py, never a shell redirection), expected"
    " criteria total=3593. Four follow-up sections all PASS through the"
    " new src/os/battery_followup_R2264.py (same shape as R2262, only"
    " the evidence path and the round label changed): matrix regenerated"
    " to 436 suites / 3593 criteria and read back byte-identical"
    " (docs/sandbox-suite-matrix.md, 42342B, green=436/436), fingerprint"
    " chain CLEAN over 5 domains, runner profile --daily --check PASS,"
    " writer census re-frozen then DRIFT-CLEAN files=2210 tee=1681"
    " baselined=529 disappeared=0 flags=0, closing on VERDICT PASS with"
    " the log own EOL self-check crlf=0 bare_cr=0 bom=False over 769785B."
    " The measured deltas against R2262 (435 suites / 3587 criteria) are"
    " +1 suite and +6 criteria, exactly the R2263 os-queue-only suite"
    " joining the registry, so the newest slice is now covered by the"
    " whole battery and not only by its own suite plus neighbours. Honest"
    " score: a 0-point verification window with no product face;"
    " state.json measures 61289B+ against the 78500B waterline, so no"
    " fold is due. Register row closed and the successor"
    " product-face-R2265 opened as first=yes.",
    "R2264 heartbeat debt backfilled: heartbeat.txt carried tick 2259 at"
    " the open while state.json carried tick 2263 (lag 237 by the scan"
    " gauge, four rounds of rows missing), so rows 2260..2264 were"
    " appended from the state.json log rather than invented, and the"
    " last row now names this round.",
    "R2264 tokens: local=~9k api=0 api_reason=verification window - one"
    " battery run plus four read-only follow-up sections, no generative"
    " call of any kind",
]


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    state = json.loads(text)
    before = len(state["log"])
    tail = "\r\n  ]\r\n}\r\n"
    if not text.endswith(tail):
        print("REFUSE: unexpected tail")
        return 2
    body = text[:-len(tail)]
    chunks = []
    for item in ITEMS:
        chunks.append(",\r\n                " + json.dumps(item))
    new_text = body + "".join(chunks) + tail
    new_text = new_text.replace('"tick": %d,' % state["tick"],
                                '"tick": %d,' % (state["tick"] + 1), 1)
    out = new_text.encode("utf-8")
    io.open(PATH, "wb").write(out)
    check = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = (check["tick"] == state["tick"] + 1
          and len(check["log"]) == before + len(ITEMS)
          and check["log"][-1] == ITEMS[-1])
    crlf = out.decode("utf-8").count("\r\n")
    print("APPEND items=%d tick=%d->%d log=%d->%d crlf=%d bytes=%d ok=%s"
          % (len(ITEMS), state["tick"], check["tick"], before,
             len(check["log"]), crlf, len(out), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())