# closeout_R2252.py - R2252 closeout: state.json tick/log/baseline,
# debt register row closure, status-export refresh.
# Single writer, utf-8, canonical CRLF + 16-space log items via state_io.
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

STATE = os.path.join(HERE, "state.json")
DEBT = os.path.join(ROOT, "state", "debt.md")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

ROUND_LINE = (
    "2026-10-29 R2252 (five-silence scan at open: tree clean with an empty "
    "git status --short and no index.lock; the queue gauge read main 5/5 "
    "tech 10/10 explore 10/10 FLOOR-MET; decisions.md carries 289 non-empty "
    "rows and 189 content-addressed D/C tokens against the stored 190-token "
    "superset baseline, so the diff is four NEW tokens D-20261029-11..14 "
    "plus the five known losses (O-20261012-2330, O-20261026-0735 and the "
    "T-20261026-01..03 truncation artefacts) - all four new rows are "
    "cross-company dispatch reports with no BigDomain execution assignment "
    "(D-11 L1 coder :8090 endpoint dispatched @BigCompute, D-12 AutoYield "
    "resume route dispatched @night shift 19:07, D-13 BigStream three-cycle "
    "gap executed in the BigStream lane, D-14 digest of 31 company reports "
    "whose only BigDomain mention is the standing bootstrap/merchant-number "
    "item already blocked on CEO), so each is acknowledged by number and "
    "none is acted on; the group ledger carries the same @BigDomain patrol "
    "rows already paid off with zero unreplied; the group orders tail is "
    "unchanged at the 2026-10-29 02:1x CEO-PROXY event round R2.48 already "
    "consumed in R2226; benchmarks refreshed 2026-10-29 inside the "
    "seven-day gate) - this window took the debt register first=yes row "
    "(opened R2250, deferred by R2251) instead of opening a new product "
    "face, because R2250 and R2251 both shipped src/os code and wired new "
    "suites that no full battery had covered, and the R2168 mixed-tree rule "
    "forbids product edits inside a battery window. RESULT on the committed "
    "tree: full reconcile battery RUNNER PASS 430/430 suites green plus "
    "reconcile controls 7/7 in 798.1s with birth-site TMP RECLAIM 932/932 "
    "worlds 326.57 MiB busy=0 failed=0 (qa/reconcile-all-R2252.log, 764259B "
    "at RUNNER close, single-writer utf-8 LF through src/os/battery_stream.py, "
    "never a shell redirection), expected criteria total 3558. Four "
    "post-battery sections then all PASS through the new single-writer "
    "helper src/os/battery_followup_R2252.py (same shape as R2249, evidence "
    "path and label changed): matrix regenerated and read back byte-identical "
    "at 430 suites / 3558 criteria (docs/sandbox-suite-matrix.md, 41900B, "
    "green=430/430), fingerprint chain CLEAN over 5 domains, runner profile "
    "--daily --check PASS byte-identical, writer census re-frozen then "
    "DRIFT-CLEAN files=2188 tee=1659 baselined=529 disappeared=0 flags=0, "
    "closing on VERDICT PASS. Measured deltas against R2249 (428 suites / "
    "3546 criteria): +2 suites and +12 criteria are exactly the R2250 "
    "os-export-freshness suite (6) and the R2251 os-debt-append suite (6) "
    "joining the registry, so both recent product slices are now covered by "
    "the whole battery. Honest score: zero product code changed and zero new "
    "face, so this is a 0-point verification window that buys back the debt; "
    "state.json measures 46647B against the 78500B waterline (no fold due) "
    "and its layout is canonical (crlf 43, bare_lf 0, log items 33 at the "
    "16-space indent)."
)

TOKENS_LINE = (
    "R2252 tokens: local=~14k api=0 api_reason=verification window on the "
    "debt register first item - one streamed full battery with the "
    "birth-site tmp reclaim inside its own window, one new four-section "
    "follow-up helper, one register row closed, and the events/backlog/"
    "debt/state/export closeout; zero cloud calls and zero external API "
    "touches; no product code changed (the R2168 mixed-tree rule)"
)

SELFHEAL_LINE = (
    "R2252 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply "
    "it, and this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (twenty-first consecutive disclosure, registered as the "
    "stale row loop-s4u-reconcile in state/debt.md)."
)

