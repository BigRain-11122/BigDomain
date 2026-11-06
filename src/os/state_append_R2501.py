"""R2501 receipt: the push line and the self-heal disclosure, appended in place."""
import io
import json

P = "src/os/state.json"
LINES = [
    "2026-11-07 R2501 push: git push origin main SUCCEEDED this window (3e84d40f..54f7c6d4 main -> main) and git rev-parse read HEAD equal to origin/main at 54f7c6d4, so the closeout commit is delivered and nothing is left staged. The export is re-derived through the shipped driver AFTER this line lands (the R2449/R2433 ordering law) and the driver carries the queue face itself, so the document the CEO reads reports queue=CURRENT with no drift rather than needing a hand-landed block.",
    "2026-11-07 R2501 self-heal check: BigDomain-OSLoop exists and reads Running, but its Principal.LogonType still reads Interactive, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again and is carried as the stale row loop-s4u-reconcile.",
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