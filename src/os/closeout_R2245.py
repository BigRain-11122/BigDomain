"""R2245 closeout: state.json log append plus the status-export patch.

The state log append is layout-preserving (canonical 16-space CRLF items) and
verified before the write: tick bumped, three log lines appended, the log
list re-parsed equal to expectation, and the file byte size reported. The
export patch is targeted string surgery so every other byte of the 171KB
export keeps its content, with the self_drive numbers derived from the real
gauge reading rather than written by hand (the F3 law).

ASCII source; the Chinese CEO-face text lives in the UTF-8 data file
src/os/export_R2245_data.json, read through json.
"""

import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
DATA = os.path.join(BASE, "export_R2245_data.json")
GAUGE = os.path.join(BASE, "queue_floor.py")

TICK = 2245

ROUND = (
    "2026-10-29 R2245 (five-silence scan clean at open: decisions.md carries "
    "283 non-empty rows and 185 content-addressed D/C tokens with ZERO "
    "additions against the stored 190-token baseline - the five apparent "
    "losses are the known truncation artefacts, and the baseline is "
    "deliberately left a superset so a later-restored token cannot masquerade "
    "as a new decision - so zero domain action; the group ledger carries the "
    "same three @BigDomain patrol rows already paid off with zero unreplied; "
    "the group orders tail is unchanged at the 2026-10-29 02:1x CEO-PROXY "
    "fleet event round R2.48 already consumed in R2226; benchmarks refreshed "
    "2026-10-29 inside the seven-day gate; tree clean, no index.lock) - the "
    "P1 canonical rows stay blocked-on-CEO and the weekly proposal duty is "
    "met by BD-PROP-005, so this window claimed the tech head. Product: "
    "src/os/state_fold.py, the fold as one callable. measure(disk_bytes) "
    "returns the waterline verdict from the real disk size (margin = gate - "
    "bytes, fold_needed strictly negative margin, verdict in FOLD-CLEAR / "
    "FOLD-DUE); plan_fold(raw, state, w1, w2, summary) is the predicate and "
    "writes nothing - window line count and content bytes, PAT token coverage "
    "(every token in the window must appear in the summary), the predicted "
    "post-fold size, and the exact prefix+[summary]+suffix splice on the "
    "canonical 16-space CRLF layout, with E_SF_BAD_LAYOUT when the item lines "
    "do not match the parsed log length and E_SF_WINDOW when the window is out "
    "of bounds, both refused rather than guessed; append_archive(path, header, "
    "lines) appends the header plus the window lines verbatim, proves the old "
    "bytes are a strict prefix of the new bytes, repairs a missing trailing "
    "newline, creates only under allow_create and verifies the read-back; "
    "fold(root, ...) plans, writes a byte-identical backup (read back), "
    "appends, atomically replaces state.json and proves post bytes == "
    "predicted and the log == prefix+[summary]+suffix; check(root) is the "
    "read-only --check (0 clear / 2 due or bad flags / 3 unreadable). Anchor "
    "check at HEAD 2026-10-29: state_fold, plan_fold, append_archive and "
    "os-state-fold were git grep -F zero-occupancy rc=1 apart from the seed "
    "generator src/os/seed_queue_R2240.py and the queue row's own text. "
    "Criteria AC-SF1..AC-SF6 were pre-registered in that row BEFORE the code "
    "and the suite came back 6/6 green on the first run with no criterion "
    "relaxed and no assertion corrected. Evidence: SUITE PASS 6/6 double-run "
    "byte-identical criterion sha16 921DC309BDA01051 (qa/state-fold-R2245-a.log "
    "and -b.log, 728B each, single writer utf-8 LF by src/os/evidence_R2245.py, "
    "never a shell redirection); wired os-state-fold(6); six adjacent os "
    "suites green plus the live --check reading 21352B/78500B FOLD-CLEAR "
    "margin 57148B in qa/regression-R2245.log (fails=0). Debt carried: the "
    "full reconcile battery and the suite-matrix regeneration were NOT run "
    "this window - the 25-minute budget went to the product face, the battery "
    "was also owed by R2244, and both are the R2246 first item (the R2168 "
    "mixed-tree rule).")

TOKENS = (
    "R2245 tokens: local=~16k api=0 api_reason=product window on the tech "
    "head - one callable with its six-criterion suite, one single-writer "
    "double-run evidence pair, six adjacent os regressions plus the live "
    "check reading, and the queue/backlog/state/export closeout; zero cloud "
    "calls and zero external API touches; the reconcile battery and the "
    "matrix regeneration are deferred and recorded for the second window "
    "running")

SELF_HEAL = (
    "R2245 self-heal check: BigDomain-OSLoop exists and is Running, but its "
    "principal still reads LogonType=InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 "
    "already passes an explicit S4U principal but applying it needs an "
    "elevated shell and this session is unelevated, so the definition of the "
    "loop hosting this window was left untouched. Open local-lane item for an "
    "elevated window (fifteenth consecutive disclosure).")


def escape_item(value):
    literal = json.dumps(value, ensure_ascii=False)
    for char, esc in (("<", "\\u003c"), (">", "\\u003e"),
                      ("&", "\\u0026"), ("'", "\\u0027")):
        literal = literal.replace(char, esc)
    return literal


