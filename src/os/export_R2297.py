"""R2297 closeout: verification window on the debt register first item.

ASCII-only source (the encoding law); the CEO-visible Chinese text lives in
the data file state/export_face_R2297.json and is only read here.

Every number written into state.json / docs/status-export.json is derived
from this round's real artefacts; nothing is invented.
"""

import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
FACE = os.path.join(ROOT, "state", "export_face_R2297.json")

ROUND = "R2297"
TICK = 2297

LOG_OPEN = (
    "2026-11-01 R2297 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored baseline and the token diff was empty, "
    "so no new decision row is presented and zero domain action was owed; "
    "group orders.md latest timestamp 2026-10-31 18:23 EQUAL to the stored "
    "last_order, so no new order; global-benchmarks refreshed 2026-10-29, "
    "inside the 7-day gate; the ledger carries no un-replied @BigDomain row). "
    "Verification window on the register first item: the full reconcile "
    "battery ran on the committed R2296 tree cd78b4a4 with an empty git "
    "status before and after, RUNNER PASS 454/454 suites plus controls 7/7 in "
    "841.2s, birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 "
    "failed=0, criteria total 3700 - exactly the pre-registered +1 suite / "
    "+6 criteria against R2295 (453/3694) from the os-evidence-output-map "
    "suite. The four follow-up sections read PASS after the matrix section "
    "refused to rewrite the stale doc (on-disk 43675B vs regenerated 43762B) "
    "and suite_matrix regenerated docs/sandbox-suite-matrix.md to 454 suites "
    "/ 3700 criteria at 43762B; VERDICT R2297 PASS. Register closed through "
    "its own writer and product-face-R2298 opened first=yes naming the tech "
    "head at state/queue/tech.md line 365 prefix AC-SRS1."
)

LOG_TOKENS = (
    "R2297 tokens: local=~9k api=0 api_reason=verification window on the debt "
    "register first item - one full battery run on the committed tree, one "
    "four-section follow-up with one matrix regeneration inside the same "
    "minute, one register close and one register append through the shipped "
    "writers, and the state/board/export closeout; zero cloud calls and zero "
    "external API touches; the product face carries to R2298"
)

LOG_SELF_HEAL = (
    "R2297 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply it, and "
    "this session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(sixty-second consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

LOG_DISCLOSE = (
    "R2297 honest disclosures: (a) the first battery invocation piped the run "
    "through a truncating selector and was cancelled by the five-minute "
    "no-output rule, leaving no evidence file and no partial artefact; an "
    "orphan check proved zero battery_stream/reconcile_all processes and a "
    "clean tree before the sanctioned `python -u` unpiped rerun that produced "
    "the only evidence log claimed - the R2279 precedent repeating, disclosed "
    "rather than swept; (b) this is a 0-point verification window with no "
    "product face, honestly recorded; (c) the first debt_append was refused "
    "E_DEBTA_BAD_FIELD because the note carried '=' characters and the note "
    "was rewritten without them, never the parser loosened; (d) heartbeat.txt "
    "had no tick 2296 row, so this closeout backfills it from the state log "
    "rather than silently leaving the gauge lagging."
)

HEARTBEAT_2296 = (
    "tick 2296 2026-11-01 product window: the legacy evidence pile gained a "
    "read-only output map - src/os/evidence_output_map.py plus its suite "
    "(AC-EOM1..AC-EOM6 pinned in the R2282 seed row before the code, SUITE "
    "PASS 6/6 double-run identical digest F9ABC32AFC68130B, wired "
    "os-evidence-output-map(6)) reporting per script the qa output paths it "
    "declares, every collision naming both scripts and its declaration line, "
    "and the cited outputs nobody declares, read-only and refusing rather than "
    "guessing; live reading 92 scripts / 164 declared paths / 0 collisions / "
    "16 cited-but-undeclared / 1 NONE; one real gap row seeded "
    "(evidence_output_audit) to hold the tech floor at 10/10 - backfilled here "
    "from the state log because the row was missing"
)

HEARTBEAT_2297 = (
    "tick 2297 2026-11-01 verification window: zero product edits - the full "
    "reconcile battery ran on the committed R2296 tree cd78b4a4 and read "
    "RUNNER PASS 454/454 suites plus controls 7/7 in 841.2s with birth-site "
    "TMP RECLAIM 932/932 worlds 326.57 MiB and criteria total 3700, exactly "
    "the pre-registered +1 suite / +6 criteria from the R2296 "
    "os-evidence-output-map suite; the four follow-up sections read PASS after "
    "the matrix section refused to rewrite the stale doc (43675B vs 43762B) "
    "and suite_matrix regenerated it to 454 suites / 3694-to-3700 criteria at "
    "43762B; the register closed product-face-R2297 (open 2->1, done 46->47) "
    "and opened product-face-R2298 first=yes naming the tech head line 365 "
    "prefix AC-SRS1; the first invocation died to the five-minute no-output "
    "rule behind a truncating pipe and the unpiped rerun produced the only "
    "claimed evidence"
)


def load(path, mode="rb"):
    with open(path, mode) as handle:
        return handle.read()


def write_json(path, data):
    text = json.dumps(data, ensure_ascii=False, indent=2)
    blob = text.encode("utf-8")
    if not blob.endswith(b"\n"):
        blob += b"\n"
    temp = path + ".tmp"
    with open(temp, "wb") as sink:
        sink.write(blob)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, path)
    return len(blob)


