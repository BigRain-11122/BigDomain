"""R2233 closeout: state tick + log lines, status-export refresh (the
CEO face is read from closeout_payload_R2233.json so this source stays
ASCII), backlog prepend, and one tech-queue seed for the forward
retry-naming convention. Every target keeps its own writer dialect
(state.json CRLF, export CRLF, markdown LF).
"""

import datetime
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")
PAYLOAD = os.path.join(ROOT, "src", "os", "closeout_payload_R2233.json")

ROUND_LINE = (
    "2026-10-29 R2233 (five-silence scan clean at open: decisions.md 274"
    " non-empty rows against the stored baseline, zero new"
    " content-addressed tokens and zero domain action; the group ledger"
    " carries the same three @BigDomain patrol rows already paid off with"
    " zero unreplied; the own-orders baseline stays at the 2026-10-29"
    " 01:3x fleet-event round already consumed in R2232; benchmarks"
    " refreshed 2026-10-29 inside the seven-day gate; tree clean, no"
    " index.lock) - the P1 canonical rows stayed blocked-on-CEO and all"
    " four tech heads stayed gated, so this window took the debt R2232"
    " designated as its first item: the full reconcile battery plus the"
    " suite-matrix regeneration on the committed tree, with the state"
    " fold checked rather than assumed (state.json measures 67142B,"
    " below the 78500B waterline, so no fold was due - recorded instead"
    " of performed). THE FIRST BATTERY RUN WAS RED: RUNNER FAIL, 3 failed"
    " assertions, 1021.7s, qa/reconcile-all-R2233.log, 415/417 suites"
    " green with expected criteria total=3459. Both reds were REAL"
    " evidence-hygiene defects, not EOL noise and not product logic."
    " (1) reconcile-daily-census / cd7-live-real-tree exited 2 with"
    " label=drift because qa/apimarket-sellerquestionmonths-R2231-a.log"
    " and -b.log had been captured through a PowerShell pipe: both read"
    " 763B with 10 CRLF and 0 LF, so the writer census correctly flagged"
    " new-dialect class=pwsh-capture. Repair: src/os/evidence_normalize_"
    "R2233.py rewrites both legs through the canonical writer"
    " (run_identity.normalize: no BOM, CRLF->LF, one trailing newline)"
    " with the payload text untouched - 763->753 bytes each, CRLF=0, both"
    " legs byte-identical at sha16 2207807e14fc2f88 - and the census then"
    " read DRIFT-CLEAN flags=0. (2) os-run-identity / AC-RID8 failed the"
    " live audit with new=1: the pair reconcile-all-R2230.log vs"
    " reconcile-all-R2230-run2.log. That stem is a BATTERY log, not one"
    " suite's double run - the primary leg is the RED first attempt and"
    " the run2 leg is the post-fix rerun (RUNNER PASS 415/415), so the"
    " files legitimately differ by 44 lines and 2139 bytes; the"
    " E_FALSE_BYTE_CLAIM class is raised by the 420/421 per-suite"
    " sentences inside the bodies, which describe those suites' own a/b"
    " legs and never this pair. Disclosed in state/run_identity_baseline."
    "json the same way R2153 disclosed the R2100 pair (a baselined class"
    " never masks another class in the same pair), because a battery log"
    " cannot be reproduced to the same bytes; the forward convention"
    " recorded here and queued is that a correction rerun is named -retry"
    " so it is never read as a pair suffix. THE SECOND BATTERY RUN ON THE"
    " COMMITTED FIX TREE (HEAD cdbddf30) IS GREEN: RUNNER PASS 417/417"
    " suites, reconcile controls 7/7, 1023.4s, birth-site TMP RECLAIM"
    " 920/920 worlds and 323.06 MiB (qa/reconcile-all-R2233.log,"
    " single-writer utf-8 LF via src/os/battery_stream.py); the four"
    " follow-up sections in src/os/battery_followup_R2233.py all PASS -"
    " the suite matrix was regenerated to 417 suites / 3459 criteria and"
    " read back (docs/sandbox-suite-matrix.md, 40690 bytes,"
    " green=417/417), the fingerprint chain is CLEAN over five domains,"
    " runner profile --daily --check PASS, and the writer census was"
    " re-frozen then read DRIFT-CLEAN. PRODUCT SCORE IS HONESTLY ZERO:"
    " no product code shipped - this was the designated verification"
    " debt. Honest notes: the first battery invocation was cancelled by"
    " the five-minute no-output rule because its output was piped through"
    " Out-String; the ownership check found no surviving python child and"
    " no partial evidence file, so nothing was lost before the direct"
    " re-run, exactly the R2211 precedent; the four claimable explore"
    " seeds (R2230 3/6..6/6) stay open for the next windows.")

