"""R2316 closeout: state, export, heartbeat and the board line.

ASCII source; the Chinese CEO face lives in the JSON data file.

Usage: python src/os/closeout_R2316.py
"""

import datetime
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEART = os.path.join(ROOT, "heartbeat.txt")
BOARD = os.path.join(ROOT, "src", "os", "backlog.md")

NOW = datetime.datetime.now().astimezone()
NOW_ISO = NOW.isoformat(timespec="seconds")
DUE = (NOW + datetime.timedelta(hours=48)).isoformat(timespec="seconds")

ROUND_LOG = (
    "R2316 honest disclosures: (a) the first battery on the R2315 tree was "
    "RED in two places and both were real defects, never an EOL artefact - "
    "the three R2315 reader-wire evidence files had been written through a "
    "shell redirection so the census flagged them as new-dialect "
    "class=pwsh-capture (suite reconcile-daily-census, criterion "
    "cd7-live-real-tree exit=2 DRIFT-FLAG, 3 flags), and the live residue "
    "read 187 rounds against a 186-round triage declaration because R2300 "
    "had no entry (suite os-residue-triage, AC-RTR6 FAIL, untriaged=1). "
    "(b) The repair regenerated the evidence from a fresh double suite run "
    "plus the live refusal through ONE python writer rather than "
    "transcoding, but its first live leg passed the wrong argv and wrote a "
    "95B BAD_ARGS capture, which was discarded and re-taken with "
    "--capability/--reason/--declared-by (2980B, sha16 C0702EA43F9DE631, "
    "no BOM, CRLF 0). (c) Round R2300 was triaged DELIVERED off evidence, "
    "not assumption - tech.md:366 carries [done 2026-11-01 R2300] for the "
    "gate_drift row and commit b6bf3a38 read that committed tree green - "
    "and the declaration grew 186 -> 187 entries with every existing entry "
    "byte-intact (50923B -> 51429B after the successor row). (d) tasks.md "
    "was left untouched: the P-47 canonical board carries no row for a "
    "verification window, disclosed rather than silently skipped. (e) The "
    "one waiting local-lane item stays the elevated-shell S4U "
    "re-registration, seventy-seventh consecutive disclosure."
)

TOKENS = (
    "R2316 tokens: local=~22k api=0 api_reason=one red battery on the "
    "committed tree, its two root causes repaired at their birth sites and "
    "one green re-run; zero cloud calls and zero external API touches."
)

SELF_HEAL = (
    "R2316 self-heal check: BigDomain-OSLoop is registered and its "
    "principal still reads LogonType=InteractiveToken, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 "
    "already passes an explicit S4U principal and needs an elevated shell to "
    "apply, and this session runs unelevated, so the loop definition was "
    "left untouched. Open local-lane item for an elevated window "
    "(seventy-seventh consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md)."
)

HEART_LINE = (
    "tick 2316 2026-11-01 verification window with a real repair: the first "
    "full battery on the committed R2315 tree was RED 463/465 with 3 failed "
    "assertions - three R2315 reader-wire evidence files had been written "
    "through a shell redirection (census cd7-live-real-tree DRIFT-FLAG x3) "
    "and the live residue read 187 rounds against a 186-round triage "
    "declaration (os-residue-triage AC-RTR6, R2300 untriaged) - both were "
    "repaired at their birth sites through src/os/repair_R2316.py, which "
    "regenerated the evidence from a fresh double suite run plus the live "
    "refusal with one utf-8 LF python writer and appended the R2300 entry "
    "off the board row and commit b6bf3a38; the re-run on the committed tree "
    "886743c8 read RUNNER PASS 465/465 suites plus controls 7/7 in 842.2s "
    "with criteria total 3766, exactly the pre-registered target, and the "
    "four follow-up sections read PASS after suite_matrix regenerated the "
    "stale doc to 465 suites / 3766 criteria at 44685B. Zero product code "
    "changed, so 0 product points, honestly recorded."
)

NEXT_ITEM = (
    "- [ ] R2316 first item: BACK TO THE PRODUCT FACE on the row the reader "
    "names. python src/os/queue_head.py --head tech reads state/queue/tech.md"
    ":376 (prefix AC-GDRT1, claimable=11) - the gate_decl_retire seed, whose "
    "AC-GDRT1..AC-GDRT6 criteria are already pinned inside that row BEFORE "
    "the code. Run a fresh zero-occupancy anchor check at HEAD (git grep -F "
    "rc=1) before writing anything, ship one product face with its suite, "
    "refill the tech floor with one real gap row if the claim drops "
    "claimable to 10, and commit BEFORE any battery (the R2168 mixed-tree "
    "rule) - the battery is then the successor row. Also open and needing an "
    "ELEVATED shell: BigDomain-OSLoop reads LogonType=InteractiveToken "
    "(seventy-eighth consecutive disclosure; carried as "
    "loop-s4u-reconcile in state/debt.md)."
)

