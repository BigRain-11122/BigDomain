"""R2502 final receipt: the seed row, the push line and the self-heal check."""

import io
import json
import sys

P = "src/os/state.json"
LINES = [
    "2026-11-07 R2502 FLOOR RESTORED FROM A MEASUREMENT, NOT PADDING: closing the claim took tech from 10 claimable to 9, so one row was seeded from this window's own reading - suite_matrix.load_patterns reads the patterns file with json.load and render() interpolates every label verbatim, so the shipped render command still publishes a mis-encoded label into the CEO-visible artifact and the gate shipped above only protects callers that choose publish(). Seed row AC-PLRC1..AC-PLRC6 pinned at state/queue/tech.md:540 BEFORE any code, queue_head now reads prefix=AC-PLRC1 claimable=10, and no other queue row was touched.",
    "2026-11-07 R2502 push: git push origin main SUCCEEDED twice this window - the product commit a4393852..161ad687, then the battery closeout 161ad687..74a4beee - and git rev-parse read HEAD equal to origin/main at 74a4beee before this receipt was written, so nothing is left staged. The export is re-derived through the shipped driver AFTER these lines land (the R2449/R2433 ordering law) and the driver carries the queue face itself, so the document the CEO reads reports queue=CURRENT with no drift rather than needing a hand-landed block.",
    "2026-11-07 R2502 self-heal check: BigDomain-OSLoop exists and reads Running, but its Principal.LogonType still reads Interactive, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again and is carried as the stale row loop-s4u-reconcile, the only row still open on the register.",
]


def main():
    raw = io.open(P, "rb").read()
    text = raw.decode("utf-8")
    tail = "\r\n  ]\r\n}\r\n"
    if not text.endswith(tail):
        print("FAIL state tail %r" % text[-30:])
        return 2
    block = "".join(",\r\n                " + json.dumps(line, ensure_ascii=False)
                    for line in LINES)
    text = text[:-len(tail)] + block + tail
    io.open(P, "w", encoding="utf-8", newline="").write(text)
    state = json.loads(io.open(P, encoding="utf-8").read())
    print("tick=%d loglen=%d bytes=%d"
          % (state["tick"], len(state["log"]), len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())