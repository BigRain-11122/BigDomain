"""R2230 closeout: state tick + log lines, status-export refresh,
backlog prepend, six fresh explore seeds (pool was exhausted), and the
HQ-FEEDBACK routine refresh line. Pure stdlib, ASCII source, and every
target keeps its own writer dialect (state.json CRLF, export CRLF,
markdown LF).
"""

import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
HQFB = os.path.join(ROOT, "HQ-FEEDBACK.md")

ROUND_LINE = (
    "2026-10-29 R2230 (five-silence scan clean at open: decisions.md 274"
    " rows with zero genuinely new content-addressed tokens against the"
    " stored baseline; the group ledger carries the same three"
    " @BigDomain patrol rows already paid off with zero unreplied; the"
    " group orders baseline is unchanged at the 2026-10-29 00:52"
    " fleet-event round already consumed in R2226; benchmarks refreshed"
    " 2026-10-29 inside the seven-day gate; tree clean, no index.lock)"
    " - the P1 canonical board stayed blocked-on-CEO and all four tech"
    " heads stayed gated (docker host absent, logs toolkit standing"
    " maintenance, member refunded schema product-gated, the live-mtime"
    " row waiting on a real normalized-mtime event), so this window took"
    " the debt R2229 designated as its first item: the full reconcile"
    " battery plus the four follow-up sections on the committed tree."
    " THE FIRST BATTERY RUN WAS RED (RUNNER FAIL, 2 failed assertions,"
    " 1063.7s, qa/reconcile-all-R2230.log): the reconcile-daily-census"
    " suite failed cd7-live-real-tree with exit=2 label=drift and the"
    " criteria gate read 414/415 green. The root cause was a REAL"
    " DEFECT, not the known autocrlf artefact: the R2228"
    " seller-repeat-month evidence (qa/apimarket-sellerrepeatmonths-"
    "R2228-a.log and -b.log) had been written through a shell"
    " redirection, so both files landed UTF-16LE with a BOM and the"
    " census correctly flagged them as new-dialect (class=ps-utf16)."
    " Repair: src/os/repair_evidence_R2230.py re-executes the very same"
    " suite twice and rewrites both files through ONE python writer -"
    " SUITE-A rc=0 and SUITE-B rc=0 with 8 criteria each, criterion"
    " lines identical across the two runs, SHA16 5D930765EFFC2574, 701"
    " bytes each, no BOM, CRLF=0 (nothing transcoded, no assertion"
    " relaxed) - and the census then read DRIFT-CLEAN flags=0 on the"
    " live tree. THE SECOND BATTERY RUN IS GREEN: RUNNER PASS 415/415"
    " suites, reconcile controls 7/7, expected criteria total=3443,"
    " 1001.0s, birth-site TMP RECLAIM 916/916 worlds and 321.89 MiB"
    " (qa/reconcile-all-R2230-run2.log, single-writer utf-8 LF via"
    " src/os/battery_stream.py); the four follow-up sections appended to"
    " that same file all PASS - the suite matrix was regenerated to 415"
    " suites / 3443 criteria and read back byte-identical"
    " (docs/sandbox-suite-matrix.md, 40491 bytes, green=415/415), the"
    " fingerprint chain is CLEAN over five domains, runner profile"
    " --daily --check is byte-identical PASS, and the qa writer census"
    " was re-frozen then read DRIFT-CLEAN. PRODUCT SCORE IS HONESTLY"
    " ZERO: no product code shipped this window - the window was the"
    " designated verification debt. Honest notes: (1) the follow-up"
    " runner was created by copying battery_followup_R2227.py, so its"
    " first pass appended the sections to the RED log;"
    " qa/reconcile-all-R2230.log was restored to its runner output (its"
    " last line is the RUNNER FAIL line, and the trailing 'BATTERY rc=1"
    " 1063.7s' summary line was lost in that restoration and is"
    " disclosed here rather than faked back), and the sections were then"
    " re-run into the green log; (2) the explore seed pool was down to a"
    " single stale row, so this window registered six fresh seeds with"
    " pre-registered criteria (head=api_seller_question_months,"
    " AC-SQM1..AC-SQM8) and flipped the stale R2202 row to done because"
    " api_market_question_months shipped in R2205.")

TOKENS_LINE = (
    "R2230 tokens: local=~18k api=0 api_reason=verification window - one"
    " full battery that came back red on a real evidence-dialect defect,"
    " one single-writer evidence repair, one green full battery plus the"
    " four follow-up sections, and a closeout that seeded six fresh"
    " explore rows; zero cloud calls")