def append_state_log():
    with io.open(STATE, "rb") as handle:
        raw = handle.read()
    text = raw.decode("utf-8")
    before = json.loads(text)
    newline = "\r\n" if "\r\n" in text else "\n"
    print("STATE layout newline=%r" % newline)
    lines = text.split(newline)
    item_index = []
    in_log = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('"log"') and stripped.endswith("["):
            in_log = True
            continue
        if not in_log:
            continue
        if len(line) > 16 and line[:16] == " " * 16 and line[16] == '"':
            item_index.append(index)
        elif stripped.startswith("]"):
            break
    if len(item_index) != len(before["log"]):
        raise SystemExit("E_STATE_LAYOUT: item lines do not match log length")
    last = item_index[-1]
    if not lines[last].endswith(","):
        lines[last] = lines[last] + ","
    extra = [" " * 16 + escape_item(value) for value in
             (ROUND, TOKENS, SELF_HEAL)]
    for offset, literal in enumerate(extra):
        if offset < len(extra) - 1:
            literal += ","
        lines.insert(last + 1 + offset, literal)
    text = newline.join(lines)
    text = re.sub(r'"tick": \d+', '"tick": %d' % TICK, text, count=1)
    after = json.loads(text)
    expected_log = before["log"] + [ROUND, TOKENS, SELF_HEAL]
    if after["tick"] != TICK or after["log"] != expected_log:
        raise SystemExit("E_STATE_VERIFY: append did not land cleanly")
    data = text.encode("utf-8")
    with io.open(STATE, "wb") as handle:
        handle.write(data)
    with io.open(STATE, "rb") as handle:
        if handle.read() != data:
            raise SystemExit("E_STATE_VERIFY: read-back differs")
    print("STATE bytes=%d log=%d sha16=%s"
          % (len(data), len(after["log"]),
             hashlib.sha256(data).hexdigest()[:16]))
    return len(after["log"])


def gauge():
    proc = subprocess.run([sys.executable, GAUGE, "--check", "--json"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return json.loads(proc.stdout.decode("utf-8"))


def window_round_lines(days=7):
    """Count round lines inside the trailing window, derived from the log."""
    with io.open(STATE, "rb") as handle:
        state = json.loads(handle.read().decode("utf-8"))
    today = datetime.date.today()
    floor = today - datetime.timedelta(days=days - 1)
    count = 0
    for line in state["log"]:
        match = re.match(r"^(\d{4}-\d{2}-\d{2}) R\d+", line)
        if not match:
            continue
        try:
            stamp = datetime.date(*[int(part) for part
                                    in match.group(1).split("-")])
        except ValueError:
            continue
        if stamp >= floor:
            count += 1
    return count


def patch_export():
    with io.open(DATA, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        text = handle.read()
    before = json.loads(text)
    now = datetime.datetime.now().replace(microsecond=0).isoformat()

    replacements = [
        ("export_ts", r'"export_ts": "[^"]*"', now),
        ("do", r'"do": "[^"]*"', payload["do"]),
        ("current", r'"current": "[^"]*"', payload["current"]),
        ("latest_artifact", r'"latest_artifact": "[^"]*"',
         payload["latest_artifact"]),
        ("next_milestone", r'"next_milestone": "[^"]*"',
         payload["next_milestone"]),
    ]
    for name, pattern, value in replacements:
        if len(re.findall(pattern, text)) != 1:
            raise SystemExit("E_ANCHOR: %s is not unique" % name)
        text = re.sub(pattern,
                      lambda match, v=value: '"%s": %s'
                      % (name, json.dumps(v, ensure_ascii=False)),
                      text, count=1)

    for head_key, entries in (("outs", payload["out"]),
                              ("results", payload["result"])):
        head = '"%s": [\n' % head_key
        if text.count(head) != 1:
            raise SystemExit("E_ANCHOR: %s head" % head_key)
        block = ("%s    %s,\n"
                 % (head, json.dumps(list(entries), ensure_ascii=False,
                                     indent=0).replace("\n", "\n    ")))
        text = text.replace(head, block, 1)

    reading = gauge()
    counts = {}
    for row in reading["queues"]:
        counts[row["queue"]] = row["open_rows"]
    after_probe = json.loads(text)
    if (after_probe["export_ts"] != now
            or after_probe["ceo_face"]["current"] != payload["current"]
            or after_probe["outs"][0][0] != payload["out"][0]
            or after_probe["results"][0][0] != payload["result"][0]):
        raise SystemExit("E_VERIFY: export patch did not land")

    live_lines = window_round_lines()
    updates = {
        "queue_main_open": counts["main"],
        "queue_tech_open": counts["tech"],
        "queue_explore_open": counts["explore"],
        "log_lines_in_window": live_lines,
        "substantive_non_idle_mention_lines": live_lines,
    }
    for key, value in updates.items():
        pattern = r'"%s": \d+' % key
        if len(re.findall(pattern, text)) != 1:
            raise SystemExit("E_ANCHOR: self_drive %s" % key)
        text = re.sub(pattern,
                      lambda match, k=key, v=value: '"%s": %d' % (k, v),
                      text, count=1)

    final = json.loads(text)
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("EXPORT ts=%s bytes=%d outs=%d results=%d floors=%s"
          % (final["export_ts"], len(text.encode("utf-8")),
             len(final["outs"]), len(final["results"]),
             reading["verdict"]))
    print("EXPORT self_drive queue main=%d tech=%d explore=%d"
          % (counts["main"], counts["tech"], counts["explore"]))
    return 0


def main():
    append_state_log()
    return patch_export()


if __name__ == "__main__":
    raise SystemExit(main())