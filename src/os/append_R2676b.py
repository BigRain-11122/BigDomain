import io, json, os, sys

P = "src/os/state.json"
d = json.load(io.open(P, encoding="utf-8"))
if d.get("tick") != 2666:
    print("REFUSED tick=%r" % (d.get("tick"),))
    sys.exit(2)
before = os.path.getsize(P)
item = ("R2676 push receipt: git push origin main read 327f914f..b753b123 main -> main and git rev-parse read HEAD equal to origin/main at "
        "b753b123 with an EMPTY git status, so the scan repair, the opened verification window and the closeout board/state/heartbeat/export are "
        "delivered; this receipt line lands in the follow-up commit it describes. THE LEG IS STILL LIVE AND THAT IS THE HONEST STATE OF THIS "
        "ROUND: pid 97688 alive by command line, logs/battery-R2676.stream at 197576B carrying 108 closed PASS suite rows and ZERO FAIL suite "
        "rows at closeout, against a full leg that has measured 1600-3300s here, so reconcile-battery-R2675 stays OPEN at its registered 655 "
        "suites / 4906 criteria and the next window adopts it by its evidence path qa/reconcile-all-R2676.log rather than relaunching. NO "
        "successor battery is owed beyond it because this window moved no product src byte and the registry is unmoved at 655/4906 re-measured "
        "by import.")
d["log"].append(item)
out = json.dumps(d, ensure_ascii=False, indent=1).replace("\n", "\r\n")
tmp = P + ".tmp"
with io.open(tmp, "w", encoding="utf-8", newline="") as f:
    f.write(out)
back = json.load(io.open(tmp, encoding="utf-8"))
if len(back["log"]) != len(d["log"]):
    print("REFUSED readback")
    sys.exit(3)
os.replace(tmp, P)
print("APPENDED before=%d after=%d predicted=%d log=%d" % (before, os.path.getsize(P), len(out.encode("utf-8")), len(d["log"])))
