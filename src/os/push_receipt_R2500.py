"""R2500 push receipt: append the push line to state.json, canon layout."""
import io
import json

P = "src/os/state.json"
LINES = [
    "2026-11-07 R2500 push: git push origin main SUCCEEDED this window (5ac3d85b..8a14be9b main -> main) with the closeout commit 8a14be9b carrying the battery evidence, the regenerated matrix, the debt register, state/export/backlog/heartbeat and the three one-off R2500 scripts, so nothing is left staged. The export was refreshed through the shipped driver BEFORE this commit (the R2449/R2433 ordering law) and check_export_consistency read pass=21 fail=0 at state_tick=2500 with the queue face CURRENT and no drift, export_consistency_queue_face reading AGREE base=21/21 queue=CURRENT, so the document the CEO reads carries this round. This receipt line lands in its own commit and the export is re-derived again after it, so the derived counters cannot be left one line behind.",
    "2026-11-07 R2500 self-heal check: BigDomain-OSLoop exists and reads Ready, but its Principal.LogonType still reads Interactive, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again and is carried as the stale row loop-s4u-reconcile.",
]

raw = io.open(P, "rb").read()
text = raw.decode("utf-8")
tail = '\r\n  ]\r\n}\r\n'
assert text.endswith(tail), repr(text[-40:])
block = "".join(",\r\n                " + json.dumps(line, ensure_ascii=False)
                for line in LINES)
text = text[:-len(tail)] + block + tail
io.open(P, "w", encoding="utf-8", newline="").write(text)

state = json.loads(io.open(P, encoding="utf-8").read())
print("tick=%d loglen=%d bytes=%d"
      % (state["tick"], len(state["log"]), len(text.encode("utf-8"))))