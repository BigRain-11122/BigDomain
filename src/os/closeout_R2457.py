"""closeout_R2457 - write this round state, backlog, tasks and heartbeat rows.

R2457 is a product window taken on the CEO fleet order OB-20261105-003656-879
(real output, no new mechanism / rule / document) rather than on the internal
tech queue head: the city read face answered JSON only, so the silicon city
had nothing a person could open. ASCII only; prose is English per the
encoding law.
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(BASE, "state.json")
BACKLOG = os.path.join(BASE, "backlog.md")
TASKS = os.path.join(ROOT, "tasks.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

ROUND = 2457

LINES = [
    "2026-11-05 R2457 PRODUCT window, taken on the CEO fleet order OB-20261105-003656-879 (real output "
    "only, no new mechanism / rule / document) and on the product-first law, not on the debt gate named "
    "product-face-R2456. The five-silence scan HELD this window: git status empty at HEAD 0368b20b with no "
    "index.lock, the evolution ledger carried zero @BigDomain rows, the content-addressed decisions diff "
    "read 129 tokens with new=0 against the stored baseline (rows 199), the group orders tail max_ts 2026-11-05 "
    "00:36 equals the stored last_order, and benchmarks were refreshed 2026-11-03 inside the seven-day gate. "
    "So the choice was not forced by a dispatch: the internal queue head (tech.md AC-PFKC1 row_key_carrier_scope) "
    "is an audit face, and the standing order of the day is real output, so this window shipped a product face "
    "instead. product-face-R2456 is CARRIED, not dropped, and stays open and claimable.",

    "2026-11-05 R2457 SHIPPED, and what a CEO can finally open: src/sandbox/lobby/city_view.html (6653B, "
    "self-contained, zero network references) plus one route in src/sandbox/lobby/city.py, so the read-only "
    "city HTTP face now answers GET /city and GET /city/ with that page while /city/snapshot and /census/<id> "
    "keep their exact JSON contract. Bring-up is unchanged and now gives a human page: "
    "python src/sandbox/lobby/server.py --city-http-port 8092 then open http://127.0.0.1:8092/city/ (the "
    "docker-compose bring-up gets the page for free on the already-published 8092). The page renders the "
    "snapshot package - population, districts, visitors, the ambient line, the event tail - and a census "
    "lookup box that reads /census/<id>, so a visitor can look up B-00231 without a terminal. It carries both "
    "standing compliance surfaces verbatim: the AI 生成内容 label and the non-advice note (non-investment), "
    "plus the read-only statement.",

    "2026-11-05 R2457 EVIDENCE, measured twice and identical: src/sandbox/lobby/test_city_view.py reads "
    "SUITE PASS 6/6 twice with byte-identical verdict lines (AC-CV1 page 200 text/html 6653B offline=True; "
    "AC-CV2 aigc_label=True risk_note=True; AC-CV3 snapshot=json post=405 unknown=404 census=200; AC-CV4 "
    "identical=True bytes=6653 sha16=F4DA3A32459C2E32 and equal to the file on disk; AC-CV5 empty city dir "
    "still serves page=200 snapshot=503 with the not-ready line; AC-CV6 bom=False crlf=0 ascii_src=True "
    "wired=True), qa/city-view-R2457.log written by one utf-8 LF single writer. Both legs start the REAL "
    "server on a private port and a temp db, so no live database was touched. Regression: the 79-criteria "
    "lobby suite stays green (AC-S13 snapshot/census/405/404/read-only proofs unchanged), and the registry "
    "now reads 556 suites / 4312 criteria (555/4306 plus this window os-lobby-city-view(6)).",

    "2026-11-05 R2457 honest disclosures: (a) the first suite run FAILED 5/6 on my own wiring assertion - the "
    "criterion pre-registered the label os-lobby-city-view while the registry row was first written as "
    "lobby-city-view; the REGISTRY was renamed to match the pinned criterion rather than the criterion being "
    "loosened. (b) The page reads live JSON through fetch, so opening the HTML file straight off disk shows "
    "empty fields: the honest way to view it is the server route above (file:// has no origin to fetch from). "
    "(c) No full reconcile battery and no matrix regeneration ran this window (the R2168 mixed-tree rule): "
    "src changed, so a battery is owed FIRST next window on the committed tree, registered as "
    "reconcile-battery-R2458 (first=no, because product-face-R2456 already holds the first slot). "
    "(d) READ-ONLY observation in this repo, not repaired because the city data line owns the file: "
    "src/sandbox/lobby/city_data/world-public.json and citizens-light.jsonl both contain evidently truncated "
    "multi-byte sequences (for example a stray replacement character inside the ambient line), which the new "
    "page will display as-is; seeded for the city data line instead of fixed here. (e) No new document was "
    "written, per the standing order in the same order batch; the only prose added is the backlog claim row "
    "carrying the pre-registered criteria and this round log. (f) The window ran well past its 25-minute "
    "budget on the live two-leg proof.",

    "R2457 tokens: local=~10k api=0 api_reason=product window - one shipped page and one route in the shipped "
    "server, six criteria proved twice on two real-server legs, one adjacent 79-criteria suite re-run green, "
    "one registry row, one single-writer evidence file, and the state/export/backlog/tasks/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
]

BACKLOG_ITEM = (
    "- [x] [done 2026-11-05 R2457] R2457 product window on the CEO fleet order OB-20261105-003656-879: the "
    "silicon city is openable in a browser. SHIPPED src/sandbox/lobby/city_view.html (6653B, self-contained, "
    "zero network references, AI 生成内容 label + non-investment note verbatim) and one route in "
    "src/sandbox/lobby/city.py so GET /city and GET /city/ serve that page while /city/snapshot and "
    "/census/<id> keep their exact JSON contract; bring-up: python src/sandbox/lobby/server.py "
    "--city-http-port 8092 then http://127.0.0.1:8092/city/. Suite src/sandbox/lobby/test_city_view.py "
    "passed AC-CV1..AC-CV6 twice with identical verdicts (qa/city-view-R2457.log, sha16 F4DA3A32459C2E32 of "
    "the served bytes, both legs on a private port and temp db), the 79-criteria lobby suite stayed green, "
    "and the registry reads 556 suites / 4312 criteria. Honest: no battery this window (mixed-tree rule) so "
    "reconcile-battery-R2458 is owed first next window; the page needs the server (file:// shows empty "
    "fields); world-public.json carries pre-existing truncated multi-byte sequences, seeded not fixed. "
    "product-face-R2456 stays open and claimable.\n"
)

TASK_ITEM = (
    "- [x] P-47-1c-2 城市观测页（D-20261105-09 派工延伸·R2457 交付）：只读 HTTP 面从纯 JSON 变为浏览器可开页 "
    "`/city/`+`/city`（city_view.html·零外链·AIGC 标识+非投顾常驻面）——[done 2026-11-05 R2457]"
    "（AC-CV1..CV6 双跑 6/6·邻域 lobby 79/79 绿·证据 qa/city-view-R2457.log）；来源=CEO 机队令 "
    "OB-20261105-003656-879 真实产出面\n"
)


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write_atomic(path, text):
    tmp = path + ".tmp-r2457"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)
    with open(path, "r", encoding="utf-8", newline="") as fh:
        back = fh.read()
    if back != text:
        raise SystemExit("E_CLOSE_R2457_READBACK " + path)


def main():
    raw = load(STATE)
    data = json.loads(raw)
    data["tick"] = ROUND
    log = data.setdefault("log", [])
    for line in LINES:
        if line not in log:
            log.append(line)
    data["last_decision_rows"] = 199
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    canon = state_io.canon(body)
    # write_canon refuses any payload change by design (it is the layout
    # repair face), so the canonical text is landed with the local atomic
    # writer and its own read-back.
    write_atomic(STATE, canon)

    bl = load(BACKLOG)
    # Replace the open claim row with its done form so the board carries one row.
    claim = bl.find("- [ ] R2457 product window")
    if claim != -1:
        end = bl.find("\n", claim) + 1
        bl = bl[:claim] + BACKLOG_ITEM + bl[end:]
        write_atomic(BACKLOG, bl)
    elif "R2457 product window" not in bl:
        write_atomic(BACKLOG, BACKLOG_ITEM + bl)

    bl2 = load(BACKLOG)
    if "AC-CV1..AC-CV6 pre-registered" in bl2 and "[done 2026-11-05 R2457]" not in bl2:
        raise SystemExit("E_CLOSE_R2457_CLAIM_ROW_LEFT_OPEN")

    tasks = load(TASKS)
    if "P-47-1c-2" not in tasks:
        marker = "## "
        pos = tasks.find(marker)
        if pos == -1:
            write_atomic(TASKS, tasks + TASK_ITEM)
        else:
            write_atomic(TASKS, tasks[:pos] + TASK_ITEM + "\n" + tasks[pos:])

    hb = load(HEARTBEAT)
    if not hb.endswith("\n"):
        hb += "\n"
    hb += ("tick=%d %s\n" % (ROUND, "2026-11-05T city view page shipped: GET /city serves the silicon city "
                                       "page (6/6 criteria twice, lobby 79/79 green)"))
    write_atomic(HEARTBEAT, hb)

    print("CLOSEOUT R2457 tick=%d log_added=%d bytes=%d layout=%s"
          % (ROUND, len(LINES), os.path.getsize(STATE), state_io.layout(load(STATE)).get("layout_ok")))
    return 0


if __name__ == "__main__":
    sys.exit(main())