"""R2492 push record: append the delivered-commit line, keep canon layout."""
import io
import json

P = "src/os/state.json"
LINE = ("2026-11-06 R2492 push: git push origin main SUCCEEDED this window "
        "(f358685d..2ca894bc main -> main) and git rev-parse read HEAD at "
        "2ca894bc, so the whole R2492 delivery - the face, its suite, the two "
        "evidence logs, the registry row, the stamp-aligned matrix, the debt "
        "register and the state/export/backlog/heartbeat closeout - is in one "
        "commit and nothing is left staged. The export was re-derived through the "
        "shipped driver AFTER the state append (the R2449/R2433 ordering law), so "
        "the published document carries this round rather than predating it; "
        "check_export_consistency read pass=21 fail=0 at state_tick=2492 with the "
        "queue face CURRENT at claimable 6/10/10.")

raw = io.open(P, "rb").read()
text = raw.decode("utf-8")
tail = "\r\n  ]\r\n}\r\n"
assert text.endswith(tail), repr(text[-40:])
text = text[:-len(tail)] + (",\r\n                "
                            + json.dumps(LINE, ensure_ascii=False)
                            + tail)
io.open(P, "w", encoding="utf-8", newline="").write(text)
state = json.loads(io.open(P, encoding="utf-8").read())
print("tick=%d loglen=%d bytes=%d"
      % (state["tick"], len(state["log"]), len(text.encode("utf-8"))))