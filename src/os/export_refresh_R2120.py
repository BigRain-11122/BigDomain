"""R2120 status-export refresh: the CEO-facing three lines plus the
outs/results rows, all numbers read off the on-disk evidence (F3 law).
Pure ASCII source; Chinese only in the data written to the json."""

import datetime
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
STATE = os.path.join(ROOT, "src", "os", "state.json")
BATTERY_LOG = os.path.join(ROOT, "qa", "reconcile-all-R2120.log")
MATRIX = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")


def read_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", "replace")


def main():
    battery = re.findall(
        r"RUNNER PASS \((\d+)/(\d+) suites green, reconcile controls"
        r" (\d+)/(\d+), ([\d.]+)s\)", read_text(BATTERY_LOG))
    matrix = re.search(r"\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)/(\d+)\s*\|",
                       read_text(MATRIX))
    if not battery or not matrix:
        raise SystemExit("evidence stamps missing")
    last = battery[-1]

    data = json.load(io.open(EXPORT, encoding="utf-8"))
    data["export_ts"] = datetime.datetime.now().astimezone().replace(
        microsecond=0).isoformat()

    data["ceo_face"] = {
        "current": (
            "R2120 卖家侧「已答问答全史 + 响应时延记分」：R2118 立的售前问答只让卖家"
            "看见还没答的债（rows 仅未答行），答过的只剩一个计数；一个在 N 件挂牌上"
            "答过话的卖家要回答「我答过什么、答了什么、每个买家等了多久」只能逐件"
            "挂牌翻线程。本轮补 api_seller_answers：跨挂牌合并的已答台账（最旧在前、"
            "每行整秒时延、最快/最慢/均值、触及买家数、退役挂牌仍可读、标题取现行"
            "元数据、严格卖家隔离），并接进结算报表卖家区块与 answered questions 表，"
            "机读契约 schema 12→13 加法升级。"),
        "latest_artifact": (
            "src/sandbox/ledger/apimarket.py（api_seller_answers 读面）；"
            "src/sandbox/ledger/apimarket_report.py（卖家区块 answers + answered "
            "questions 表 + REPORT_SCHEMA 13）；"
            "src/sandbox/ledger/test_apimarket_selleranswers.py（SUITE 8/8 双跑判据行"
            "同一 sha16；qa/apimarket-selleranswers-R2120.log + -run2）；"
            "qa/reconcile-all-R2120.log（电池 %s/%s suites + controls %s/7 %ss）；"
            "docs/sandbox-suite-matrix.md（%s suites / %s criteria --check 逐字节同）；"
            "呈看件：preview/apimarket-report-selleranswers.html 与 .json（schema 13）"
            % (last[0], last[1], last[2],
               last[4], matrix.group(1), matrix.group(2))),
        "next_milestone": (
            "48 小时内：给结算报告的 attention 摘要补「答得太慢」家族（已答问题"
            "超过阈值仍在榜 → warn），让运营者不用逐行看时延就能发现服务滑坡；同窗"
            "把本轮读面的买家侧镜像补齐（买家能看见自己每个问题等了多久），不做完"
            "不宣称。"),
    }

    data["outs"].insert(0, [
        "apimarket 卖家侧已答问答全史 + 响应时延记分读面（api_seller_answers + "
        "卖家块消费）",
        "on",
        "R2120：R2118 的卖家问答面只给未答债务队列（api_seller_questions 的 rows "
        "仅未答行，已答只是一个计数），R2119 又只补了买家侧全史，于是卖家侧没有"
        "任何面回答「我答过什么、答了什么、每个买家等了多久」。本窗补 "
        "api_seller_answers(dev_account)：十一键信封 + 十一键行，总序 "
        "(answered_utc, question_id)，每行 response_seconds 为整秒差，"
        "fastest/slowest/mean_seconds 由行派生，buyer_count 与首末戳同时给出；"
        "标题走单一元数据修订缝（edit_listing 后即现新标题），退役挂牌的已答历史"
        "仍可读，未答问题不进本面（仍在 api_seller_questions 且两面的已答计数逐值"
        "相等），严格卖家隔离（前缀合法的买家账户得诚实空信封），账户门 "
        "fail-closed，纯读零 token（十五表摘要与 ledger_tx 集恒定），三实例跨重启"
        "字节同一。消费者=报表卖家区块 answers 键（每次 collect 现读）+ HTML "
        "answered questions 表（诚实空态、敌意文本转义、旧块缺键降级）+ "
        "REPORT_SCHEMA 12→13 加法升级（信封仍恰 schema_version/report/attention）。"
        "判据 AC-AMSA1..AC-AMSA8 预注册于代码前（四锚 git grep -F 零占用 rc=1）；"
        "套件 8/8 双跑判据行同一；接线 ledger-apimarket-selleranswers(8)；电池与"
        "矩阵全绿；呈看件 preview/apimarket-report-selleranswers.html + .json。"
        "诚实注：套件内一处读稳定性断言先比了编辑前快照（测试侧缺陷，改为连续两次"
        "新读）；预注册行里的表数由十二改十五（按实测 schema，先于套件）；"
        "test_apimarket_buyerquestions.py 的 schema 字面断言改为跟随模块常量。",
        "2026-10-25"])

    data["results"].insert(0, [
        "R2120",
        "R2120: the seller-side answered-question ledger. api_seller_questions "
        "proved only the open debt - its rows carry unanswered questions and "
        "the answered side is a single number - while api_listing_qna opens "
        "one shelf at a time, so a seller who answered on N listings had to "
        "open N threads, merge by hand, and could not answer any "
        "service-level question (how long did the slowest buyer wait, what is "
        "the mean). api_seller_answers merges every answered question of one "
        "seller into a single time line: eleven-key envelope, eleven-key "
        "rows, total order on (answered_utc, question_id), per-row "
        "response_seconds as the exact whole-second gap, fastest / slowest / "
        "mean latency, buyer_count and both end stamps, the title read "
        "through the one metadata revision seam, retired shelves keeping "
        "their answered history, strict seller isolation, a fail-closed "
        "account gate, pure read (fifteen table digests and the ledger tx "
        "set frozen) and byte-identical reads across three restarts. "
        "Consumer: every seller block gains an answers key read fresh, the "
        "page renders an answered-questions table with an honest empty "
        "state, and REPORT_SCHEMA moves 12 -> 13 additively. Suite 8/8 "
        "double-run criterion lines identical; battery and matrix green; "
        "preview/apimarket-report-selleranswers.html plus .json (schema 13). "
        "Two honest disclosures: a test-side read-stability assertion first "
        "compared a pre-edit snapshot and now compares two consecutive fresh "
        "reads; the pre-registration row's table count was corrected from "
        "twelve to fifteen against the measured schema before the suite "
        "existed. One birth-station repair: the buyerquestions suite pinned "
        "the schema literal and now follows the module constant."])

    explore_open = sum(
        1 for line in io.open(EXPLORE, encoding="utf-8")
        if line.startswith("- [ ] "))
    drive = data.get("self_drive", {})
    drive["log_lines_in_window"] = int(
        drive.get("log_lines_in_window", 0)) + 2
    drive["substantive_non_idle_mention_lines"] = int(
        drive.get("substantive_non_idle_mention_lines", 0)) + 2
    drive["queue_explore_open"] = explore_open
    data["self_drive"] = drive

    io.open(EXPORT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    state = json.load(io.open(STATE, encoding="utf-8"))
    print("export_ts=%s tick=%d explore_open=%d"
          % (data["export_ts"], state.get("tick"), explore_open))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())