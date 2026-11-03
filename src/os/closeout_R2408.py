# closeout_R2408.py - the R2408 verification window: the carried battery ran
# ONCE on the committed tree and read fully green, two carried battery rows
# were closed through the shipped CLI instead of by hand, and the register
# gained the product face the next window owes.
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import state_io  # noqa: E402
import ledger_line_shape_guard as LLSG  # noqa: E402
import queue_floor_export_face as QFEF  # noqa: E402
import check_export_consistency as CEC  # noqa: E402

STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
HEART = os.path.join(REPO, "heartbeat.txt")
BACKLOG = os.path.join(BASE, "backlog.md")

STAMP = "2026-11-03T08:2x:00+08:00"
DO = ("R2408 verification: the carried battery ran once on the committed tree "
      "and read RUNNER PASS 532/532 suites with criteria 4168 exactly as "
      "pre-registered, so both carried battery rows closed")
ART = ("qa/reconcile-daily-20261103-2.log + state/debt.md + "
       "src/os/closeout_R2408.py")
NEXT = ("claim state/queue/tech.md top claimable row as a PRODUCT face with "
        "its criteria pre-registered before the code (debt row "
        "product-face-R2409 leads)")

LEDGER = (
    "R2408 tokens: local=~30k api=0 api_reason=verification window - the "
    "carried battery ran once on the committed tree and read RUNNER PASS over "
    "532 of 532 suites plus reconcile controls 7 of 7 in 953.2s with criteria "
    "total 4168 exactly as pre-registered and sentinel, profile and census all "
    "green, which discharged both carried battery rows through the shipped "
    "debt_close CLI rather than by hand; one real register defect was measured "
    "and repaired before the second close (an open row carried a closed key "
    "that the parser refuses), the register then read one open row and the "
    "gate was given the product face the next window owes, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches")

LOG = [
    ("2026-11-03 R2408 verification window (five-silence scan at open: empty "
     "git status and no .git/index.lock; LEDGER @BigDomain addressed rows=0 "
     "unreplied=0; DEC baseline 95 tokens carries D-20261103-11 as its newest "
     "member and the live file names nothing beyond it, so new=0; the local "
     "orders table tail is the 2026-09-28 batch already acknowledged and the "
     "group orders tail dispatches other companies; benchmarks refreshed "
     "2026-11-02 inside the seven-day gate). The debt gate had first claim on "
     "reconcile-battery-R2407 because R2407 changed src/os and one registry "
     "line, so the R2168 mixed-tree rule put the battery FIRST with zero "
     "product edits."),
    ("2026-11-03 R2408 battery: RUNNER PASS 532/532 suites plus reconcile "
     "controls 7/7 in 953.2s with expected criteria total 4168 exactly as the "
     "closed row pre-registered, sentinel=ok profile=ok census=ok on the live "
     "tree, verdict PASS exit 0 (qa/reconcile-daily-20261103-2.log, 837645B). "
     "Nothing was changed before the run, so this is a green leg on the "
     "committed R2407 tree and not a repair."),
    ("2026-11-03 R2408 disclosures: (a) a first attempt at the same battery "
     "was launched through a pipeline that buffers, printed nothing and was "
     "cancelled at the five-minute output gate; it left an incomplete "
     "qa/reconcile-daily-20261103.log with no RUNNER or verdict line, which is "
     "ABORTED evidence by the shipped runner_abort_face reading and is NOT "
     "counted as a leg; the green leg is the -2 file from a detached process. "
     "(b) The second close refused with E_DEBC_BAD_REGISTER because the open "
     "R2392 row carried a trailing closed key that the row parser rejects; the "
     "key was removed and the close then read back ok, and the same defect had "
     "kept that row stale for sixteen windows without being seen. (c) The "
     "successor row was appended through the shipped CLI after it refused a "
     "first note carrying an equals sign, which is the tool own field law "
     "working rather than a defect."),
    ("2026-11-03 R2408 self-heal check: BigDomain-OSLoop is still registered "
     "with LogonType=InteractiveToken, which the 2026-09-29 machine law "
     "forbids for every lane task; src/os/register_loop_task.ps1 passes an "
     "explicit S4U principal but needs an elevated shell and this session is "
     "unelevated, so the task definition was left untouched (hundred-and-"
     "sixty-third consecutive disclosure, carried as the stale row "
     "loop-s4u-reconcile in state/debt.md)."),
]

