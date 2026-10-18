# closeout_R2031.py - R2031 closeout driver (D-20261019-04
# execution round): fold R561 first (pre-closeout ruling),
# then byte-surgical state append (tick 2031, round/tokens
# pair, DEC baseline fields), heartbeat line, export refresh.
# Pure ASCII source; CJK lives in closeout_payload_R2031.json
# (data-file law). Fold window = tail 3 (fold R560 rolling +
# R2030 round + R2030 tokens), per the R2030 precedent.
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import logs_toolkit as LT  # noqa: E402 (PAT single source)

STATE = os.path.join(ROOT, "src", "os", "state.json")
P_PAYLOAD = os.path.join(HERE, "closeout_payload_R2031.json")
P_HEART = os.path.join(ROOT, "heartbeat.txt")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
TPL = os.path.join(HERE, "fold_summary_R2031.json")
SUMMARY = os.path.join(os.environ["TEMP"], "fold-summary-R2031.txt")

TAIL = 3
ROUND = "R2031"
FOLD_NO = "561"
DESC = ("fold R560 rolling line + R2030 round+tokens (the"
        " 2026-10-18 datasub coverage month-roll takeover"
        " closeout round; fold R560 carries the"
        " R2017..R2030 spectrum)")
HEAD_ASSERTS = ("fold R560", "2026-10-18 R2030", "R2030 tokens:")

pay = json.loads(io.open(P_PAYLOAD, encoding="utf-8").read())