HEAL_LINE = (
    "R2230 self-heal check: the BigDomain-OSLoop scheduled task exists"
    " (Running) but its principal still reads LogonType=Interactive with"
    " RunLevel=Limited, which the 2026-09-29 machine law forbids for every"
    " lane task; src/os/register_loop_task.ps1 already passes an explicit"
    " S4U principal but applying it needs an elevated shell and this"
    " session is unelevated, so the definition of the loop hosting this"
    " window was left untouched. Open local-lane item for an elevated"
    " window.")

BACKLOG_ENTRY = (
    "- [x] [done 2026-10-29 R2230] P2 verification head (the debt R2229"
    " designated as this window's first item): full reconcile battery plus"
    " the four follow-up sections on the committed tree. The first run was"
    " RED and the failure was a real defect, not an EOL artefact - the"
    " R2228 seller-repeat-month evidence had been written through a shell"
    " redirection and landed as UTF-16LE with a BOM, so the census flagged"
    " new-dialect class=ps-utf16 (suite reconcile-daily-census, criterion"
    " cd7-live-real-tree exit=2, gate 414/415). Repaired by re-executing"
    " the actual suite twice through one python writer"
    " (src/os/repair_evidence_R2230.py: rc=0/0, 8 criteria each, criterion"
    " lines identical, SHA16 5D930765EFFC2574, 701B, no BOM, CRLF=0,"
    " nothing transcoded). Second run GREEN: RUNNER PASS 415/415 suites +"
    " controls 7/7, criteria total 3443, 1001.0s, TMP RECLAIM 916/916"
    " worlds / 321.89 MiB (qa/reconcile-all-R2230-run2.log); follow-ups all"
    " PASS in the same file (matrix 415 suites / 3443 criteria"
    " byte-identical, fingerprint CLEAN 5 domains, profile --daily --check"
    " PASS, census DRIFT-CLEAN). Product score honestly zero - no product"
    " code changed. Stale explore row closed (api_market_question_months"
    " shipped R2205) and six fresh seeds registered. [done 2026-10-29"
    " R2230]")