PROBE_LINE = (
    "R2252 honest disclosure: a `python src/sandbox/reconcile_all.py --help` "
    "probe started a real battery run (the runner has no --help and begins "
    "executing immediately), and the truncating pipe through a selector "
    "closed its stdout so it died inside the five-minute no-output rule. An "
    "ownership check proved zero surviving reconcile_all processes and no "
    "evidence file was ever written (the runner only writes evidence when "
    "--evidence is given), so nothing was lost or left to clean before the "
    "sanctioned streamed run; the wasted partial pass cost only time."
)

NEW_TOKENS = ["D-20261029-11", "D-20261029-12",
              "D-20261029-13", "D-20261029-14"]

DEBT_DONE_NOTE = (
    "R2250 changed src/os (export_freshness.py, test_export_freshness.py, "
    "evidence_R2250.py) and R2251 added src/os/debt_append.py, "
    "test_debt_append.py and evidence_R2251.py plus one runner and two queue "
    "files; closed at R2252 on the committed tree = RUNNER PASS 430/430 "
    "suites plus controls 7/7 in 798.1s, tmp reclaim 932/932 worlds "
    "326.57 MiB, then matrix 430 suites / 3558 criteria byte-identical, "
    "fingerprint CLEAN, profile PASS, census DRIFT-CLEAN files=2188"
)


def close_state():
    raw = io.open(STATE, encoding="utf-8", newline="").read()
    state = json.loads(raw)
    state["tick"] = int(state["tick"]) + 1
    base = [t for t in state.get("last_dec_tokens", "").split(",") if t]
    for token in NEW_TOKENS:
        if token not in base:
            base.append(token)
    state["last_dec_tokens"] = ",".join(base)
    state["last_decision_rows"] = 289
    for line in (ROUND_LINE, TOKENS_LINE, SELFHEAL_LINE, PROBE_LINE):
        state["log"].append(line)
    text = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    text = state_io.canon(text)
    assert json.loads(text) == state
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return state["tick"], len(text.encode("utf-8"))


def close_debt():
    text = io.open(DEBT, encoding="utf-8", newline="").read()
    lines = text.split("\n")
    keep = []
    removed = 0
    for line in lines:
        if (line.startswith("- [ ]")
                and "opened=R2250" in line
                and "item=reconcile-battery-and-matrix" in line):
            removed += 1
            continue
        keep.append(line)
    if removed != 1:
        raise SystemExit("E_DEBT_ROW count=%d" % removed)
    done = ("- [x] opened=R2250 | item=reconcile-battery-and-matrix"
            " | note=%s | closed=R2252" % DEBT_DONE_NOTE)
    body = "\n".join(keep).rstrip("\n")
    body = body + "\n\n" + done + "\n"
    with io.open(DEBT, "w", encoding="utf-8", newline="") as handle:
        handle.write(body)
    return done[:80]


def close_export():
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    data["export_ts"] = "2026-10-29T13:20:00+08:00"
    data["do"] = (
        "verification window R2252: the debt register first item is closed on "
        "the committed tree - full reconcile battery RUNNER PASS 430/430 "
        "suites plus controls 7/7 in 798.1s (qa/reconcile-all-R2252.log), "
        "then matrix 430 suites / 3558 criteria byte-identical, fingerprint "
        "CLEAN, profile PASS, census DRIFT-CLEAN files=2188; zero product "
        "code changed")
    face = data.setdefault("ceo_face", {})
    face["current"] = (
        "R2252 验证轮：把 R2250/R2251 两批新代码交给全量电池，430 套件全绿"
        "（含两个新套件），验证欠账清零")
    face["latest_artifact"] = (
        "qa/reconcile-all-R2252.log（764259B·单写者 UTF-8 LF·含 RUNNER PASS "
        "430/430 + 四段跟进结果 + VERDICT PASS）+ "
        "docs/sandbox-suite-matrix.md（430 套件 / 3558 判据·41900B）·"
        "2026-10-29 R2252"
    )
    face["last_artifact"] = (
        "qa/reconcile-all-R2252.log + docs/sandbox-suite-matrix.md（R2252·"
        "2026-10-29）"
    )
    face["next_milestone"] = (
        "R2253 回到产品面：认领 tech/explore 队头（两条队列均 10/10 达标），"
        "预注册判据后交付一个新读面，并在同窗补满验证"
    )
    face["next_milestone_due"] = "2026-10-30T13:20:00+08:00"
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return len(text.encode("utf-8"))


if __name__ == "__main__":
    print("state", close_state())
    print("debt", close_debt())
    print("export", close_export())