DISCHARGE = (
    " [done 2026-11-01 R2316] Discharged as a verification window that "
    "turned into a repair because the first run was RED and both reds were "
    "real, never widened: RUNNER FAIL 463/465 suites with 3 failed "
    "assertions (qa/reconcile-all-R2316.log, the honest red leg). Root "
    "cause one = the R2315 reader-wire evidence had been shell-captured, so "
    "the census read three new-dialect files; root cause two = the live "
    "residue carried 187 rounds against a 186-round declaration. "
    "src/os/repair_R2316.py regenerated a/b from a fresh double suite run "
    "and the live refusal (SUITE PASS 6/6 identical sha16 2A0C716C646A3446, "
    "405B/405B, live 2980B sha16 C0702EA43F9DE631, no BOM, CRLF 0) and "
    "appended the R2300 triage entry off tech.md:366 and commit b6bf3a38 "
    "with one minimal text insertion (186 -> 187 entries, readback ok). Both "
    "gates then read green on their own: census flags=0 DRIFT-CLEAN, "
    "residue TRIAGED 187/187 untriaged=0, and the three previously failing "
    "suites re-read 6/6, 8/8, 6/6. The re-run on the committed tree "
    "886743c8 with an empty git status = RUNNER PASS 465/465 suites plus "
    "controls 7/7 in 842.2s, TMP RECLAIM 932/932 worlds 326.57 MiB "
    "busy=0 failed=0 (qa/reconcile-all-R2316-run2.log, single utf-8 LF "
    "writer through battery_stream), criteria total 3766 - exactly the "
    "pre-registered +1 suite / +6 criteria against R2314. Four follow-up "
    "sections: matrix FAILED first on the stale doc and did not rewrite it, "
    "suite_matrix regenerated 465 suites / 3766 criteria (44685B), re-run "
    "read all four PASS, VERDICT run2 PASS. Register closed "
    "reconcile-battery-R2316 through its own writer (line 85, open 2->1, "
    "done 62->63) and opened product-face-R2317 first=yes through "
    "debt_append."
)


def write_json(path, data):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def state():
    with io.open(STATE, encoding="utf-8") as handle:
        data = json.load(handle)
    data["tick"] = 2316
    for line in (ROUND_LOG, TOKENS, SELF_HEAL):
        data["log"].append(line)
    write_json(STATE, data)
    return len(data["log"])