SEEDS = [
    "- [ ] P3 explore seed (R2230 1/6, head, criteria AC-SQM1..AC-SQM8"
    " pre-registered in this row BEFORE the code): apimarket"
    " **seller monthly question pressure** (`api_seller_question_months`)"
    " - market (api_market_question_months) and category"
    " (api_category_question_months) month axes exist and the seller"
    " ANSWER axis exists (api_seller_answer_months), but no face puts one"
    " seller's INCOMING pre-sale pressure on the month axis, so a seller"
    " drowning in questions last month reads exactly like a quiet one."
    " AC-SQM1 contract: eighteen-key envelope, nine-key month rows,"
    " resident disclaimer, honest empty envelope for a prefix-valid"
    " account with no questions. AC-SQM2 booking law: a question books in"
    " the UTC month of its own asked_utc and the answering leg is"
    " credited to the ASKING month, never to the month the answer landed"
    " in. AC-SQM3 grid: contiguous first..last month with an honest zero"
    " row whose answer_rate is None, and a monotone running_question whose"
    " last value equals the envelope question_count. AC-SQM4 participants:"
    " per-month distinct buyers and listings against lifetime distinct"
    " envelope counts (row sums honestly >= envelope). AC-SQM5 peak:"
    " highest month with the earlier-month tie-break, a zero month never a"
    " peak. AC-SQM6 scope: strict seller isolation on the usr: account"
    " gate, other sellers never leak, envelope listing_count is every"
    " listing the seller owns. AC-SQM7 identity: totals equal a raw join"
    " over apimarket_questions joined to the seller's listings, and"
    " unanswered_count matches the open rows. AC-SQM8 purity: E_AM_BAD_"
    "ACCOUNT before any read for a non-prefix account, frozen table"
    " digests, constant ledger_tx set, three instances across two"
    " restarts byte-identical, wired ledger-apimarket-sellerquestionmonths"
    "(8). [open, unclaimed]",
    "- [ ] P3 explore seed (R2230 2/6): apimarket **buyer monthly answer"
    " wait** (`api_buyer_answer_wait`) - the buyer side can see its"
    " questions and its claims, but nothing tells a buyer how long it"
    " actually waited for answers month over month. Criteria prefix"
    " AC-BAW1..8 (contract, booking law on the answer month, contiguous"
    " grid with honest zero months, integer-floor mean plus fastest and"
    " slowest, backlog split, buyer isolation, cross-face identity against"
    " api_buyer_questions, purity and three-instance identity). [open,"
    " unclaimed]",
    "- [ ] P3 explore seed (R2230 3/6): apimarket **market monthly reply"
    " backlog** (`api_market_backlog_months`) - api_seller_inbox answers"
    " the present debt and api_market_question_months the arrivals, but no"
    " face shows whether the whole market's open question debt is growing"
    " or shrinking month over month. Criteria prefix AC-MBM1..8 (contract,"
    " open-at-month-end definition derived from asked_utc vs answered_utc,"
    " contiguous grid, net flow, peak with earlier-month tie-break,"
    " identity against api_market_question_months, purity, three-instance"
    " identity). [open, unclaimed]",
    "- [ ] P3 explore seed (R2230 4/6): apimarket **seller monthly rating"
    " response** (`api_seller_rating_months`) - ratings arrive on the"
    " month axis market-wide (api_market_rating_months) and per seller"
    " only as a lifetime star aggregate (api_seller_quality), so a seller"
    " cannot see whether its rating intake and star level are improving."
    " Criteria prefix AC-SRT1..8 (contract, booking law on rated_utc,"
    " contiguous grid with None on a zero month, star mean and histogram,"
    " reply-coverage column reusing the reply seam, seller isolation,"
    " cross-face identity with api_ratings, purity, three-instance"
    " identity). [open, unclaimed]",
    "- [ ] P3 explore seed (R2230 5/6): apimarket **category watch-to-buy"
    " conversion months** (`api_category_watch_conversion_months`) -"
    " api_watch_conversion answers one listing's conversion and"
    " api_category_watch_months the watch volume, but no face answers"
    " whether a category's watchers actually convert, month over month."
    " Criteria prefix AC-CWC1..8 (contract, cohort law on the watch month,"
    " conversion and cancellation legs, contiguous grid with None rate on"
    " a zero month, category seam through the effective bucket, market"
    " benchmark column, identity against api_category_watch_months,"
    " purity, three-instance identity). [open, unclaimed]",
    "- [ ] P3 explore seed (R2230 6/6): apimarket **seller price response"
    " to demand** (`api_seller_price_demand_months`) - price cadence"
    " (api_seller_price_cadence_months) and demand signals (watch and"
    " question month rows) both exist, but nobody joins them, so a seller"
    " cannot see whether it reprices when interest rises. Criteria prefix"
    " AC-SPD1..8 (contract, month join law on the same UTC month, revision"
    " count against watch delta with a None correlation on a flat month,"
    " contiguous grid, seller isolation, market benchmark row, identity"
    " against both source faces, purity, three-instance identity). [open,"
    " unclaimed]",
]

HQFB_LINE = (
    "- (2026-10-29 R2230, P2 routine refresh + defect notice, non-urgent)"
    " **P0/P1 to CEO unchanged**: platform name verdict, server,"
    " domain/ICP filing, WeChat Pay merchant id and the account-domain"
    " msgSecCheck are still zero-arrived, so bootstrap and the chargeable"
    " front desk stay parked behind them per discipline, zero chasing."
    " **Defect found and closed this window**: the R2228 evidence files"
    " had been written through a shell redirection, landing as UTF-16LE"
    " with a BOM; the qa writer census caught it on the live tree, both"
    " files were regenerated from a fresh double run through one python"
    " writer (no transcoding, no criterion relaxed), and the full battery"
    " then came back green (415/415 suites, criteria total 3443, 1001.0s)"
    " with matrix, fingerprint, profile and census follow-ups all PASS."
    " **Cross-company note**: any lane whose evidence is captured by shell"
    " redirection will produce exactly this defect and trip its own census"
    " gate - capturing child stdout in-process (subprocess PIPE plus one"
    " binary writer) is the safe shape. Delivery = this line + the R2230"
    " state log row + the R2230 commit message.")


def write_state():
    with io.open(STATE, encoding="utf-8", newline="") as handle:
        d = json.load(handle)
    d["tick"] = 2230
    for line in (ROUND_LINE, TOKENS_LINE, HEAL_LINE):
        d["log"].append(line)
    body = json.dumps(d, indent=2, ensure_ascii=False)
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(body.replace("\n", "\r\n") + "\r\n")
    return len(d["log"])