BACKLOG_ROW = (
    "- [x] R2408 verification window: the debt gate named "
    "reconcile-battery-R2407 first=yes, so the battery ran FIRST on the "
    "committed tree and read RUNNER PASS 532/532 suites plus reconcile "
    "controls 7/7 in 953.2s with criteria total 4168 exactly as the closed "
    "row pre-registered, sentinel=ok profile=ok census=ok, verdict PASS "
    "(qa/reconcile-daily-20261103-2.log). Both carried battery rows were then "
    "closed through the shipped debt_close CLI (R2407 and the sixteen-window "
    "stale R2392, whose note conditioned it on one green RUNNER PASS), and "
    "one real register defect surfaced and was repaired first: the R2392 open "
    "row carried a closed key the parser refuses, which is why every close of "
    "it had answered E_DEBC_BAD_REGISTER. The register then read open=1 and "
    "the gate owed a leader, so product-face-R2409 was appended first=yes by "
    "the shipped debt_append CLI (its own field law refused a first note that "
    "carried an equals sign). Zero product code changed, honestly scored: no "
    "product module shipped this window and none is claimed; the next window "
    "owes a PRODUCT face with criteria pre-registered before the code. "
    "Disclosed: an earlier buffered launch of the same battery was cancelled "
    "at the five-minute gate and left an ABORTED evidence file that is not "
    "counted as a leg.\n")


def write_atomic(path, text):
    temp = path + ".tmp-co2408"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(temp, path)


def main():
    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if backlog.startswith("- [x] R2408"):
        sys.stdout.write("NOTE backlog already carries the R2408 row\n")
    else:
        write_atomic(BACKLOG, BACKLOG_ROW + backlog)
        sys.stdout.write("BACKLOG row prepended\n")

    before = io.open(STATE, encoding="utf-8", newline="").read()
    state = json.loads(before)
    if LOG[0] in state.get("log", []):
        sys.stdout.write("NOTE state already carries this window's items\n")
    else:
        state["tick"] = int(state.get("tick", 0)) + 1
        for item in LOG:
            if item in state["log"]:
                sys.stdout.write("E_STATE duplicate item\n")
                return 2
            state["log"].append(item)
    state["last_decision_rows"] = 148
    text = state_io.canon(json.dumps(state, ensure_ascii=False, indent=2)
                          + "\n")
    raw = text.encode("utf-8")
    write_atomic(STATE, text)
    if open(STATE, "rb").read() != raw:
        sys.stdout.write("E_STATE read-back differs\n")
        return 2
    readback = json.load(io.open(STATE, encoding="utf-8"))
    sys.stdout.write("STATE tick=%d log_items=%d tokens=%d bytes=%d -> %d\n"
                     % (readback["tick"], len(readback["log"]),
                        len(readback.get("last_dec_tokens") or []),
                        len(before.encode("utf-8")), len(raw)))

    verdict = LLSG.append_ledger_line(STATE, LEDGER, execute=True)
    sys.stdout.write("LEDGER door verdict=%s predicted=%s wrote=%s\n"
                     % (verdict["verdict"], verdict.get("predicted_bytes"),
                        verdict.get("wrote")))
    if verdict["verdict"] != "ACCEPTED" or verdict.get("wrote") != "yes":
        return 2
    final = json.load(io.open(STATE, encoding="utf-8"))
    sys.stdout.write("STATE after ledger tick=%d log_items=%d bytes=%d\n"
                     % (final["tick"], len(final["log"]),
                        os.path.getsize(STATE)))

    data = json.load(io.open(EXPORT, encoding="utf-8"))
    QFEF.apply(data, REPO)
    derived = CEC.recompute()[0]
    for key, value in derived.items():
        if key in data.get("self_drive", {}):
            data["self_drive"][key] = value
        else:
            sys.stdout.write("NOTE derived key not in export: %s\n" % key)
    data["export_ts"] = STAMP
    data["do"] = DO
    outs = data.get("outs") or []
    if not outs or outs[0] != ART:
        data["outs"] = [ART] + outs
    rows = data.get("results") or []
    if not rows or rows[0][0] != "2408":
        data["results"] = [["2408", DO]] + rows
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ART
    face["last_artifact"] = ART
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = "2026-11-04T23:00:00+08:00"
    face["updated_at"] = STAMP
    write_atomic(EXPORT, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.write("EXPORT refreshed bytes=%d\n" % os.path.getsize(EXPORT))

    heart = io.open(HEART, encoding="utf-8", newline="").read()
    if not heart.endswith("\n"):
        heart += "\n"
    heart += ("%s tick=%d R2408 verification - the battery read fully green on "
              "the committed tree (532/532, 4168 criteria) and two carried "
              "battery rows closed through the shipped CLI\n"
              % (STAMP, final["tick"]))
    write_atomic(HEART, heart)
    sys.stdout.write("HEARTBEAT appended\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())