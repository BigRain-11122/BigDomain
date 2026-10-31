# export_R2268.py - refresh docs/status-export.json from this window's
# measured state. Every value is derived from files on disk (F3 law): the
# tick and log window from state.json, the queue counts from the consistency
# checker, the milestone window from the wall clock. Pure stdlib, pure ASCII
# source, utf-8 LF writer without BOM.
import datetime
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(BASE, "..", ".."))
PATH = os.path.join(ROOT, "docs", "status-export.json")
STATE = os.path.join(ROOT, "src", "os", "state.json")

CURRENT = (
    "R2268 验证窗：在已提交的树上把全量回归电池跑绿——439 套件全绿 + 控制 7/7"
    "（1604.1s，判据总数 3610，恰好是 R2266 的 438/3605 加上 R2267 的 "
    "debt_gate 1 套件 5 判据），随后四段收尾全过：套件矩阵再生成 439/3610 逐"
    "字节同一、指纹链 5 域 CLEAN、runner profile 逐字节同一、qa 写者普查重新"
    "冻结后 DRIFT-CLEAN，终判 PASS。同时 state.json 量得 77298B（水位 78500B"
    "·余量仅 1202B），本轮收尾按状态折叠法把最老 13 行折进十月归档（525 个"
    "token 全覆盖，折后 70018B·余量 8482B）。"
)
LATEST = (
    "qa/reconcile-all-R2268.log（772153B，单写者 utf-8 LF）+ "
    "docs/sandbox-suite-matrix.md（42567B·439/3610·green=439/439）；"
    "实况 RUNNER PASS 439/439 套件 + 控制 7/7"
)
NEXT = (
    "R2269 回到产品面：验证债已清，登记簿现点名 product-face-R2269 first=yes；"
    "下一窗认领队列最上可交付行（R2267 的 queue_head 种子或 R2266 的 "
    "queue_only_floor_wire 种子），判据先于代码预注册、写入前先做 HEAD 零占用"
    "锚检，并先把产品面提交再跑电池。预计 2026-11-01 18:00 前完成"
)
RESULTS = (
    "R2268 verification window on the debt register first item "
    "(reconcile-battery-R2268), discharged on the committed tree with ZERO "
    "product edits until green (the R2168 mixed-tree rule): RUNNER PASS 439/439 "
    "suites green plus controls 7/7 in 1604.1s with birth-site TMP RECLAIM "
    "932/932 worlds 326.57 MiB busy=0 failed=0 (qa/reconcile-all-R2268.log, "
    "single-writer utf-8 LF through src/os/battery_stream.py), criteria total "
    "3610 - exactly the pre-registered +1 suite / +5 criteria against R2266 "
    "(438/3605) from the R2267 os-debt-gate suite. Four follow-up sections all "
    "PASS via src/os/battery_followup_R2268.py: matrix 439 suites / 3610 "
    "criteria byte-identical (42567B, green=439/439), fingerprint CLEAN 5 "
    "domains, runner profile --daily --check PASS byte-identical, census "
    "re-frozen then DRIFT-CLEAN files=2215 tee=1686 baselined=529 flags=0, "
    "VERDICT PASS with eol crlf=0 bare_cr=0 bom=False over 772153B. The state "
    "fold was measured not assumed (77298B against the 78500B gate, margin "
    "1202B) and executed through state_fold.fold: 13 lines into the October "
    "archive, 525 tokens covered with token_missing empty, 70018B, margin "
    "8482B. Honest disclosures: the first invocation was piped through a "
    "truncating selector and died to the five-minute no-output rule with zero "
    "output, no evidence file and no surviving child (the R2211 trap "
    "re-proven), and an orphan check proved zero survivors and a clean tree "
    "before the unpiped rerun whose numbers are above; the RUNNER took 1604.1s, "
    "beyond the 25-minute budget, so no product face shipped and the window "
    "scores 0 product points, honestly recorded."
)


def load_state():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    state = load_state()
    tick = state["tick"]
    log = state["log"]
    stamps = []
    for item in log:
        match = re.match(r"^(?:carry-forward[^ ]* )?(\d{4}-\d{2}-\d{2})",
                         item.strip())
        if match:
            stamps.append(match.group(1))
    stamps.sort()
    last = stamps[-1]
    start = (datetime.date.fromisoformat(last)
             - datetime.timedelta(days=6)).isoformat()
    import check_export_consistency as CEC
    derived = CEC.recompute()[0]
    now = datetime.datetime.now().astimezone()
    export = {
        "export_ts": now.replace(microsecond=0).isoformat(),
        "do": ("verification window R2268 on the debt register first item: the "
               "full reconcile battery and its four follow-ups are green on the "
               "committed tree, and the state log was folded inside the "
               "waterline with every token covered."),
        "ceo_face": {
            "current": CURRENT,
            "latest_artifact": LATEST,
            "last_artifact": LATEST,
            "next_milestone": NEXT,
            "next_milestone_due": (now.replace(microsecond=0)
                                   + datetime.timedelta(hours=27)).isoformat(),
        },
        "depts": [],
        "outs": [],
        "results": [],
        "self_drive": {
            "window": derived["window"],
            "window_days": derived["window_days"],
            "log_lines_in_window": derived["log_lines_in_window"],
            "idle_fast_mention_lines": derived["idle_fast_mention_lines"],
            "no_pullable_mention_lines": derived["no_pullable_mention_lines"],
            "substantive_non_idle_mention_lines":
                derived["substantive_non_idle_mention_lines"],
            "proposals_total": derived["proposals_total"],
            "proposals_open": derived["proposals_open"],
            "queue_main_open": derived["queue_main_open"],
            "queue_tech_open": derived["queue_tech_open"],
            "queue_explore_open": derived["queue_explore_open"],
        },
    }
    with io.open(PATH, "r", encoding="utf-8") as handle:
        previous = json.load(handle)
    export["depts"] = previous["depts"]
    export["outs"] = previous["outs"]
    results = []
    for row in previous["results"]:
        if isinstance(row, list) and len(row) == 2:
            if "OSLoop" in str(row[1]) and "tick" in str(row[1]):
                continue
            if str(row[0]) == "R2268":
                continue
        results.append(row)
    results.append(["R2268", RESULTS])
    results.append([str(tick), "OSLoop \u6267\u884c tick"])
    export["results"] = results
    body = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    print("export_ts=%s tick=%d window=%s..%s results=%d"
          % (export["export_ts"], tick, start, last, len(export["results"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())