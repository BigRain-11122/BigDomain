"""Watch a RUNNING battery leg's evidence file and judge whether the
streaming claim holds on a long leg.

Why this exists: AC-BSGB15/AC-BSGB16 (src/os/test_battery_shard.py, R2886)
already prove on a real subprocess that `battery_shard` streams rows and that a
partial file is refused by `--check`. What no criterion covered is the pair
"streaming x a leg longer than five minutes": the tool was graded on a probe
leg that lasts about a second, so "readable mid-run" had never been observed
past the 300s wall it was built to cross. R2889 left that as its MAIN item.

This tool is the observer, not the grade: it samples the evidence file while
the leg runs and prints what it actually saw. It never writes into qa/ unless
asked to, and it never touches the leg's own evidence file.

Exit codes: 0 MID-RUN CONFIRMED, 2 REFUSED (premise not met), 3 unreadable.

Usage (single snapshot):
    python tools/leg_watch.py qa/wide-os-full-R2890.log

Usage (watch across a window, write its own evidence):
    python tools/leg_watch.py qa/wide-os-full-R2890.log --interval 30
        --min-window 300 --evidence leg-watch-R2890.log
"""

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QA_DIR = os.path.join(ROOT, "qa")


class Refuse(Exception):
    pass


def evidence_name(raw):
    """Keep the battery's AC-BSH6 rule: own evidence lives under qa/ only."""
    if not raw:
        raise Refuse("E_EVIDENCE_PATH empty")
    if os.path.isabs(raw) or "/" in raw or "\\" in raw or ".." in raw:
        raise Refuse("E_EVIDENCE_PATH %s" % raw)
    if not raw.endswith(".log"):
        raise Refuse("E_EVIDENCE_PATH %s (needs .log)" % raw)
    return raw


def sample(path):
    """One honest reading. Torn reads are COUNTED, not hidden: the writer
    rewrites the whole file per row, so a reader can legitimately catch it
    mid-rewrite. A torn sample is reported, never silently dropped."""
    info = {"readable": False, "torn": False, "bytes": 0, "rows": 0,
            "running": False, "closing": False, "rc": None, "mtime": 0.0}
    try:
        st = os.stat(path)
        info["bytes"] = st.st_size
        info["mtime"] = st.st_mtime
        with open(path, "rb") as handle:
            raw = handle.read()
    except FileNotFoundError:
        info["torn"] = True
        return info
    except OSError:
        info["torn"] = True
        return info
    text = raw.decode("utf-8", "replace")
    lines = text.splitlines()
    info["readable"] = True
    info["rows"] = len([l for l in lines if l.startswith("SHARD row ")])
    info["running"] = "state=RUNNING" in text
    for line in lines:
        if line.startswith("SHARD rc="):
            info["closing"] = True
            for tok in line.split():
                if tok.startswith("rc="):
                    try:
                        info["rc"] = int(tok[3:])
                    except ValueError:
                        pass
    # A torn read is a readable file whose LAST line looks cut: the writer
    # rewrites header+rows+closing as one blob, so a truncated tail is the
    # signature. Counted so the verdict can state how often it happened.
    if raw and not raw.endswith(b"\n"):
        info["torn"] = True
    info["tail_ok"] = raw.endswith(b"\n") if raw else False
    return info


def judge(samples, min_window):
    """Judge only what the samples prove. Mid-run readability needs a sample
    that carries at least one row and NO closing row - a finished file read at
    the end proves the output, not the streaming."""
    readable = [s for s in samples if s["info"]["readable"]]
    midrun = [s for s in samples
              if s["info"]["readable"] and s["info"]["rows"] > 0
              and not s["info"]["closing"]]
    rows_seq = [s["info"]["rows"] for s in readable]
    monotone = all(b >= a for a, b in zip(rows_seq, rows_seq[1:]))
    span = (samples[-1]["t"] - samples[0]["t"]) if len(samples) > 1 else 0.0
    torn = len([s for s in samples if s["info"]["torn"]])
    reasons = []
    if not readable:
        reasons.append("E_NO_READABLE_SAMPLE")
    if not midrun:
        reasons.append("E_NO_MIDRUN_SAMPLE")
    if not monotone:
        reasons.append("E_ROWS_WENT_BACKWARDS")
    if min_window and span < min_window - 0.5:
        reasons.append("E_WINDOW_SHORT span=%.1f<%ds" % (span, min_window))
    return {"ok": not reasons, "reasons": reasons, "readable": len(readable),
            "midrun": len(midrun), "torn": torn, "span": span,
            "monotone": monotone, "rows_first": rows_seq[0] if rows_seq else 0,
            "rows_last": rows_seq[-1] if rows_seq else 0}


def main(argv):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("leg", help="evidence file under qa/ (basename)")
    ap.add_argument("--interval", type=float, default=0.0,
                    help="seconds between samples; 0 = one snapshot")
    ap.add_argument("--min-window", type=int, default=0,
                    help="required readable span in seconds")
    ap.add_argument("--max-samples", type=int, default=40)
    ap.add_argument("--evidence", default="",
                    help="write this report under qa/")
    args = ap.parse_args(argv)

    leg = os.path.join(QA_DIR, os.path.basename(args.leg))
    if not os.path.exists(leg):
        print("E_LEG_MISSING %s" % args.leg)
        return 3

    samples = []
    started = time.time()
    while True:
        samples.append({"t": time.time() - started, "info": sample(leg)})
        last = samples[-1]["info"]
        if args.interval <= 0:
            break
        if last["closing"]:
            break
        if len(samples) >= args.max_samples:
            break
        if (args.min_window and samples[-1]["t"] >= args.min_window
                and len(samples) >= 2):
            break
        time.sleep(args.interval)

    verdict = judge(samples, args.min_window)
    lines = []
    lines.append("LEG-WATCH leg=%s samples=%d span=%.1fs interval=%.1fs "
                 "min_window=%ds" % (args.leg, len(samples), verdict["span"],
                                     args.interval, args.min_window))
    for s in samples:
        i = s["info"]
        lines.append("LEG-WATCH sample t=%.1f bytes=%d rows=%d running=%s "
                     "closing=%s torn=%s readable=%s"
                     % (s["t"], i["bytes"], i["rows"], i["running"],
                        i["closing"], i["torn"], i["readable"]))
    lines.append("LEG-WATCH verdict %s readable=%d midrun=%d torn=%d "
                 "monotone=%s rows=%d..%d reasons=%s"
                 % ("MID-RUN CONFIRMED" if verdict["ok"] else "REFUSED",
                    verdict["readable"], verdict["midrun"], verdict["torn"],
                    verdict["monotone"], verdict["rows_first"],
                    verdict["rows_last"],
                    ",".join(verdict["reasons"]) or "-"))
    text = "\n".join(lines) + "\n"
    print(text, end="")

    if args.evidence:
        name = evidence_name(args.evidence)
        path = os.path.join(QA_DIR, name)
        tmp = path + ".partial"
        with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        print("DECL evidence name=%s bytes=%d lines=%d"
              % (name, len(text.encode("utf-8")), len(lines)))
    return 0 if verdict["ok"] else 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    sys.exit(main(sys.argv[1:]))
