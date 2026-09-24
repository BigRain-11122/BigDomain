"""Acceptance suite for the UGC pipeline sandbox (BigDomain P-47-3b).

Asserts the pre-registered criteria AC-U1..AC-U12 from
docs/spec/ugc-pipeline-spec.md section 1. Each criterion prints
PASS/FAIL with evidence; the process exits non-zero on any FAIL.

Chinese probe strings are sourced from config.json (data file) per the
encoding discipline; the only non-ASCII literals here are unicode
escapes for the emoji noise sample.

Usage: python test_ugc.py
"""

import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.normpath(os.path.join(BASE, "..", "ledger")))

import pipeline as P  # noqa: E402
import store as UGC  # noqa: E402
from sec_gate import GateOfflineError  # noqa: E402 (lobby gate product)
import ledger as LED  # noqa: E402 (cross-piece check, AC-U10)

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_error(fn, *codes):
    try:
        fn()
    except (UGC.PipelineError, GateOfflineError) as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def expect_ledger_error(fn, *codes):
    """Cross-piece assertions (AC-U10) raise the ledger's own family."""
    try:
        fn()
    except LED.LedgerError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def raw_aborts(db_path, sql, args, want):
    conn = sqlite3.connect(db_path, isolation_level=None)
    ok, detail = False, "no-abort"
    try:
        conn.execute(sql, args)
    except sqlite3.IntegrityError as exc:
        ok, detail = want in str(exc), str(exc)
    finally:
        conn.close()
    return ok, detail


