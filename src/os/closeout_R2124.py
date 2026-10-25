"""R2124 closeout: state tick/log, backlog + explore-queue done flips,
status-export refresh. Every number is read off the on-disk evidence
(F3 law). Pure ASCII source; Chinese only in the data written out.

Honesty note: this round did NOT run the full reconcile battery and did
NOT regenerate the suite matrix (25-minute round budget), so neither is
claimed in the log or the export; targeted regression of the three
adjacent apimarket suites is the evidence recorded instead.
"""

import datetime
import hashlib
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")
MAIN = os.path.join(ROOT, "tasks.md")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
SUITE = os.path.join(ROOT, "qa",
                    "apimarket-provideridentity-R2124.log")
SUITE2 = os.path.join(ROOT, "qa",
                      "apimarket-provideridentity-R2124-2.log")
REG = os.path.join(ROOT, "qa", "regression-R2124.log")


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def suite_facts():
    a = read_bytes(SUITE)
    b = read_bytes(SUITE2)
    return {"same": a == b,
            "sha16": hashlib.sha256(a).hexdigest()[:16],
            "bytes": len(a),
            "verdict": a.decode("utf-8").splitlines()[-1]}


def open_count(path):
    return sum(1 for line in io.open(path, encoding="utf-8")
               if line.startswith("- [ ]"))


def texts():
    round_text = (
        "R2124 (five-silence scan clean: ledger zero new @BigDomain"
        " rows, decisions zero new content-addressed tokens against the"
        " stored baseline - newest still D-20261025-13 - benchmarks"
        " refreshed 2026-10-25 inside 7 days, tree clean with no"
        " index.lock; all four tech heads stayed gated or standing -"
        " docker host absent, logs toolkit standing maintenance, member"
        " refunded schema product-gated, live-mtime row waiting on a real"
        " event - and the single open explore row stays gated on the"
        " merchant id) - so this window seeded and claimed a fresh P3 row"
        " with AC-AMPI1..AC-AMPI8 pre-registered BEFORE the code existed"
        " (ten anchors, all git grep -F zero-occupancy rc=1 on"
        " 2026-10-25): the apimarket distribution-duty faces that R2123's"
        " regulation crawl proved missing. Product: the marketplace"
        " identified a seller by a bare dev_account string and had no"
        " real-name layer, no public display layer and no review refusal"
        " face. Three faces now exist. (1) register_provider + api_"
        "provider_identity: an append-only apimarket_providers table,"
        " exactly one row per developer, name and unified social credit"
        " code trimmed non-empty, gate order account -> name -> credit ->"
        " registry -> duplicate (a bad name on a non-developer is a shape"
        " refusal, not a registry refusal), zero rows stored on every"
        " refusal, zero token movement; an unregistered developer reads"
        " back an honest empty identity rather than an error. (2)"
        " api_public_listings: the outside reader's face - one row per"
        " LIVE listing with the registered provider name and credit code,"
        " disclosure_ok false plus null identity for an unregistered"
        " seller (shown honestly, not hidden), the AIGC label, the"
        " current price, and the review state pending/approved/refused"
        " with a reason only on refusal; retired shelves drop out."
        " (3) review_listing + api_review_queue: one append-only review"
        " row per listing, approve/refuse only, a refusal without a"
        " reason is refused, duplicate decisions refused, and the pending"
        " queue is ordered (listed_utc, listing_id) with its count tied"
        " to the public face's pending set. Suite src/sandbox/ledger/"
        "test_apimarket_provideridentity.py %s, double-run byte-identical"
        " sha16 %s (%dB, utf-8 LF pure ASCII); wired"
        " ledger-apimarket-provideridentity (8). Targeted regression of"
        " three adjacent suites all green (qa/regression-R2124.log:"
        " test_apimarket 7/7, marketstats 8/8, watchlist 8/8). Honest"
        " boundaries: the full reconcile battery and the suite matrix"
        " were NOT re-run this round (25-minute budget), so no battery or"
        " matrix number is claimed; and enforcement into publish_api was"
        " deliberately NOT wired (this slice adds the faces only, so 55"
        " existing suites keep their contracts) - wiring the gate is the"
        " next slice and needs its own pre-registered criteria.")

    tokens = ("R2124 tokens: local=~85k api=0 api_reason=no cloud calls;"
              " five-silence scan plus one new apimarket face family"
              " (provider identity, public display, review refusal), a"
              " new suite at 8/8 double-run, three adjacent regression"
              " suites, and state/export closeout; full battery and"
              " matrix intentionally skipped under the round budget")
    return round_text, tokens