def write_export():
    with io.open(EXPORT, encoding="utf-8", newline="") as handle:
        d = json.load(handle)
    hits = 0
    for row in d["results"]:
        if isinstance(row, list) and len(row) >= 2 and "tick" in str(row[1]):
            row[0] = "2230"
            hits += 1
    d["outs"].insert(0, [
        "verification debt closed + evidence defect fixed (R2230)",
        "on",
        "full battery green on the repaired tree: RUNNER PASS 415/415"
        " suites + controls 7/7, criteria total 3443 in 1001.0s; the first"
        " run was red because the R2228 evidence files were UTF-16LE from a"
        " shell redirection, regenerated via one python writer (SHA16"
        " 5D930765EFFC2574, 701B each, CRLF=0); matrix 415/3443"
        " byte-identical, fingerprint CLEAN, profile PASS, census"
        " DRIFT-CLEAN"])
    d["results"].insert(0, [
        "R2230",
        "P2 verification debt (the item R2229 designated first): full"
        " reconcile battery plus four follow-up sections on the committed"
        " tree. First run RED - the census suite cd7-live-real-tree flagged"
        " new-dialect ps-utf16 on the two R2228 evidence files, a real"
        " defect from a shell redirection (UTF-16LE + BOM), not the"
        " autocrlf artefact. Repaired by re-executing the actual suite"
        " twice through one python writer (rc=0/0, 8 criteria, identical"
        " criterion lines, SHA16 5D930765EFFC2574, 701B, no BOM, CRLF=0,"
        " nothing transcoded, no assertion relaxed); census then"
        " DRIFT-CLEAN flags=0. Second run GREEN: RUNNER PASS 415/415"
        " suites, controls 7/7, criteria total 3443, 1001.0s, TMP RECLAIM"
        " 916/916 worlds / 321.89 MiB; follow-ups appended to the same"
        " evidence log all PASS (matrix 415 suites / 3443 criteria"
        " byte-identical, fingerprint CLEAN 5 domains, runner profile"
        " --daily --check PASS, census re-frozen then DRIFT-CLEAN). Product"
        " score honestly zero - no product code shipped. Explore pool was"
        " exhausted, so six fresh seeds were registered with pre-registered"
        " criteria (head api_seller_question_months AC-SQM1..AC-SQM8) and"
        " the stale R2202 row was closed. Honest notes: the follow-up"
        " runner's first pass appended to the red log by a copy slip (that"
        " file was restored to its runner output and the trailing BATTERY"
        " summary line is disclosed in the state log instead of faked"
        " back); the loop task still needs an elevated S4U re-registration."])
    sd = d["self_drive"]
    sd["log_lines_in_window"] = 21
    sd["substantive_non_idle_mention_lines"] = 21
    sd["queue_explore_open"] = 6
    body = json.dumps(d, indent=2, ensure_ascii=False)
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    with io.open(EXPORT, "w", encoding="utf-8", newline="") as handle:
        handle.write(body.replace("\n", "\r\n") + "\r\n")
    return hits


def write_backlog():
    with io.open(BACKLOG, encoding="utf-8", newline="") as handle:
        body = handle.read()
    entry = BACKLOG_ENTRY
    if "\n" not in body[:2]:
        entry = entry  # markdown is LF per the file's own dialect
    with io.open(BACKLOG, "w", encoding="utf-8", newline="") as handle:
        handle.write(entry + "\n" + body)


def write_explore():
    with io.open(EXPLORE, encoding="utf-8", newline="") as handle:
        lines = handle.read().split("\n")
    flipped = 0
    marker = (" [done 2026-10-29 R2230: delivered as"
              " api_market_question_months in R2205; only the stale marker"
              " was missing, zero product change]")
    for i, line in enumerate(lines):
        if ("P3 explore seed" in line and "R2202" in line
                and "api_market_question_months" in line
                and "CLAIMED" not in line and "done 2026" not in line):
            lines[i] = line.rstrip() + marker
            flipped += 1
            break
    body = "\n".join(lines)
    if not body.endswith("\n"):
        body += "\n"
    body += "\n".join(SEEDS) + "\n"
    with io.open(EXPLORE, "w", encoding="utf-8", newline="") as handle:
        handle.write(body)
    return flipped


def write_hqfb():
    with io.open(HQFB, encoding="utf-8", newline="") as handle:
        body = handle.read()
    if not body.endswith("\n"):
        body += "\n"
    with io.open(HQFB, "w", encoding="utf-8", newline="") as handle:
        handle.write(body + HQFB_LINE + "\n")


def main():
    n = write_state()
    hits = write_export()
    write_backlog()
    flipped = write_explore()
    write_hqfb()
    print("state log lines=%d; export tick rows=%d; explore flipped=%d,"
          " seeds=6" % (n, hits, flipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())