def update_state(execute):
    data = json.loads(load(STATE).decode("utf-8"))
    if data["tick"] != TICK - 1:
        print("E_STATE_TICK expected %d, found %s" % (TICK - 1, data["tick"]))
        return 3
    data["tick"] = TICK
    data["log"].extend([LOG_OPEN, LOG_TOKENS, LOG_SELF_HEAL, LOG_DISCLOSE])
    if not execute:
        print("DRY RUN state tick=%d log=%d" % (data["tick"], len(data["log"])))
        return 0
    size = write_json(STATE, data)
    back = json.loads(load(STATE).decode("utf-8"))
    if back["tick"] != TICK or len(back["log"]) != len(data["log"]):
        print("E_STATE_READBACK")
        return 3
    print("STATE tick=%d log=%d %dB readback ok" % (back["tick"],
                                                    len(back["log"]), size))
    return 0


def update_export(execute):
    face = json.loads(load(FACE).decode("utf-8"))
    data = json.loads(load(EXPORT).decode("utf-8"))
    now = datetime.datetime.now().astimezone().replace(microsecond=0)
    data["export_ts"] = now.isoformat()
    data["do"] = face["do"]
    block = data.setdefault("ceo_face", {})
    block["current"] = face["current"]
    block["latest_artifact"] = face["latest"]
    block["next_milestone"] = face["next"]
    block["next_milestone_due"] = (
        now + datetime.timedelta(hours=24)).replace(microsecond=0).isoformat()
    block["last_artifact"] = face["last"]
    data["results"] = [[ROUND, face["result"]]] + data["results"]
    data["outs"] = [[face["out"], "on", face["result"][:0] or
                     "verification only: no product surface changed this window; "
                     "the reading is the artefact"]] + data["outs"]
    import check_export_consistency as consistency
    derived, _, _, pattern = consistency.recompute()
    data["self_drive"] = derived
    label = pattern["tick_row_label"]
    rows = [row for row in data["results"]
            if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(rows) != 1:
        print("E_TICK_ROW expected exactly one tick row, found %d" % len(rows))
        return 3
    rows[0][0] = str(TICK)
    if not execute:
        print("DRY RUN export_ts=%s results=%d outs=%d"
              % (data["export_ts"], len(data["results"]), len(data["outs"])))
        return 0
    size = write_json(EXPORT, data)
    back = json.loads(load(EXPORT).decode("utf-8"))
    if back["export_ts"] != data["export_ts"]:
        print("E_EXPORT_READBACK")
        return 3
    print("EXPORT %dB readback ok results=%d outs=%d"
          % (size, len(back["results"]), len(back["outs"])))
    return 0


def append_heartbeat(execute):
    path = os.path.join(ROOT, "heartbeat.txt")
    raw = load(path)
    text = raw.decode("utf-8")
    have = set()
    for line in text.splitlines():
        if line.startswith("tick "):
            have.add(line.split()[1])
    add = []
    if "2296" not in have:
        add.append(HEARTBEAT_2296)
    if "2297" not in have:
        add.append(HEARTBEAT_2297)
    if not add:
        print("HEARTBEAT already carries ticks 2296 and 2297")
        return 0
    if not text.endswith("\n"):
        text += "\n"
    text += "".join(line + "\n" for line in add)
    if not execute:
        print("DRY RUN heartbeat +%d rows" % len(add))
        return 0
    with open(path, "wb") as sink:
        sink.write(text.encode("utf-8"))
    print("HEARTBEAT +%d rows" % len(add))
    return 0


def main(argv):
    execute = "--execute" in argv
    for step in (update_state, update_export, append_heartbeat):
        code = step(execute)
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))