TOKENS_LINE = (
    "R2233 tokens: local=~22k api=0 api_reason=verification window - one"
    " full battery that came back red on two real evidence-hygiene"
    " defects, one single-writer normalisation of a CRLF evidence pair,"
    " one disclosed baseline entry for a battery-log pair, one green full"
    " battery on the committed fix tree plus the four follow-up sections,"
    " and a closeout that queued the forward retry-naming convention;"
    " zero cloud calls")

HEAL_LINE = (
    "R2233 self-heal check: the BigDomain-OSLoop scheduled task exists"
    " (Running) but its principal still reads LogonType=Interactive with"
    " RunLevel=Limited, which the 2026-09-29 machine law forbids for every"
    " lane task; src/os/register_loop_task.ps1 already passes an explicit"
    " S4U principal but applying it needs an elevated shell and this"
    " session is unelevated, so the definition of the loop hosting this"
    " window was left untouched. Open local-lane item for an elevated"
    " window (third consecutive disclosure).")

BACKLOG_ENTRY = (
    "- [x] [done 2026-10-29 R2233] P2 verification head (the debt R2232"
    " designated as this window's first item): full reconcile battery plus"
    " suite-matrix regeneration on the committed tree, with the state fold"
    " measured rather than assumed (67142B < 78500B waterline, no fold"
    " due). First run RED: RUNNER FAIL, 3 failed assertions, 1021.7s,"
    " 415/417 suites (qa/reconcile-all-R2233.log). Both reds were real"
    " evidence-hygiene defects. (1) reconcile-daily-census cd7-live-real-"
    "tree exit=2 label=drift: the two R2231 seller-question evidence legs"
    " were PowerShell-pipe captures (763B, 10 CRLF, 0 LF) so the census"
    " flagged class=pwsh-capture; repaired by src/os/evidence_normalize_"
    "R2233.py rewriting both through run_identity.normalize (763->753B,"
    " CRLF=0, payload untouched, both legs sha16 2207807e14fc2f88), census"
    " then DRIFT-CLEAN. (2) os-run-identity AC-RID8 live audit new=1: the"
    " battery pair reconcile-all-R2230.log vs -run2.log is a RED attempt"
    " and its post-fix rerun (44 lines / 2139 bytes apart), and the"
    " E_FALSE_BYTE_CLAIM class comes from the 420/421 per-suite"
    " 'byte-identical' sentences inside the bodies, not from the file"
    " pair; disclosed in state/run_identity_baseline.json under the R2153"
    " convention, and the forward rule (a correction rerun is named"
    " -retry, never a pair suffix) queued in state/queue/tech.md. Second"
    " run on the committed fix tree HEAD cdbddf30 GREEN: RUNNER PASS"
    " 417/417 suites + controls 7/7, 1023.4s, TMP RECLAIM 920/920 worlds /"
    " 323.06 MiB; the four follow-up sections all PASS in the same log"
    " (matrix regenerated 417 suites / 3459 criteria, 40690 bytes,"
    " green=417/417; fingerprint CLEAN 5 domains; profile --daily --check"
    " PASS; census re-frozen then DRIFT-CLEAN). Product score honestly"
    " zero - no product code shipped. [done 2026-10-29 R2233]")

TECH_SEED = (
    "- [ ] P2 tech seed (R2233): **retry-naming convention as a gate "
    "rule**. Born from the R2233 red: the R2230 battery stored its "
    "post-fix rerun as `reconcile-all-R2230-run2.log`, and AC-RID6 reads "
    "the `-run2` suffix as the second leg of a double-run byte-identity "
    "pair, so 420 suite-internal 'byte-identical' sentences in the body "
    " were read as a file-pair claim (E_FALSE_BYTE_CLAIM, disclosed into "
    "state/run_identity_baseline.json this window). Gap: a correction "
    "rerun and an identity pair are different things that share one "
    "suffix. Criteria prefix AC-RTN1..AC-RTN6 (contract; the writer/naming "
    "helper emits `-retry` for any rerun of an evidence stem that already "
    " exists and whose RUNNER verdict differs, and refuses `-run2`/`-2` "
    " for that case; the identity auditor never pairs a `-retry` leg; a "
    "fixture pair that genuinely claims byte identity still turns red; "
    "the live baseline stops growing by construction for this class, so "
    "the R2153/R2233 disclosures stay as history rather than precedent; "
    "purity and wiring into reconcile_all). [open, unclaimed]")