def export():
    with io.open(EXPORT, encoding="utf-8") as handle:
        data = json.load(handle)
    data["export_ts"] = NOW_ISO
    data["do"] = (
        "R2316 \u9a8c\u8bc1\u8f6e\u5e26\u4fee\u590d\uff1aR2315 "
        "\u6811\u4e0a\u7b2c\u4e00\u6b21\u5168\u91cf\u5bf9\u8d26\u662f\u7ea2"
        "\u7684\uff08463/465\uff093 \u6761\u65ad\u8a00\u5931\u8d25\uff09\uff0c"
        "\u4e24\u4e2a\u6839\u56e0\u5747\u662f\u771f\u7f3a\u9677\uff1aR2315 "
        "\u4e09\u4efd\u8bc1\u636e\u88ab shell \u91cd\u5b9a\u5411\u5199\u6210 "
        "pwsh \u65b9\u8a00\uff08\u666e\u67e5 cd7 DRIFT-FLAG x3\uff09\uff0c"
        "\u4ee5\u53ca\u5b9e\u65f6\u6b8b\u7559 187 \u8f6e\u5bf9 \u4e00\u4e2a "
        "186 \u8f6e\u7684\u4e09\u5206\u7c7b\u58f0\u660e\uff08R2300 "
        "\u672a\u5206\u7c7b\uff09\uff08\u3002\u4fee\u590d\u5728\u51fa\u751f"
        "\u5730\uff1a\u4e00\u4e2a python \u5355\u5199\u8005\u91cd\u751f\u6210"
        "\u8bc1\u636e\uff0cR2300 \u6309\u677f\u5355\u884c\u4e0e commit "
        "b6bf3a38 \u8865\u767b\u8bb0\uff1b\u91cd\u8dd1 465/465 \u5168\u7eff"
        "\u3001\u5224\u636e 3766 \u4e0e\u9884\u6ce8\u518c\u4e00\u81f4\u3002"
    )
    face = data["ceo_face"]
    face["current"] = (
        "R2316 \u672c\u8f6e\u4e3a\u9a8c\u8bc1\u4e0e\u4fee\u590d\u7a97"
        "\uff1a\u5df2\u63d0\u4ea4\u6811 886743c8 \u4e0a\u5168\u91cf\u5bf9"
        "\u8d26\u91cd\u8dd1\u8bfb RUNNER PASS 465/465 \u5957\u4ef6 + \u63a7"
        "\u5236 7/7\uff0c\u5224\u636e 3766 \u6761\u4e0e\u9884\u6ce8\u518c"
        "\u5b8c\u5168\u4e00\u81f4\uff084\u4e2a\u8ddf\u6bb5\u5168 PASS\uff09"
        "\uff1b\u73af\u5883\u9762\u672a\u53d8\uff1aorders \u5c3e\u884c"
        "\u4ecd\u4e3a 2026-10-31 18:23\uff0cdecisions \u65e0\u65b0\u884c"
        "\uff0c\u53f0\u8d26\u5f00\u9879\u4ec5\u5269 S4U \u91cd\u6ce8\u518c"
        "\u4e00\u9879\uff08\u9700\u63d0\u6743\u7a97\u53e3\uff09\uff1b"
        "\u672c\u8f6e\u65e0\u4ea7\u54c1\u4ee3\u7801\u6539\u52a8\uff0c\u8bda"
        "\u5b9e\u8ba1 0 \u5206\u3002"
    )
    face["latest_artifact"] = (
        "qa/reconcile-all-R2316-run2.log\uff08465/465 \u5168\u7eff\u3001"
        "\u5224\u636e 3766\u3001\u63a7\u5236 7/7\u3001842.2 \u79d2\uff09+ "
        "src/os/repair_R2316.py\uff08\u4e24\u5904\u7f3a\u9677\u51fa\u751f"
        "\u5730\u4fee\u590d\uff09\uff0c2026-11-01"
    )
    face["last_artifact"] = face["latest_artifact"]
    face["next_milestone"] = (
        "R2317 \u56de\u4ea7\u54c1\u9762\uff1astate/queue/tech.md:376 "
        "AC-GDRT1 gate_decl_retire\uff08\u95e8\u58f0\u660e\u9000\u5f79\uff09"
        "\u5148\u505a\u96f6\u5360\u7528\u951a\u68c0\u3001\u518d\u51fa\u6a21"
        "\u5757+\u5957\u4ef6\uff0c\u63d0\u4ea4\u540e\u624d\u8dd1\u7535\u6c60"
    )
    face["next_milestone_due"] = DUE
    data["results"].insert(0, [
        "R2316",
        "the first battery on the R2315 tree was red for two real reasons and "
        "both were repaired at their birth sites: three shell-captured "
        "evidence files were regenerated through one python writer, and round "
        "R2300 was triaged DELIVERED off the board row and commit b6bf3a38 so "
        "the live residue reads TRIAGED 187/187; the re-run on the committed "
        "tree read 465/465 suites, controls 7/7, criteria 3766 exactly as "
        "pre-registered, and all four follow-up sections PASS after "
        "suite_matrix regenerated the stale doc",
    ])
    if len(data["results"]) > 64:
        data["results"].pop()
    data["outs"].append([
        "src/os/repair_R2316.py",
        "on",
        "R2316 repair: regenerates the three shell-captured R2315 evidence "
        "files from a fresh double suite run plus the live refusal through "
        "one utf-8 LF writer (census flags 3 -> 0), and appends the R2300 "
        "triage entry as a minimal text insertion (186 -> 187 entries, every "
        "existing entry byte-intact); the re-run battery read 465/465 green",
    ])
    if len(data["outs"]) > 42:
        data["outs"].pop(0)
    sd = data["self_drive"]
    for key, path in (("queue_main_open", "main"), ("queue_tech_open", "tech"),
                      ("queue_explore_open", "explore")):
        full = os.path.join(ROOT, "state", "queue", path + ".md")
        with io.open(full, encoding="utf-8") as handle:
            sd[key] = sum(1 for line in handle if line.startswith("- [ ]"))
    write_json(EXPORT, data)
    return data["export_ts"]


def heartbeat():
    with io.open(HEART, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(HEART_LINE + "\n")


def board():
    with io.open(BOARD, encoding="utf-8") as handle:
        lines = handle.read().split("\n")
    head = lines[0]
    old = "- [ ] [carried 2026-11-01 R2314] R2315 first item:"
    assert head.startswith(old), "unexpected board head"
    lines[0] = ("- [x] [done 2026-11-01 R2316] R2315 first item:"
                + head[len(old):] + DISCHARGE)
    lines.insert(0, NEXT_ITEM)
    with io.open(BOARD, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
    return len(lines)


def main(argv=None):
    n = state()
    ts = export()
    heartbeat()
    size = board()
    print("STATE log=%d tick=2316" % n)
    print("EXPORT ts=%s" % ts)
    print("HEART appended")
    print("BOARD lines=%d" % size)
    return 0


if __name__ == "__main__":
    sys.exit(main())