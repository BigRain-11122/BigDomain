# closeout_R2258.py - R2258 closeout: state log + debt register rows +
# status-export face + backlog row. Pure stdlib, ASCII source, single
# utf-8 LF writer for the export (json.dumps), state via state_io.
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

ROUND = "R2258"
TICK = 2258

ROUND_LINE = (
    "2026-10-29 R2258 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; the queue gauge read main "
    "5/5 tech 10/10 explore 10/10 FLOOR-MET with tech 11 open of which 1 "
    "gated and explore 10 open; decisions.md carries 289 non-empty rows and "
    "194 content-addressed D/C/O/T/XL tokens against the stored 194-token "
    "superset baseline with ZERO additions - the baseline already covers the "
    "known rotation and truncation artefacts - so zero domain action; the "
    "group ledger carries the same three @BigDomain patrol rows already paid "
    "off, none numbered, so zero unreplied handoffs; the group orders tail is "
    "unchanged at the 2026-10-29 02:1x CEO-PROXY event round R2.48 already "
    "consumed in R2226; benchmarks refreshed 2026-10-29 inside the seven-day "
    "gate) - the P1 canonical rows stay blocked-on-CEO, the weekly proposal "
    "duty is met by BD-PROP-005, and the debt register named exactly one "
    "first=yes row (reconcile-battery-R2258, opened by R2257), so this "
    "window took the verification debt instead of opening a new product "
    "face: R2257 shipped src/os code (state_seq.py, test_state_seq.py, "
    "evidence_R2257.py) and wired a new suite that no full battery had "
    "covered, and the R2168 mixed-tree rule forbids product edits inside a "
    "battery window. RESULT on the committed tree: full reconcile battery "
    "RUNNER PASS 433/433 suites green plus reconcile controls 7/7 in 989.7s "
    "with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2258.log, 765852B at RUNNER close, single-writer "
    "utf-8 LF through src/os/battery_stream.py, never a shell redirection), "
    "expected criteria total=3576. Four post-battery sections then all PASS "
    "through the new single-writer helper src/os/battery_followup_R2258.py "
    "(same shape as R2256, only the evidence path and the round label "
    "changed): matrix regenerated to 433 suites / 3576 criteria and read "
    "back byte-identical (docs/sandbox-suite-matrix.md, 42111B, "
    "green=433/433), fingerprint chain CLEAN over 5 domains, runner profile "
    "--daily --check PASS, writer census re-frozen then DRIFT-CLEAN "
    "files=2200 tee=1671 baselined=529 disappeared=0 flags=0, closing on "
    "VERDICT PASS. The +1 suite / +6 criteria against R2256 (432/3570) is "
    "exactly the R2257 os-state-seq suite joining the registry, so the "
    "newest slice is now covered by the whole battery and not only by its "
    "own suite plus neighbours. Honest score: zero product code changed and "
    "zero new apimarket face, so this is a 0-point verification window that "
    "only buys back the debt.")

TOKENS_LINE = (
    "R2258 tokens: local=~10k api=0 api_reason=verification window on the "
    "debt register first item - one retried streamed full battery (the first "
    "attempt was piped through a truncating selector and died in the "
    "five-minute no-output rule with zero orphans and no evidence loss), one "
    "new four-section follow-up helper, one register row closed with its "
    "successor opened, and the backlog/state/export closeout; zero cloud "
    "calls and zero external API touches; no product code changed (the R2168 "
    "mixed-tree rule)")

SELFHEAL_LINE = (
    "R2258 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply "
    "it, and this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (twenty-sixth consecutive disclosure, registered as the "
    "stale row loop-s4u-reconcile in state/debt.md).")


def close_state():
    path = os.path.join(ROOT, "src", "os", "state.json")
    raw = state_io.read_raw(path)
    text = state_io.decode(raw)
    data = state_io.parse(text)
    data["tick"] = TICK
    data["log"] = list(data["log"]) + [ROUND_LINE, TOKENS_LINE,
                                       SELFHEAL_LINE]
    body = json.dumps(data, ensure_ascii=False, indent=2)
    new_text = state_io.canon(body)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="") as h:
        h.write(new_text)
    os.replace(tmp, path)
    reread = state_io.parse(state_io.decode(state_io.read_raw(path)))
    if reread["tick"] != TICK or len(reread["log"]) != len(data["log"]):
        raise SystemExit("E_CLOSE_STATE: read-back mismatch")
    print("state ok=1 bytes=%d log_items=%d"
          % (os.path.getsize(path), len(data["log"])))
    print("layout:", state_io.report(path))


