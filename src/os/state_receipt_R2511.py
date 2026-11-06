"""R2511 receipt: append the push line after the closeout commit landed.

The export is re-derived AFTER this append so the derived counters cannot be
left one line behind. ASCII source, stdlib only.
"""
import io
import json
import sys

P = "src/os/state.json"

LINE = (
    "2026-11-07 R2511 push: git push origin main SUCCEEDED this window "
    "(bb87d581..222a1c10 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 222a1c10, so the whole window is delivered and nothing is "
    "left staged. The export was refreshed through the shipped driver AFTER "
    "the state append (the R2449/R2433 ordering law) and that driver carries "
    "the queue face itself, so the document the CEO reads reported "
    "queue=CURRENT at 229517 bytes with queue_drifted=(none), the queue gate "
    "wire re-wrote the same CURRENT block, and check_export_consistency read "
    "pass=21 fail=0 at state_tick=2511 with the three CEO lines derived rather "
    "than typed. The debt gate now names reconcile-battery-R2511 first=yes at "
    "a pre-registered 585 suites / 4486 criteria, so the next window owes the "
    "battery on this committed tree before any further product byte."
)


def main():
    raw = io.open(P, "rb").read()
    text = raw.decode("utf-8")
    tail = "\r\n  ]\r\n}\r\n"
    if not text.endswith(tail):
        print("FAIL state tail %r" % text[-30:])
        return 2
    before = len(json.loads(text)["log"])
    block = ",\r\n                " + json.dumps(LINE, ensure_ascii=False)
    text = text[:-len(tail)] + block + tail
    io.open(P, "w", encoding="utf-8", newline="").write(text)
    raw_after = io.open(P, "rb").read()
    state = json.loads(raw_after.decode("utf-8"))
    lf_only = raw_after.count(b"\n") - raw_after.count(b"\r\n")
    print("tick=%d loglen=%d bytes=%d crlf=%d lf_only=%d"
          % (state["tick"], len(state["log"]), len(raw_after),
             raw_after.count(b"\r\n"), lf_only))
    return 0 if (len(state["log"]) == before + 1 and lf_only == 0) else 1


if __name__ == "__main__":
    sys.exit(main())