def state_patch():
    """Text-surgical state write: the canonical on-disk layout keeps
    one log item per line at 16-space indent with the closing bracket
    at one space, so re-serialising the whole document is forbidden
    (AC-LT11). Only the tick token and the two new log lines change."""
    round_text, tokens = texts()
    text = io.open(STATE, encoding="utf-8").read()
    if '"tick": 2124' in text:
        raise SystemExit("state already patched")
    text = text.replace('"tick": 2123', '"tick": 2124', 1)
    tail = "\n ]\n}\n"
    if not text.endswith(tail):
        raise SystemExit("unexpected state layout tail")
    body = text[:-len(tail)]
    last_line_start = body.rfind("\n")
    last_line = body[last_line_start + 1:]
    if not last_line.startswith('                "'):
        raise SystemExit("unexpected last log line layout")
    body = (body[:last_line_start + 1] + last_line + ","
            + "\n" + "                " + json.dumps(round_text,
                                                     ensure_ascii=False)
            + ",\n" + "                " + json.dumps(tokens,
                                                     ensure_ascii=False))
    io.open(STATE, "w", encoding="utf-8", newline="\n").write(body + tail)
    check = json.load(io.open(STATE, encoding="utf-8"))
    if int(check["tick"]) != 2124 or len(check["log"]) != 100:
        raise SystemExit("state patch verification failed")
    return check["tick"], len(check["log"])