def close_debt():
    path = os.path.join(ROOT, "state", "debt.md")
    with io.open(path, encoding="utf-8", newline="") as h:
        text = h.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    old_row = (
        "- [ ] opened=R2257 | item=reconcile-battery-R2258 | note=R2257 "
        "changed src/os (state_seq.py, test_state_seq.py, evidence_R2257.py), "
        "one runner entry and three queue/board files; run it on the committed "
        "tree with zero product code changed (the R2168 mixed-tree rule) - the "
        "full reconcile battery plus the suite-matrix regeneration, then close "
        "this row | first=yes")
    if old_row not in text:
        raise SystemExit("E_CLOSE_DEBT: open row not found")
    done_row = (
        "- [x] opened=R2257 | item=reconcile-battery-R2258 | note=R2257 "
        "changed src/os (state_seq.py, test_state_seq.py, evidence_R2257.py), "
        "one runner entry and three queue/board files; run on the committed "
        "tree at R2258 with zero product code changed = RUNNER PASS 433/433 "
        "suites plus controls 7/7 in 989.7s with birth-site TMP RECLAIM "
        "932/932 worlds 326.57 MiB busy=0 failed=0 (qa/reconcile-all-R2258.log, "
        "765852B at RUNNER close, single-writer utf-8 LF through "
        "battery_stream.py), expected criteria total=3576; four follow-up "
        "sections all PASS through src/os/battery_followup_R2258.py - matrix "
        "regenerated to 433 suites / 3576 criteria and read back byte-identical "
        "(docs/sandbox-suite-matrix.md, 42111B, green=433/433), fingerprint "
        "CLEAN over 5 domains, runner profile --daily --check PASS, writer "
        "census re-frozen then DRIFT-CLEAN files=2200 tee=1671 baselined=529 "
        "flags=0; the +1 suite / +6 criteria against R2256 is exactly the R2257 "
        "os-state-seq suite joining the registry | closed=R2258")
    text = text.replace(old_row, "", 1)
    successor = (
        "- [ ] opened=R2258 | item=product-face-R2259 | "
        "note=the battery debt is clear, the floors read main 5/5 tech 10/10 "
        "explore 10/10 at closeout and the P1 canonical rows stay blocked-on-CEO, "
        "so the next window claims the top real queue row and ships one product "
        "face; pre-register its criteria INSIDE the queue row BEFORE the code "
        "and run the zero-occupancy anchor check at HEAD first | first=yes")
    open_marker = "## Open" + nl
    idx = text.index(open_marker) + len(open_marker)
    text = text[:idx] + nl + successor + nl + text[idx:]
    closed_marker = "## Closed" + nl
    cidx = text.index(closed_marker) + len(closed_marker)
    text = text[:cidx] + nl + done_row + nl + text[cidx:]
    text = text.replace("twenty-fourth consecutive disclosure at R2257",
                        "twenty-sixth consecutive disclosure at R2258", 1)
    text = text.replace("\n\n\n", "\n\n")
    with io.open(path, "w", encoding="utf-8", newline="") as h:
        h.write(text)
    print("debt bytes=%d" % os.path.getsize(path))