def write_state():
    with io.open(STATE, encoding="utf-8", newline="") as handle:
        d = json.load(handle)
    d["tick"] = 2233
    for line in (ROUND_LINE, TOKENS_LINE, HEAL_LINE):
        d["log"].append(line)
    body = json.dumps(d, indent=2, ensure_ascii=False)
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(body.replace("\n", "\r\n") + "\r\n")
    return len(d["log"])


def count_open(path):
    with io.open(path, encoding="utf-8", newline="") as handle:
        return sum(1 for line in handle.read().split("\n")
                   if line.startswith("- [ ]"))


def write_export():
    with io.open(EXPORT, encoding="utf-8", newline="") as handle:
        d = json.load(handle)
    with io.open(PAYLOAD, encoding="utf-8") as handle:
        face = json.load(handle)
    hits = 0
    for row in d["results"]:
        if isinstance(row, list) and len(row) >= 2 and "tick" in str(row[1]):
            row[0] = "2233"
            hits += 1
    d["export_ts"] = datetime.datetime.now().replace(
        microsecond=0).isoformat() + "+08:00"
    d["do"] = face["do"]
    d["ceo_face"] = {
        "current": face["current"],
        "latest_artifact": face["latest_artifact"],
        "next_milestone": face["next_milestone"],
    }
    d["outs"].insert(0, [
        "verification debt closed on a green battery (R2233)",
        "on",
        "full battery on the committed fix tree: RUNNER PASS 417/417"
        " suites + controls 7/7 in 1023.4s; the first run was red on two"
        " real evidence-hygiene defects (R2231 logs captured in a"
        " PowerShell pipe as CRLF, normalised to utf-8 LF at sha16"
        " 2207807e14fc2f88; the R2230 battery pair disclosed in the"
        " identity baseline under the R2153 convention); matrix 417"
        " suites / 3459 criteria, fingerprint CLEAN, profile PASS,"
        " census DRIFT-CLEAN"])
    d["results"].insert(0, [
        "R2233",
        "P2 verification debt (the item R2232 designated first): full"
        " reconcile battery plus matrix regeneration on the committed"
        " tree, with the state fold measured (67142B < 78500B waterline,"
        " not due). First run RED: RUNNER FAIL, 3 failed assertions,"
        " 1021.7s, 415/417. Two real defects: (1) the two R2231"
        " seller-question evidence legs were PowerShell captures (763B,"
        " 10 CRLF, 0 LF) so the census flagged pwsh-capture; normalised"
        " through one python writer to utf-8 LF, payload untouched, both"
        " legs sha16 2207807e14fc2f88, census then DRIFT-CLEAN; (2) the"
        " battery pair reconcile-all-R2230.log/-run2.log raised"
        " E_FALSE_BYTE_CLAIM because the suffix means a pair while the"
        " file is a RED-then-rerun pair (44 lines / 2139 bytes apart,"
        " the class raised by 420/421 suite-internal sentences);"
        " disclosed in state/run_identity_baseline.json under the R2153"
        " convention and the forward -retry naming rule queued. Second"
        " run on the committed fix tree HEAD cdbddf30 GREEN: RUNNER PASS"
        " 417/417 + controls 7/7, 1023.4s, TMP RECLAIM 920/920 worlds /"
        " 323.06 MiB; follow-ups all PASS (matrix 417 suites / 3459"
        " criteria in 40690 bytes green=417/417, fingerprint CLEAN 5"
        " domains, profile PASS, census DRIFT-CLEAN). Product score"
        " honestly zero - no product code shipped."])
    sd = d["self_drive"]
    sd["log_lines_in_window"] = 3
    sd["substantive_non_idle_mention_lines"] = 3
    sd["queue_explore_open"] = count_open(
        os.path.join(ROOT, "state", "queue", "explore.md"))
    body = json.dumps(d, indent=2, ensure_ascii=False)
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    with io.open(EXPORT, "w", encoding="utf-8", newline="") as handle:
        handle.write(body.replace("\n", "\r\n") + "\r\n")
    return hits


def write_backlog():
    with io.open(BACKLOG, encoding="utf-8", newline="") as handle:
        body = handle.read()
    with io.open(BACKLOG, "w", encoding="utf-8", newline="") as handle:
        handle.write(BACKLOG_ENTRY + "\n" + body)


def write_tech():
    with io.open(TECH, encoding="utf-8", newline="") as handle:
        body = handle.read()
    if not body.endswith("\n"):
        body += "\n"
    with io.open(TECH, "w", encoding="utf-8", newline="") as handle:
        handle.write(body + TECH_SEED + "\n")


def main():
    n = write_state()
    hits = write_export()
    write_backlog()
    write_tech()
    print("state log lines=%d; export tick rows=%d; tech seed queued"
          % (n, hits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())