def main():
    suite = suite_facts()
    if not suite["same"]:
        raise SystemExit("double-run evidence is not identical")
    reg = read_bytes(REG).decode("utf-8")
    reg_ok = "rc=0" in reg and "FAIL" not in reg

    round_text, tokens = texts()

    done_note = ("[done 2026-10-25 R2124]（判据 AC-AMPI1..AC-AMPI8 预注册先于代码·"
                 "十锚 git grep -F 零占用 rc=1·套件 8/8 双跑逐字节同一 sha16 "
                 "%s=qa/apimarket-provideridentity-R2124.log+-2·相邻三套件回归全绿"
                 " qa/regression-R2124.log·诚实边界=本轮未跑全量电池与矩阵、"
                 "publish 强制接线留后继切片）" % suite["sha16"])

    tick, loglen = state_patch()

    def flip(path, marker, note):
        lines = io.open(path, encoding="utf-8").read().splitlines(True)
        out = []
        hit = False
        for line in lines:
            if not hit and line.startswith("- [ ] " + marker):
                line = "- [x] " + line[len("- [ ] "):]
                hit = True
                line = line.rstrip("\n") + " " + note + "\n"
            out.append(line)
        io.open(path, "w", encoding="utf-8", newline="\n").write("".join(out))
        return hit

    flipped = flip(EXPLORE,
                   "P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97\u8ba4"
                   "\u9886\uff08R2124\uff09", done_note)
    backlog_line = (
        "- [x] P3 explore 自补种并同窗认领（R2124）apimarket "
        "**平台分发义务面三件**（register_provider + api_provider_identity"
        " 实名层 · api_public_listings 公开展示层 · review_listing + "
        "api_review_queue 审核拒绝层）——" + done_note.strip() + "\n")
    backlog_text = io.open(BACKLOG, encoding="utf-8").read()
    io.open(BACKLOG, "w", encoding="utf-8", newline="\n").write(
        backlog_line + backlog_text)

    self_drive = {"window": "2026-10-19..2026-10-25",
                  "window_days": 7,
                  "queue_main_open": open_count(MAIN),
                  "queue_tech_open": open_count(TECH),
                  "queue_explore_open": open_count(EXPLORE)}
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    data["export_ts"] = datetime.datetime.now().astimezone().replace(
        microsecond=0).isoformat()
    data["ceo_face"] = {
        "current": (
            "R2124 平台分发义务面三件落地：提供者实名登记（append-only·每开发者恒"
            "一行·名称与统一社会信用代码去空白非空·门序 账户→名称→代码→注册表→重复，"
            "任一拒绝零落库零代币移动）、公开展示层（每张在售挂牌一行：已实名显示提供者"
            "名称与信用代码，未实名诚实标 null+disclosure_ok=false，带 AIGC 标识、现价与"
            "审核态 pending/approved/refused，拒绝才带理由，退役牌不入榜）、审核拒绝面"
            "（一牌一行 append-only·只收 approve/refuse·拒绝必须写理由·重复审核拒收）"
            "与待审队列（按 listed_utc/listing_id 升序，计数与公开展示面待审集合恒等）。"),
        "latest_artifact": (
            "src/sandbox/ledger/apimarket.py（apimarket_providers / apimarket_reviews "
            "两张新表 + register_provider / api_provider_identity / api_public_listings "
            "/ review_listing / api_review_queue 五面）；"
            "src/sandbox/ledger/test_apimarket_provideridentity.py（SUITE 8/8 双跑逐字节"
            "同一 sha16 %s）；qa/apimarket-provideridentity-R2124.log + -2；"
            "qa/regression-R2124.log（相邻三套件 7/7、8/8、8/8 全绿）；"
            "src/sandbox/reconcile_all.py 新接线 ledger-apimarket-provideridentity(8)"
            % suite["sha16"]),
        "next_milestone": (
            "48 小时内：把审核门真正接进 publish_api（未过审/未实名不得上架），并为"
            "「上架前强制实名 + 三类拒绝逐条可验」预注册判据；同步把这五面接进结算报表"
            "（提供者公示段 + 待审队列段 + REPORT_SCHEMA 加法升级），让运营者在一页上"
            "同时看到未实名货架、待审积压与被拒原因。"),
    }
    data["outs"] = data.get("outs", [])
    data["outs"].append([
        "apimarket 平台分发义务面三件（提供者实名 + 公开展示 + 审核拒绝）",
        "on",
        "R2124：R2123 法规普查实证分发平台义务域在产品面完全空缺（提供者身份只是裸 "
        "dev_account 字符串）。本窗补三面五方法两张 append-only 表；判据 AC-AMPI1.."
        "AC-AMPI8 先于代码预注册（十锚零占用 rc=1）；套件 8/8 双跑逐字节同一 sha16；"
        "相邻三套件回归全绿；诚实边界=未跑全量电池与矩阵、publish 强制接线留后继切片。",
        "2026-10-25"])
    data["results"] = data.get("results", [])
    data["results"].append([
        "R2124",
        "R2124 平台分发义务面三件：register_provider/api_provider_identity 实名层、"
        "api_public_listings 公开展示层、review_listing/api_review_queue 审核拒绝面。"
        "套件 SUITE 8/8 双跑逐字节同一（qa/apimarket-provideridentity-R2124.log + -2）；"
        "相邻回归 test_apimarket 7/7 + marketstats 8/8 + watchlist 8/8"
        "（qa/regression-R2124.log）；接线 ledger-apimarket-provideridentity(8)。"
        "诚实声明：本轮未跑 reconcile 全量电池、未重生成 suite matrix、未把审核门接进 "
        "publish_api（零回归取舍，写进预算行与队列行）。"])
    data["self_drive"] = self_drive
    io.open(EXPORT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n")

    print("tick=%d loglen=%d explore_flip=%r suite=%r bytes=%d reg_ok=%r"
          " open(main/tech/explore)=%d/%d/%d"
          % (tick, loglen, flipped, suite["sha16"], suite["bytes"],
             reg_ok, self_drive["queue_main_open"],
             self_drive["queue_tech_open"],
             self_drive["queue_explore_open"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())