def do_fold():
    st = json.loads(io.open(STATE, encoding="utf-8").read())
    window = st["log"][-TAIL:]
    assert len(window) == TAIL, "log shorter than window"
    for line, head in zip(window, HEAD_ASSERTS):
        assert head in line, "window head mismatch: %s" % head
    sizes = [len(x.encode("utf-8")) for x in window]
    for line, sz in zip(window, sizes):
        assert sz > 100, "window line suspiciously small %d" % sz
    toks = set()
    for line in window:
        toks |= set(LT.PAT.findall(line))
    win_bytes = sum(sizes)
    tpl = json.loads(io.open(TPL, encoding="utf-8").read())["template"]
    summary = (tpl
               .replace("%%WINBYTES%%", str(win_bytes))
               .replace("%%TOKCOUNT%%", str(len(toks)))
               .replace("%%TOKENS%%", "|".join(sorted(toks))))
    assert "\n" not in summary, "summary must be one line"
    with io.open(SUMMARY, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(summary + "\n")
    base = [sys.executable, os.path.join(HERE, "logs_toolkit.py"),
            "fold", "--round", ROUND, "--fold-no", FOLD_NO,
            "--desc", DESC, "--window-tail", str(TAIL),
            "--summary-file", SUMMARY, "--allow-create"]
    p1 = subprocess.run(base + [], capture_output=True)
    plan = json.loads(p1.stdout.decode("utf-8", "replace"))
    assert plan.get("mode") == "dry-run", "dry-run plan not found"
    assert plan["token_ok"], "token_missing=%s" % plan["token_missing"]
    assert plan["gate_ok"], ("gate exceeded: predicted=%d reserve=%d"
                             % (plan["predicted_bytes"],
                                plan["reserve_bytes"]))
    assert plan["window_lines"] == TAIL
    print("DRY-RUN-OK predicted=%d window_bytes=%d tokens=%d"
          % (plan["predicted_bytes"], plan["window_content_bytes"],
             len(toks)))
    p2 = subprocess.run(base + ["--execute"], capture_output=True)
    out2 = p2.stdout.decode("utf-8", "replace")
    done_line = [ln for ln in out2.splitlines()
                 if ln.startswith("FOLD ")]
    print((done_line[-1] if done_line else "no-done-line")
          .encode("ascii", "replace").decode("ascii"))
    assert p2.returncode == 0, ("fold execute failed rc=%d out=%s"
                               % (p2.returncode, out2[-400:]))
    sz = os.path.getsize(STATE)
    st2 = json.loads(io.open(STATE, encoding="utf-8").read())
    print("POST-FOLD state bytes=%d log-items=%d" % (sz, len(st2["log"])))
    assert sz < 78500, "post-fold over the line"


def do_append():
    with io.open(STATE, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    gauge = len(text.encode("utf-8"))
    lines = text.split("\n")

    def is_log_item(l):
        s = l.strip()
        return s.startswith('"') and (s.endswith('",')
                                     or s.rstrip("\r").endswith('",')
                                     or s.rstrip("\r").endswith('"'))

    idx = [i for i, l in enumerate(lines) if is_log_item(l)]
    if not idx:
        sys.exit("FATAL: no log item lines found")
    i_last = idx[-1]
    last_line = lines[i_last]
    if pay["last_item_head"] not in last_line:
        sys.exit("FATAL: last item head mismatch: %r"
                 % last_line[:80])
    indent = last_line[:len(last_line) - len(last_line.lstrip())]

    round_line = pay["round_line"]
    tokens_line = pay["tokens_line"]
    for s in (round_line, tokens_line):
        if '"' in s or "\\" in s:
            sys.exit("FATAL: illegal char in new line")

    stripped = last_line.rstrip("\r")
    assert stripped.endswith('"'), "last item must end with a quote"
    lines[i_last] = stripped + ",\r"
    new_items = [indent + '"' + round_line + '",\r',
                 indent + '"' + tokens_line + '"\r']
    lines[i_last + 1:i_last + 1] = new_items
    text = "\n".join(lines)

    new, n = re.subn(r'"tick": 2030', '"tick": 2031', text, count=1)
    if n != 1:
        sys.exit("FATAL: field edit failed: tick")
    text = new

    new, n = re.subn(r'"last_decision_rows": 365',
                     '"last_decision_rows": 372', text, count=1)
    if n != 1:
        sys.exit("FATAL: field edit failed: last_decision_rows")
    text = new

    old_tail = ',D-20261018-01,C-20261018-06,D-20261018-02"'
    new_tail = (',D-20261018-01,C-20261018-06,D-20261018-02'
                ',D-20261019-01,D-20261019-02,D-20261019-03'
                ',D-20261019-04"')
    if text.count(old_tail) != 1:
        sys.exit("FATAL: last_dec_tokens tail anchor count=%d"
                 % text.count(old_tail))
    text = text.replace(old_tail, new_tail, 1)

    json.loads(text)  # raises on bad json
    with io.open(STATE, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    final_bytes = len(text.encode("utf-8"))
    st = json.loads(text)
    print("APPEND-OK gauge=%dB final=%dB tick=%d log-items=%d"
          % (gauge, final_bytes, st["tick"], len(st["log"])))
    assert final_bytes < 78500, "over the line"
    assert st["log"][-1].startswith("R2031 tokens:"), "tail check"
    assert st["last_decision_rows"] == 372, "dec rows check"
    assert st["last_dec_tokens"].endswith(
        "D-20261019-04"), "tok check"
    assert st["last_order"] == "2026-10-18 23:46", "ord check"
    print("STATE-APPEND-OK")


def do_closeout():
    now = datetime.now(timezone(timedelta(hours=8)))
    stamp = now.strftime("%Y-%m-%d %H:%M") + " +08:00"
    hb_line = (stamp + " | BigDomain OSLoop alive | tick 2031 | "
               + pay["heartbeat_line"] + "\n")
    with io.open(P_HEART, "a", encoding="utf-8", newline="") as fh:
        fh.write(hb_line)
    print("heartbeat ok tick=2031")

    import check_export_consistency as CEC
    derived, _state, exp, _pat = CEC.recompute()
    exp["export_ts"] = now.isoformat(timespec="seconds")
    exp["ceo_face"]["current"] = pay["ceo_current"]
    exp["ceo_face"]["latest_artifact"] = pay["ceo_artifact"]
    exp["ceo_face"]["next_milestone"] = pay["ceo_milestone"]
    exp["results"].insert(0, [pay["results_row_tick"],
                              pay["results_row_label"]])
    with io.open(os.path.join(HERE,
                 "export_consistency_patterns.json"), "r",
                 encoding="utf-8-sig") as f:
        tick_label = json.load(f)["tick_row_label"]
    hit = 0
    for row in exp["results"]:
        if len(row) >= 2 and row[1] == tick_label:
            row[0] = "2031"
            hit += 1
    if hit != 1:
        raise SystemExit("FATAL: tick row count=%d" % hit)
    derived["method"] = ("machine-derived from state.json log"
                        " per BD-PROP-001 caliber"
                        " (check_export_consistency.recompute)")
    exp["self_drive"] = derived
    with io.open(P_EXPORT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(exp, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("export ok ts=%s window=%s W=%d sub=%d explore=%d"
          % (exp["export_ts"], derived["window"],
             derived["log_lines_in_window"],
             derived["substantive_non_idle_mention_lines"],
             derived.get("queue_explore_open", -1)))
    report, n_pass, n_fail = CEC.check()
    print("\n".join(report[-4:]))
    print("CHECK n_pass=%d n_fail=%d" % (n_pass, n_fail))
    if n_fail:
        raise SystemExit(2)
    print("EXPORT-FLUSH-OK tick=2031")
    return 0


def main():
    do_fold()
    do_append()
    do_closeout()
    return 0


if __name__ == "__main__":
    sys.exit(main())