def load_lobby_store():
    path = os.path.normpath(os.path.join(BASE, "..", "lobby", "store.py"))
    spec = importlib.util.spec_from_file_location("lobby_store_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def inside_repo(path):
    real = os.path.realpath(path)
    try:
        return os.path.commonpath([P.REPO_ROOT, real]) == P.REPO_ROOT
    except ValueError:
        return False


def main():
    tmp = tempfile.mkdtemp(prefix="ugc-ac-")
    with open(os.path.join(BASE, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    # suite headroom: flood triage raised for shared actors (the flood rule
    # itself is proven on a dedicated instance below, AC-U5); test exports
    # land in a repo-local dir that this suite removes at the end
    cfg["noise"] = dict(cfg.get("noise") or {}, flood_max_submissions=50)
    cfg["export"] = dict(cfg.get("export") or {}, dir="export-ac-test")
    db = os.path.join(tmp, "ugc.db")
    export_test_dir = os.path.join(BASE, "export-ac-test")

    lobby = load_lobby_store()
    ls = lobby.EventStore(db)
    fw = cfg["gate"]["forbidden_words"][0]
    ab = cfg["gate"]["advisory_ban_words"][0]
    gw = cfg["gate"]["gray_words"][0]
    rules = cfg["routing"]["rules"]
    lk = cfg["approval"]["landfall_keywords"][0]

    # initial lobby batch: one clean idea (lobby_idea face), one avatar
    # intake (public face), one advisory word upstream row (ingest re-gate)
    idea_text = "lobby idea about " + cfg["routing"]["rules"][1]["keywords"][0]
    ls.append(lobby.utc_now_iso(), "idea.submit", "C-10010", "cocreate", idea_text,
              payload={"text": idea_text, "pool": "proposal-queue-stub"})
    av_content = "quiet reader wants to help"
    ls.append(lobby.utc_now_iso(), "avatar.intake", "anon-pub1", "intake",
              "avatar intake row",
              payload={"name": "av-pub", "intro": av_content,
                       "queue": "biglife-t04-reference"})
    adv_text = "advisory ingest probe " + ab
    adv_actor = "C-10009"
    ls.append(lobby.utc_now_iso(), "idea.submit", adv_actor, "cocreate", adv_text,
              payload={"text": adv_text, "pool": "proposal-queue-stub"})

    pipe = P.UGCPipeline(cfg, db)
    try:
        return run_suite(pipe, cfg, db, tmp, lobby, ls, fw, ab, gw, rules, lk,
                         adv_actor, adv_text)
    finally:
        pipe.close()
        ls.close()
        if os.path.isdir(export_test_dir):
            shutil.rmtree(export_test_dir, ignore_errors=True)


def run_suite(pipe, cfg, db, tmp, lobby, ls, fw, ab, gw, rules, lk, adv_actor, adv_text):
    a1 = "C-10001"
    kw0 = rules[0]["keywords"][0]

    # ---- AC-U2: startup self-check + wordlist mock -------------------------
    refusals = []
    for label, mutate in (
        ("no-gate-section", lambda c: c.__setitem__("gate", None)),
        ("empty-forbidden", lambda c: c["gate"].__setitem__("forbidden_words", [])),
        ("no-gray-words", lambda c: c["gate"].pop("gray_words")),
        ("no-disclaimer", lambda c: c["compliance"].__setitem__("disclaimer", "")),
        ("escape-export", lambda c: c.__setitem__(
            "export", {"dir": os.path.join(tempfile.gettempdir(), "esc")})),
    ):
        bad = json.loads(json.dumps(cfg))
        mutate(bad)
        ok = False
        try:
            P.UGCPipeline(bad, os.path.join(tmp, "bad-%s.db" % label))
        except GateOfflineError:
            ok = True
        refusals.append("%s=%s" % (label, ok))
    ok_all_refuse = all(r.endswith("=True") for r in refusals)
    bad_path = os.path.join(tmp, "bad-config.json")
    with open(bad_path, "w", encoding="utf-8") as handle:
        json.dump(json.loads(json.dumps(cfg)), handle)
    del_cfg = json.loads(json.dumps(cfg))
    del_cfg["gate"] = None
    with open(bad_path, "w", encoding="utf-8") as handle:
        json.dump(del_cfg, handle, ensure_ascii=False)
    proc = subprocess.run(
        [sys.executable, os.path.join(BASE, "pipeline.py"), "--config", bad_path,
         "--db", os.path.join(tmp, "cli.db")],
        capture_output=True, text=True, encoding="utf-8", timeout=60)
    cli_refused = proc.returncode == 2 and "E_GATE_OFFLINE" in (proc.stderr or "")
    proc_ok = subprocess.run(
        [sys.executable, os.path.join(BASE, "pipeline.py"),
         "--db", os.path.join(tmp, "cli-ok.db")],
        capture_output=True, text=True, encoding="utf-8", timeout=60)
    cli_ready = proc_ok.returncode == 0 and "ugc pipeline ready" in (proc_ok.stdout or "")
    ok_fw, code_fw = expect_error(
        lambda: pipe.submit("avatar_intake", "A-gate", "forbidden probe " + fw),
        UGC.E_CONTENT_REJECTED)
    ok_ab_word, code_ab = expect_error(
        lambda: pipe.submit("avatar_intake", "A-gate", "advisory probe " + ab),
        UGC.E_CONTENT_REJECTED)
    nothing_landed = pipe.store.events_count() == 0
    record("AC-U2", ok_all_refuse and cli_refused and cli_ready and ok_fw
           and ok_ab_word and nothing_landed,
           "serve-refusals %s; cli rc2-with-E_GATE_OFFLINE=%s cli-ready=%s;"
           " gate1-hit=%s(%s) gate2-hit=%s(%s) gate-hits-landed-rows=%d"
           % (",".join(refusals), cli_refused, cli_ready, ok_fw, code_fw,
              ok_ab_word, code_ab, pipe.store.events_count()))

    # ---- AC-U1: multi-entry intake, entrance, rate limit -------------------
    pipe.grant_entrance_sandbox(a1)
    r_direct = pipe.submit("direct", a1, "plaza idea about " + kw0)
    ok_direct = (r_direct["received"] and r_direct["pooled"]
                 and r_direct["line"] == rules[0]["line"] and r_direct["evt_id"])
    ok_noent, code_noent = expect_error(
        lambda: pipe.submit("direct", "C-10002", "clean idea text"),
        UGC.E_ENTRANCE_REQUIRED)
    ok_dan, code_dan = expect_error(
        lambda: pipe.submit("live_danmaku", a1, "danmaku probe"),
        UGC.E_SOURCE_BLOCKED)
    ok_bad_src, code_bad_src = expect_error(
        lambda: pipe.submit("telegram", a1, "x"), UGC.E_BAD_SOURCE)
    ok_empty, code_empty = expect_error(
        lambda: pipe.submit("direct", a1, "   "), UGC.E_BAD_FRAME)
    r_pub = pipe.submit("avatar_intake", "anon-pub2", "avatar intro: quiet reader")
    ok_pub = r_pub["received"] and r_pub["pooled"]  # spectator face accepted
    a2 = "C-10003"
    pipe.grant_entrance_sandbox(a2)
    for i in range(pipe.rate_max):
        pipe.submit("direct", a2, "rate probe %02d" % i)
    ok_rate, code_rate = expect_error(
        lambda: pipe.submit("direct", a2, "rate probe overflow"), UGC.E_RATE_LIMIT)
    receipts = pipe.ingest_lobby()
    ok_receipts = all(r.get("evt_id") or r.get("code") for r in receipts)
    r_idea = next(r for r in receipts if r.get("pooled") and r.get("line"))
    idea_evt = r_idea["evt_id"]
    ok_lobby_src = (pipe.store.event_row(idea_evt)["zone"] == "lobby_idea"
                    and r_idea["line"] == rules[1]["line"])
    r_av = next(r for r in receipts
                if r.get("evt_id") and r["evt_id"] != idea_evt and r.get("pooled"))
    ok_av_src = pipe.store.event_row(r_av["evt_id"])["zone"] == "avatar_intake"
    record("AC-U1", ok_direct and ok_noent and ok_dan and ok_bad_src and ok_empty
           and ok_pub and ok_rate and ok_receipts and ok_lobby_src and ok_av_src,
           "direct=%s entrance-neg=%s(%s) danmaku-reserved=%s(%s) unknown-src=%s(%s)"
           " empty=%s(%s) public-intake=%s rate-6th=%s(%s) ingest-lobby_idea=%s"
           " ingest-avatar=%s receipts-carry-evt_id=%s"
           % (ok_direct, ok_noent, code_noent, ok_dan, code_dan, ok_bad_src,
              code_bad_src, ok_empty, code_empty, ok_pub, ok_rate, code_rate,
              ok_lobby_src, ok_av_src, ok_receipts))

    # ---- AC-U8: advisory gate on every entry + resident disclaimer ---------
    a8 = "C-10008"
    pipe.grant_entrance_sandbox(a8)
    ok_adv_direct, code_adv = expect_error(
        lambda: pipe.submit("direct", a8, "promise " + ab), UGC.E_CONTENT_REJECTED)
    ok_adv_pub, _ = expect_error(
        lambda: pipe.submit("avatar_intake", "anon-pub3", "promise " + ab),
        UGC.E_CONTENT_REJECTED)
    adv_receipt = next(r for r in receipts if r.get("code") == UGC.E_CONTENT_REJECTED)
    adv_evt = P.compute_evt_id("lobby_idea", adv_actor, adv_text)
    ok_adv_ingest = (adv_receipt.get("origin_evt_id") is not None
                     and pipe.store.event_row(adv_evt) is None)
    pq = pipe.pool_query()
    cq = pipe.chronicle_query()
    disc = cfg["compliance"]["disclaimer"]
    ok_disc = (pq.get("disclaimer") == disc and pq.get("persistent") is True
               and cq.get("disclaimer") == disc and bool(disc))
    record("AC-U8", ok_adv_direct and ok_adv_pub and ok_adv_ingest and ok_disc,
           "gate2 direct=%s(%s) public-face=%s ingest-rejected-no-land=%s;"
           " pool+chronicle disclaimer-resident=%s persistent=%s len=%d"
           % (ok_adv_direct, code_adv, ok_adv_pub, ok_adv_ingest, ok_disc,
              pq.get("persistent") is True, len(disc)))

    # ---- AC-U3: gray-zone review desk --------------------------------------
    a3 = "C-10005"
    pipe.grant_entrance_sandbox(a3)
    r_gray = pipe.submit("direct", a3, "gray idea about " + gw)
    ok_susp = (r_gray["suspended"] and r_gray["gate"] == "review"
               and pipe.store.item_row(r_gray["evt_id"]) is None)
    qrow = pipe.store.review_row(r_gray["evt_id"])
    ok_pending = qrow["verdict"] is None and qrow["reviewer"] is None
    ok_not_pooled = r_gray["evt_id"] not in [
        i["evt_id"] for i in pipe.pool_query()["items"]]
    r_pass = pipe.review_verdict(r_gray["evt_id"], "pass", "rev-1")
    qrow = pipe.store.review_row(r_gray["evt_id"])
    ok_pass = (r_pass["pooled"] and pipe.store.item_row(r_gray["evt_id"])["state"] == "pooled"
               and qrow["verdict"] == "pass" and qrow["reviewer"] == "rev-1")
    ok_vdone, code_vdone = expect_error(
        lambda: pipe.review_verdict(r_gray["evt_id"], "pass", "rev-1b"),
        UGC.E_REVIEW_DONE)
    r_gray2 = pipe.submit("direct", a3, "gray idea two about " + gw + " again")
    ok_risky, code_risky = expect_error(
        lambda: pipe.review_verdict(r_gray2["evt_id"], "risky", "rev-2"),
        UGC.E_CONTENT_REJECTED)
    qrow2 = pipe.store.review_row(r_gray2["evt_id"])
    ok_trace = qrow2["verdict"] == "risky" and qrow2["reviewer"] == "rev-2"
    ok_risky_not_pooled = pipe.store.item_row(r_gray2["evt_id"]) is None
    ok_bad_verdict, _ = expect_error(
        lambda: pipe.review_verdict(r_gray2["evt_id"], "maybe", "rev-3"),
        UGC.E_BAD_VERDICT)
    ok_unknown, _ = expect_error(
        lambda: pipe.review_verdict("evt-nonexistent", "pass", "x"), UGC.E_NOT_FOUND)
    r_gray3 = pipe.submit("direct", a3, "gray idea three about " + gw + " and more")
    ok_forever = (pipe.desk.is_suspended(r_gray3["evt_id"])
                  and r_gray3["evt_id"] not in [
                      i["evt_id"] for i in pipe.pool_query()["items"]])
    record("AC-U3", ok_susp and ok_pending and ok_not_pooled and ok_pass
           and ok_vdone and ok_risky and ok_trace and ok_risky_not_pooled
           and ok_bad_verdict and ok_unknown and ok_forever,
           "suspended=%s no-verdict-NULL=%s not-pooled=%s pass-enters-flow=%s"
           " double-verdict=%s(%s) risky-rejects=%s(%s) trace-kept=%s"
           " risky-never-pooled=%s bad-verdict=%s unknown-case=%s"
           " no-verdict-suspended-forever=%s"
           % (ok_susp, ok_pending, ok_not_pooled, ok_pass, ok_vdone, code_vdone,
              ok_risky, code_risky, ok_trace, ok_risky_not_pooled, ok_bad_verdict,
              ok_unknown, ok_forever))

    # ---- AC-U4: config-driven routing ---------------------------------------
    lines_seen = {}
    evt0 = None
    for idx, rule in enumerate(rules):
        r = pipe.submit("avatar_intake", "C-r%d" % idx,
                        "idea number %d about %s" % (idx, rule["keywords"][0]))
        lines_seen[rule["line"]] = (r["line"] == rule["line"] and r["pooled"])
        if idx == 0:
            evt0 = r["evt_id"]
    ok_six = all(lines_seen.values()) and len(lines_seen) == len(rules)
    r_unsorted = pipe.submit("avatar_intake", "C-unsorted",
                             "totally unmatched idea text here")
    ok_unsorted = r_unsorted["line"] == cfg["routing"]["default_line"]
    moved_line = rules[1]["line"]
    pipe.config["routing"]["rules"] = [
        {"line": moved_line, "keywords": [rules[0]["keywords"][0]]}]
    rr = pipe.re_route(evt0)
    pipe.config["routing"]["rules"] = rules
    ok_reroute = rr["line"] == moved_line and rr["was"] == rules[0]["line"]
    record("AC-U4", ok_six and ok_unsorted and ok_reroute,
           "six-lines-routed=%s unsorted-fallback=%s config-reroute=%s (%s->%s"
           " code-untouched)" % (ok_six, ok_unsorted, ok_reroute,
                                 rr["was"], rr["line"]))

    # ---- AC-U5: noise triage (kept rows, never pooled) ----------------------
    emoji = "\U0001F44D\U0001F44D\U0001F44D"
    r_emoji = pipe.submit("avatar_intake", "C-n1", emoji)
    r_short = pipe.submit("avatar_intake", "C-n2", "hi")
    ok_noise = (r_emoji["noise"] and not r_emoji["pooled"]
                and r_short["noise"] and not r_short["pooled"])
    ok_rows_kept = (pipe.store.event_row(r_emoji["evt_id"]) is not None
                    and pipe.store.event_row(r_short["evt_id"]) is not None)
    ok_no_items = (pipe.store.item_row(r_emoji["evt_id"]) is None
                   and pipe.store.item_row(r_short["evt_id"]) is None)
    ok_no_draft = pipe.store.draft_row(r_emoji["evt_id"]) is None
    # flood rule on a dedicated instance: 6 ingests, 5 accepted, 6th = noise
    flood_cfg = json.loads(json.dumps(cfg))
    flood_cfg["noise"]["flood_max_submissions"] = 5
    flood_db = os.path.join(tmp, "flood.db")
    ls2 = lobby.EventStore(flood_db)
    for i in range(6):
        ls2.append(lobby.utc_now_iso(), "avatar.intake", "F1-anon", "intake",
                   "avatar intake row",
                   payload={"name": "av%d" % i, "intro": "flood probe %02d" % i,
                            "queue": "biglife-t04-reference"})
    flood_pipe = P.UGCPipeline(flood_cfg, flood_db)
    frecs = flood_pipe.ingest_lobby()
    pooled_n = sum(1 for r in frecs if r.get("pooled"))
    noise_n = sum(1 for r in frecs if r.get("noise"))
    flood_rows_n = flood_pipe.store.events_count()
    ok_flood = (pooled_n == 5 and noise_n == 1 and frecs[-1].get("noise")
                and frecs[-1].get("noise_reason") == "flooding"
                and flood_rows_n == 6)
    flood_pipe.close()
    ls2.close()
    record("AC-U5", ok_noise and ok_rows_kept and ok_no_items and ok_no_draft
           and ok_flood,
           "emoji-only=%s too-short=%s rows-kept-not-destroyed=%s no-items=%s"
           " no-draft=%s flood(6-ingests)=%s pooled=%d noise=%d rows-kept=%d"
           % (r_emoji["noise"], r_short["noise"], ok_rows_kept, ok_no_items,
              ok_no_draft, ok_flood, pooled_n, noise_n, flood_rows_n))

    # ---- AC-U6: content-addressed dedup -------------------------------------
    dup_content = "cross source duplicate probe text"
    r_first = pipe.submit("direct", a1, dup_content)
    ls.append(lobby.utc_now_iso(), "idea.submit", a1, "cocreate", dup_content,
              payload={"text": dup_content, "pool": "proposal-queue-stub"})
    pipe.ingest_lobby()
    twin_evt = P.compute_evt_id("lobby_idea", a1, dup_content)
    twin_item = pipe.store.item_row(twin_evt)
    ok_two_rows = (pipe.store.event_row(r_first["evt_id"]) is not None
                   and pipe.store.event_row(twin_evt) is not None)
    ok_cross = twin_item is not None and twin_item["duplicate_of"] == r_first["evt_id"]
    ok_replay, code_replay = expect_error(
        lambda: pipe.submit("direct", a1, dup_content), UGC.E_DUPLICATE)
    ls.append(lobby.utc_now_iso(), "idea.submit", a1, "cocreate", dup_content,
              payload={"text": dup_content, "pool": "proposal-queue-stub"})
    recs2 = pipe.ingest_lobby()
    ok_reingest = len(recs2) == 1 and recs2[0].get("code") == UGC.E_DUPLICATE
    record("AC-U6", ok_two_rows and ok_cross and ok_replay and ok_reingest,
           "same-source-replay=%s(%s) cross-source-two-rows=%s duplicate_of=%s"
           " re-ingest-dedup=%s" % (ok_replay, code_replay, ok_two_rows,
                                    ok_cross, ok_reingest))

    # ---- AC-U7: honest provenance on drafts ---------------------------------
    benches_evt = pipe.submit("direct", a1, "tiny idea: add benches",
                              producer="local_llm", ai_generated=True)["evt_id"]
    item = pipe.store.item_row(benches_evt)
    ok_item = item["producer"] == "rule_template" and item["ai_generated"] == 0
    d = pipe.draft(benches_evt)
    ok_draft = (d["producer"] == "rule_template" and d["ai_generated"] is False
                and d.get("ai_label") == cfg["compliance"]["ai_label_text"])
    ok_stored = pipe.store.draft_row(benches_evt) == d
    ok_state = pipe.store.item_row(benches_evt)["state"] == "drafted"
    ok_redraft, _ = expect_error(lambda: pipe.draft(benches_evt), UGC.E_BAD_STATE)
    record("AC-U7", ok_item and ok_draft and ok_stored and ok_state and ok_redraft,
           "client-spoof-ignored=%s (stored producer=%s ai_generated=%d)"
           " draft-face producer=%s ai_generated=%s label=%s state=%s"
           % (ok_item, item["producer"], item["ai_generated"], d["producer"],
              d["ai_generated"], bool(d.get("ai_label")), ok_state))

    # ---- AC-U9: state machine + CEO gate (DB triggers) ----------------------
    fr = pipe.final_review(benches_evt)
    ok_small = fr["state"] == "final_review" and fr["needs_ceo"] is False
    pipe.final_decide(benches_evt, "adopt")
    ok_small_adopt = pipe.store.item_row(benches_evt)["state"] == "adopted"
    land_evt = pipe.submit("avatar_intake", "C-land",
                           "big plan for the city " + lk)["evt_id"]
    pipe.draft(land_evt)
    fr2 = pipe.final_review(land_evt)
    ok_land = (fr2["state"] == "needs_ceo_review"
               and pipe.store.item_row(land_evt)["needs_ceo"] == 1)
    ok_app_refuse, code_app = expect_error(
        lambda: pipe.final_decide(land_evt, "adopt"), UGC.E_CEO_RECEIPT_REQUIRED)
    ok_force, det_force = raw_aborts(
        db, "UPDATE ugc_items SET state = 'adopted' WHERE item_id = ?",
        (land_evt,), "E_CEO_RECEIPT_REQUIRED")
    ok_freeze, det_freeze = raw_aborts(
        db, "UPDATE ugc_items SET needs_ceo = 0 WHERE item_id = ?",
        (land_evt,), "E_NEEDS_CEO_IMMUTABLE")
    ok_jump, det_jump = raw_aborts(
        db, "UPDATE ugc_items SET state = 'adopted' WHERE item_id = ?",
        (r_direct["evt_id"],), "E_BAD_TRANSITION")
    ok_terminal, det_terminal = raw_aborts(
        db, "UPDATE ugc_items SET state = 'pooled' WHERE item_id = ?",
        (benches_evt,), "E_BAD_TRANSITION")
    ok_inject, det_inject = raw_aborts(
        db, "INSERT INTO ugc_items (item_id, line, state, gate_status, producer,"
        " ai_generated, needs_ceo, duplicate_of, decision, ts_utc)"
        " VALUES ('raw-inj-1','bigdomain','adopted','pass','rule_template',0,0,"
        "NULL,'adopted','2026-09-24T00:00:00Z')", (), "E_ITEM_MUST_ENTER_POOLED")
    pipe.record_ceo_decision(land_evt, "approved")
    pipe.final_decide(land_evt, "adopt")
    ok_ceo_adopt = pipe.store.item_row(land_evt)["state"] == "adopted"
    land2_evt = pipe.submit("avatar_intake", "C-land2",
                            "second big plan " + lk)["evt_id"]
    pipe.draft(land2_evt)
    pipe.final_review(land2_evt)
    pipe.record_ceo_decision(land2_evt, "rejected")
    r_rej = pipe.final_decide(land2_evt, "reject")
    ok_ceo_reject = r_rej["state"] == "rejected"
    ok_bad_dec, _ = expect_error(
        lambda: pipe.final_decide(land2_evt, "maybe"), UGC.E_BAD_DECISION)
    record("AC-U9", ok_small and ok_small_adopt and ok_land and ok_app_refuse
           and ok_force and ok_freeze and ok_jump and ok_terminal and ok_inject
           and ok_ceo_adopt and ok_ceo_reject and ok_bad_dec,
           "small-L0-adopt=%s landfall-auto-marked=%s app-refuse=%s(%s)"
           " trigger-force-adopt=%s flag-freeze=%s pooled-jump=%s terminal-immutable=%s"
           " raw-insert=%s ceo-approved-adopt=%s ceo-rejected=%s bad-decision=%s"
           % (ok_small_adopt and ok_small, ok_land, ok_app_refuse, code_app,
              ok_force, ok_freeze, ok_jump, ok_terminal, ok_inject, ok_ceo_adopt,
              ok_ceo_reject, ok_bad_dec))

    # ---- AC-U10: receipts only at adoption + ledger cross-check -------------
    n_adopted = pipe.store.items_count("state = 'adopted'")
    n_receipts = pipe.store.gate_receipts_count()
    ok_counts = n_receipts == n_adopted == 2
    ok_only_adopted = (pipe.store.gate_receipt(benches_evt) is not None
                       and pipe.store.gate_receipt(land_evt) is not None
                       and pipe.store.gate_receipt(land2_evt) is None
                       and pipe.store.gate_receipt(r_gray2["evt_id"]) is None
                       and pipe.store.gate_receipt(r_direct["evt_id"]) is None)
    ok_bad_receipt, det_receipt = raw_aborts(
        db, "INSERT INTO gate_receipts (evt_id, gate, ts_utc) VALUES (?,?,?)",
        (r_direct["evt_id"], "pass", "2026-09-24T00:00:00Z"),
        "E_RECEIPT_REQUIRES_ADOPTED")
    with open(os.path.join(BASE, "..", "ledger", "config.json"),
              encoding="utf-8") as handle:
        lcfg = json.load(handle)
    led = LED.Ledger(os.path.join(tmp, "ledger.db"), lcfg)
    led.mint_to_pool("pool:share", 100, "SETTLE-UGC-1", "settlement")
    led.ensure_account("usr:ugc1", "AV-777")
    ok_bad_ref, code_bad_ref = expect_ledger_error(
        lambda: led.grant_reward("usr:ugc1", "cocreate", "EVT-FAKE-REF"),
        LED.E_GATE_REF)
    led.record_gate_pass(benches_evt)  # receipt = the share ref consumed face
    led.grant_reward("usr:ugc1", "cocreate", benches_evt)
    ok_good_ref = led.balance("usr:ugc1")["balance"] == \
        int(lcfg["actions"]["cocreate"]["score"])
    led.close()
    record("AC-U10", ok_counts and ok_only_adopted and ok_bad_receipt
           and ok_bad_ref and ok_good_ref,
           "receipts=%d adopted=%d only-adopted=%s bad-receipt-insert=%s;"
           " ledger bad-ref=%s(%s) receipt-ref-pays=%s"
           % (n_receipts, n_adopted, ok_only_adopted, ok_bad_receipt,
              ok_bad_ref, code_bad_ref, ok_good_ref))

    # ---- AC-U11: in-repo export + path gate ----------------------------------
    out = pipe.export()
    feed_dir = os.path.join(pipe.export_dir, "proposal_feed")
    feed_files = sorted(os.listdir(feed_dir)) if os.path.isdir(feed_dir) else []
    ok_feed = ("biggame.jsonl" in feed_files and "bigmoney.jsonl" in feed_files
               and "unsorted.jsonl" in feed_files)
    produced = [os.path.join(feed_dir, f) for f in feed_files] + [
        os.path.join(pipe.export_dir, "chronicle.jsonl"),
        os.path.join(pipe.export_dir, "hot_index.jsonl")]
    ok_inside = all(inside_repo(f) for f in produced) and all(
        os.path.isfile(f) for f in produced)
    hot_rows = [json.loads(line) for line in open(
        os.path.join(pipe.export_dir, "hot_index.jsonl"), encoding="utf-8")]
    ok_hot_sorted = all(hot_rows[i]["score"] >= hot_rows[i + 1]["score"]
                        for i in range(len(hot_rows) - 1)) and len(hot_rows) >= 2
    ok_chronicled = pipe.store.item_row(land2_evt)["state"] == "chronicled"
    record("AC-U11", ok_feed and ok_inside and ok_hot_sorted and ok_chronicled,
           "feed-lines=%s all-inside-repo=%s hot-sorted-desc=%s rejected->chronicled=%s"
           " path-gate-refusal-proven-in-AC-U2" % (feed_files, ok_inside,
                                                    ok_hot_sorted, ok_chronicled))

    # ---- AC-U12: city chronicle ----------------------------------------------
    chron_path = os.path.join(pipe.export_dir, "chronicle.jsonl")
    chron = [json.loads(line) for line in open(chron_path, encoding="utf-8")]
    by_evt = {c["evt_id"]: c for c in chron}
    ok_fields = all(("evt_id" in c and "summary" in c and "decision" in c
                     and "signature_slot" in c and "disclaimer" in c) for c in chron)
    ok_adopted_row = (by_evt.get(benches_evt, {}).get("signature_eligible") is True
                      and by_evt.get(benches_evt, {}).get("credit") == "named")
    ok_rejected_row = (by_evt.get(land2_evt, {}).get("signature_eligible") is False
                       and by_evt.get(land2_evt, {}).get("credit") == "record-only")
    ok_all_terminal = set(by_evt) == {benches_evt, land_evt, land2_evt}
    ok_rejected_zero = pipe.store.gate_receipt(land2_evt) is None
    cq = pipe.chronicle_query()
    ok_note = bool(cq.get("note")) and cq.get("disclaimer") == \
        cfg["compliance"]["disclaimer"]
    record("AC-U12", ok_fields and ok_adopted_row and ok_rejected_row
           and ok_all_terminal and ok_rejected_zero and ok_note,
           "chronicle-rows=%d fields=%s adopted-named=%s rejected-record-only=%s"
           " all-terminal-exported=%s rejected-zero-receipt=%s note=%s"
           % (len(chron), ok_fields, ok_adopted_row, ok_rejected_row,
              ok_all_terminal, ok_rejected_zero, ok_note))

    fails = [ac for ac, ok in RESULTS if not ok]
    total = len(RESULTS)
    print("SUITE %s (%d/%d criteria pass)" % ("PASS" if not fails else "FAIL",
                                              total - len(fails), total), flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
