"""R2504 push receipt: one log line appended after the delivery commit.

Same in-place law as the closeout appender: CRLF document, sixteen-space log
array, one anchored insertion before the closing bracket.
"""
import io
import json
import sys

P = "src/os/state.json"
LINE = (
    "2026-11-07 R2504 push: git push origin main SUCCEEDED this window "
    "(73aa3766..62f68212 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 62f68212, so the closeout commit is delivered and nothing "
    "is left staged. The export was refreshed through the shipped driver BEFORE "
    "that commit (the R2449/R2433 ordering law) and check_export_consistency "
    "read pass=21 fail=0 at state_tick=2504 with the queue face CURRENT and no "
    "drift, export_consistency_queue_face reading AGREE base=21/21 "
    "queue=CURRENT, so the document the CEO reads carries this round. This "
    "receipt line lands in its own commit and the export is re-derived once "
    "more after it, so the derived counters cannot be left one line behind."
)


def main():
    raw = io.open(P, "rb").read()
    text = raw.decode("utf-8")
    tail = "\r\n  ]\r\n}\r\n"
    if not text.endswith(tail):
        print("FAIL tail")
        return 2
    before = len(json.loads(text)["log"])
    text = (text[:-len(tail)] + ",\r\n                "
            + json.dumps(LINE, ensure_ascii=False) + tail)
    io.open(P, "w", encoding="utf-8", newline="").write(text)
    state = json.loads(io.open(P, encoding="utf-8").read())
    print("loglen=%d bytes=%d" % (len(state["log"]),
                                  len(text.encode("utf-8"))))
    return 0 if len(state["log"]) == before + 1 else 1


if __name__ == "__main__":
    sys.exit(main())