def close_export():
    path = os.path.join(ROOT, "docs", "status-export.json")
    with io.open(path, encoding="utf-8", newline="") as h:
        data = json.load(h)
    data["export_ts"] = "2026-10-29T14:2x+08:00"
    for row in data["results"]:
        if row[0].isdigit():
            row[0] = str(TICK)
            break
    data["results"].insert(0, [
        ROUND,
        "R2258 verification window on the committed tree: RUNNER PASS 433/433 "
        "suites green plus reconcile controls 7/7 in 989.7s with birth-site "
        "TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 failed=0 (single-writer "
        "utf-8 LF through battery_stream.py), expected criteria total=3576; "
        "four follow-up sections all PASS via src/os/battery_followup_R2258.py "
        "- matrix 433 suites / 3576 criteria read back byte-identical "
        "(42111B, green=433/433), fingerprint CLEAN 5 domains, runner profile "
        "--daily --check PASS, writer census re-frozen then DRIFT-CLEAN "
        "files=2200 tee=1671 baselined=529 flags=0. The +1 suite / +6 criteria "
        "against R2256 is exactly the R2257 os-state-seq suite joining the "
        "registry. Register row reconcile-battery-R2258 closed, successor "
        "product-face-R2259 opened as first=yes. Zero product code changed: a "
        "0-point verification window."])
    data["do"] = (
        "verification window R2258: the R2257 state-sequence suite is now "
        "covered by the whole battery instead of only its own suite plus "
        "neighbours - RUNNER PASS 433/433 suites and controls 7/7 in 989.7s, "
        "then matrix 433 suites / 3576 criteria byte-identical, fingerprint "
        "CLEAN over 5 domains, profile PASS and census DRIFT-CLEAN files=2200; "
        "zero product code changed, so this window buys back debt rather than "
        "shipping a face")
    data["ceo_face"]["current"] = (
        "R2258 验证轮：把 R2257 新加的轮次序列套件纳入全量回归——整批 433/433 "
        "套件全绿 + 对账控制 7/7（989.7s，出生地临时件回收 932/932 世界 "
        "326.57 MiB，busy=0 failed=0），随后四段跟进全过：套件矩阵重生成 "
        "433 套件 / 3576 判据并回读逐字节同一、指纹链 5 域 CLEAN、runner profile "
        "PASS、写入者普查 DRIFT-CLEAN（files=2200）。本轮不动任何产品代码，"
        "如实记 0 分验证轮，只把上轮欠的验证债还清。")
    data["ceo_face"]["latest_artifact"] = (
        "qa/reconcile-all-R2258.log（765852B，RUNNER PASS 433/433 + 四段跟进 "
        "VERDICT PASS）、docs/sandbox-suite-matrix.md（42111B，433 套件/3576 判据，"
        "green=433/433）；辅助件 src/os/battery_followup_R2258.py（四段单写者跟进器）；"
        "2026-10-29 14:2x")
    data["ceo_face"]["last_artifact"] = (
        "qa/reconcile-all-R2258.log（R2258，2026-10-29）")
    data["ceo_face"]["next_milestone"] = (
        "R2259 回到产品面：领最上一条真队列行，判据先写进队列行再动代码，"
        "锚点 HEAD 零占用检查先行，交一件可跑实物（套件 + 双跑证据）")
    data["ceo_face"]["next_milestone_due"] = "2026-10-30T12:00:00+08:00"
    with io.open(path, "w", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("export bytes=%d results=%d"
          % (os.path.getsize(path), len(data["results"])))


def close_backlog():
    path = os.path.join(ROOT, "src", "os", "backlog.md")
    with io.open(path, encoding="utf-8", newline="") as h:
        text = h.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    row = (
        "- [x] [done 2026-10-29 R2258] verification window on the debt "
        "register first item (reconcile-battery-R2258, opened by R2257): the "
        "full reconcile battery and the suite-matrix regeneration ran on the "
        "committed tree with zero product code changed (the R2168 mixed-tree "
        "rule) - RUNNER PASS 433/433 suites green plus reconcile controls 7/7 "
        "in 989.7s with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB "
        "busy=0 failed=0 (qa/reconcile-all-R2258.log, 765852B at RUNNER close, "
        "single-writer utf-8 LF through src/os/battery_stream.py), expected "
        "criteria total=3576. Four post-battery sections then all PASS through "
        "the new single-writer helper src/os/battery_followup_R2258.py: matrix "
        "regenerated to 433 suites / 3576 criteria and read back byte-identical "
        "(docs/sandbox-suite-matrix.md, 42111B, green=433/433), fingerprint "
        "chain CLEAN over 5 domains, runner profile --daily --check PASS, "
        "writer census re-frozen then DRIFT-CLEAN files=2200 tee=1671 "
        "baselined=529 disappeared=0 flags=0, closing on VERDICT PASS. The "
        "measured deltas against R2256 (432 suites / 3570 criteria) are +1 "
        "suite and +6 criteria, exactly the R2257 os-state-seq suite joining "
        "the registry. Honest score: a 0-point verification window with no "
        "product face; the register row is closed and the successor "
        "product-face-R2259 opened as first=yes. Honest disclosure: the first "
        "battery attempt was piped through a truncating selector, so its "
        "stdout never reached the caller and the five-minute no-output rule "
        "killed it; an ownership check proved zero surviving runners and no "
        "evidence file (battery_stream writes only at the end) before the "
        "sanctioned unpiped run.")
    lines = text.split(nl)
    idx = 1
    for i, line in enumerate(lines):
        if line.startswith("#"):
            idx = i + 1
            if i + 1 < len(lines) and lines[i + 1].strip() == "":
                idx = i + 2
            break
    lines.insert(idx, row + nl)
    with io.open(path, "w", encoding="utf-8", newline="") as h:
        h.write(nl.join(lines))
    print("backlog bytes=%d" % os.path.getsize(path))


if __name__ == "__main__":
    close_state()
    close_debt()
    close_export()
    close_backlog()