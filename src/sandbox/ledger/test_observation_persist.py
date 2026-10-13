"""Cross-restart persistence window for the strategy paid-observation
face (BigDomain R1936; the observation seat of the R1886
persist-family lineage - the R1931-seeded row, criteria
pre-registered in the R1936 tech.md claim row before this code
existed; honesty law). Each criterion prints PASS/FAIL with
evidence; the process exits non-zero on any FAIL.

Three-instance world on the real product path: anchor world ->
close both pieces -> reopen the same db/config -> byte-identical
read replay -> restart-surviving gate probes (zero drift) ->
post-restart real-path continuation -> frozen faces + window
isolation -> pure-read law -> third instance stability.
strategy_view rows carry registered_utc (a persisted value, not
a clock echo), so full-dump byte-identity holds without clock
freezing; the evidence digests mask the registered_utc / spend_tx
/ tx fields (banded projection, R1902 law) so the suite stdout
stays deterministic across double runs.

Usage: python test_observation_persist.py
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import ledger as L          # noqa: E402  (P-47-2b core)
import observation as O     # noqa: E402  (R623 face)

RESULTS = []

ALPHA = {"sharpe": 1.9, "cagr_pct": 24.0, "max_dd_pct": -12.5,
         "trades": 311}
BETA = {"sharpe": 1.2, "cagr_pct": 9.0, "max_dd_pct": -6.5, "trades": 88}

_TS_RE = re.compile(r'"registered_utc": "[^"]*"')
_SPEND_RE = re.compile(r'"spend_tx": "[^"]*"')
_TX_RE = re.compile(r'"tx": "[^"]*"')


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_o_error(fn, *codes):
    try:
        fn()
    except O.ObservationError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def masked(text):
    out = _SPEND_RE.sub('"spend_tx": "<tx>"', text)
    out = _TX_RE.sub('"tx": "<tx>"', out)
    return _TS_RE.sub('"registered_utc": "<ts>"', out)


def evidence_digest(snap):
    parts = []
    for key in sorted(snap):
        val = snap[key]
        if isinstance(val, int):
            parts.append("%s=%s" % (key, val))
        else:
            parts.append("%s=%s" % (key, masked(val)))
    return sha16("\n".join(parts))


def table_counts(db_path):
    out = {}
    conn = sqlite3.connect(db_path)
    for tbl in ("ledger_tx", "ledger_entries", "obs_strategies",
                "obs_grants"):
        out[tbl] = int(conn.execute(
            "SELECT COUNT(*) FROM " + tbl).fetchone()[0])
    out["spend_tx"] = int(conn.execute(
        "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
    ).fetchone()[0])
    conn.close()
    return out


def spend_leg(db_path, tx_id):
    """SQL cross for one grant: the bound spend tx is a real ledger
    spend row with a debit leg on the buying account."""
    conn = sqlite3.connect(db_path)
    head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                        (tx_id,)).fetchone()
    leg = conn.execute(
        "SELECT e.direction FROM ledger_entries e JOIN ledger_tx t"
        " ON e.tx_id = t.tx_id WHERE e.tx_id = ? AND e.direction = 'debit'",
        (tx_id,)).fetchall()
    conn.close()
    return head[0] if head else None, [r[0] for r in leg]


def read_faces(of, led):
    return {
        "ent_alice": dump(of.entitlements_view("usr:alice")),
        "ent_bob": dump(of.entitlements_view("usr:bob")),
        "ent_carol": dump(of.entitlements_view("usr:carol")),
        "ent_dave": dump(of.entitlements_view("usr:dave")),
        "obs_alice_late": dump(of.observe("usr:alice", "strat:alpha",
                                          "2099-03")),
        "obs_bob_in": dump(of.observe("usr:bob", "strat:alpha",
                                       "2099-01")),
        "gate_alice_far": dump(of.can_observe("usr:alice", "strat:alpha",
                                              "2099-12")),
        "gate_bob_in": dump(of.can_observe("usr:bob", "strat:beta",
                                           "2099-01")),
        "gate_bob_out": dump(of.can_observe("usr:bob", "strat:beta",
                                            "2099-03")),
        "gate_carol": dump(of.can_observe("usr:carol", "strat:alpha",
                                          "2099-01")),
        "gate_dave": dump(of.can_observe("usr:dave", "strat:beta",
                                         "2099-01")),
        "view_alpha": dump(of.strategy_view("strat:alpha")),
        "view_beta": dump(of.strategy_view("strat:beta")),
        "bal_alice": led.balance("usr:alice")["balance"],
        "bal_bob": led.balance("usr:bob")["balance"],
        "bal_carol": led.balance("usr:carol")["balance"],
        "bal_dave": led.balance("usr:dave")["balance"],
        "bal_pool": led.balance("pool:reserve")["balance"],
    }


def face_diffs(a, b):
    return [k for k in a if a[k] != b[k]]


def five_balances(of, led):
    return tuple(read_faces(of, led)[k] for k in
                 ("bal_alice", "bal_bob", "bal_carol", "bal_dave",
                  "bal_pool"))


def io_read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def main():
    tmp = tempfile.mkdtemp(prefix="observation-persist-")
    cfg_path = os.path.join(BASE, "config.json")
    cfg_text = io_read(cfg_path)
    cfg = json.loads(cfg_text)
    cfg_sha_before = sha16(cfg_text)
    obsmod_sha_before = sha16(io_read(os.path.join(BASE,
                                                   "observation.py")))
    ledmod_sha_before = sha16(io_read(os.path.join(BASE, "ledger.py")))
    repo_root = os.path.realpath(
        os.path.dirname(os.path.dirname(os.path.dirname(BASE))))
    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    of = O.ObservationFace(led)
    led.mint_to_pool("pool:reserve", 20000, "SETTLE-OBP-A", "settlement")
    led.ensure_account("usr:alice", census_avatar_id="alice")
    led.ensure_account("usr:bob", census_avatar_id="bob")
    led.ensure_account("usr:carol", census_avatar_id="carol")
    led.ensure_account("usr:dave", census_avatar_id="dave")
    led.adjust([("pool:reserve", "debit", 2000),
                ("usr:alice", "credit", 2000)],
               "manual:obp-fund-alice", "persist window funding alice")
    led.adjust([("pool:reserve", "debit", 3000),
                ("usr:bob", "credit", 3000)],
               "manual:obp-fund-bob", "persist window funding bob")
    led.adjust([("pool:reserve", "debit", 1000),
                ("usr:carol", "credit", 1000)],
               "manual:obp-fund-carol", "persist window funding carol")
    led.adjust([("pool:reserve", "debit", 500),
                ("usr:dave", "credit", 500)],
               "manual:obp-fund-dave", "persist window funding dave")

    # -- AC-OBP1: anchor world, real paths, pre-close snapshot -------
    r_alpha = of.register_strategy("strat:alpha", "usr:maker", ALPHA)
    r_beta = of.register_strategy("strat:beta", "usr:maker", BETA)
    g_al = of.buy_single("usr:alice", "strat:alpha", 99, "order:obp-a1")
    g_bob = of.buy_pass("usr:bob", "2099-01", 199, "order:obp-b1")
    ok_dup_pre, code_dup_pre = expect_o_error(
        lambda: of.buy_single("usr:alice", "strat:alpha", 99,
                              "order:obp-dup"), O.E_OBS_DUP)
    ok_pdup_pre, code_pdup_pre = expect_o_error(
        lambda: of.buy_pass("usr:bob", "2099-01", 199, "order:obp-pdup"),
        O.E_OBS_PASS_DUP)
    ok_unk_pre, code_unk_pre = expect_o_error(
        lambda: of.observe("usr:bob", "strat:ghost", "2099-01"),
        O.E_OBS_UNKNOWN)
    ok_den_pre, code_den_pre = expect_o_error(
        lambda: of.observe("usr:carol", "strat:alpha", "2099-01"),
        O.E_OBS_DENIED)
    head_al, legs_al = spend_leg(db_path, g_al["spend_tx"])
    head_bob, legs_bob = spend_leg(db_path, g_bob["spend_tx"])
    conn = sqlite3.connect(db_path)
    cols_strat = [r[1] for r in conn.execute(
        "PRAGMA table_info(obs_strategies)").fetchall()]
    conn.close()
    snap = read_faces(of, led)
    cnt1 = table_counts(db_path)
    ent_alice = json.loads(snap["ent_alice"])
    ent_bob = json.loads(snap["ent_bob"])
    ent_carol = json.loads(snap["ent_carol"])
    ent_dave = json.loads(snap["ent_dave"])
    obs_alice = json.loads(snap["obs_alice_late"])
    view_alpha = json.loads(snap["view_alpha"])
    ok1 = (r_alpha["registered"] and r_beta["registered"]
           and g_al["grant_kind"] == "single"
           and g_bob["grant_kind"] == "pass"
           and head_al == "spend" and head_bob == "spend"
           and legs_al == ["debit"] and legs_bob == ["debit"]
           and ok_dup_pre and code_dup_pre == O.E_OBS_DUP
           and ok_pdup_pre and code_pdup_pre == O.E_OBS_PASS_DUP
           and ok_unk_pre and code_unk_pre == O.E_OBS_UNKNOWN
           and ok_den_pre and code_den_pre == O.E_OBS_DENIED
           and cnt1["obs_strategies"] == 2 and cnt1["obs_grants"] == 2
           and cnt1["spend_tx"] == 2 and cnt1["ledger_tx"] == 7
           and cnt1["ledger_entries"] == 14
           and sorted(obs_alice.keys()) == ["kind", "strategy_id",
                                            "summary", "tx"]
           and sorted(view_alpha.keys()) == ["creator_account",
                                             "registered_utc",
                                             "strategy_id", "summary"]
           and sorted(ent_alice["grants"][0].keys()) == [
               "grant_id", "kind", "pass_month", "spend_tx",
               "strategy_id", "token_price"]
           and cols_strat == ["strategy_id", "creator_account",
                              "summary_json", "registered_utc"]
           and "source" not in cols_strat
           and len(ent_alice["grants"]) == 1
           and ent_alice["grants"][0]["kind"] == "single"
           and len(ent_bob["grants"]) == 1
           and ent_bob["grants"][0]["kind"] == "pass"
           and ent_bob["grants"][0]["pass_month"] == "2099-01"
           and ent_carol["grants"] == [] and ent_dave["grants"] == []
           and snap["bal_alice"] == 1901 and snap["bal_bob"] == 2801
           and snap["bal_carol"] == 1000 and snap["bal_dave"] == 500
           and snap["bal_pool"] == 13798
           and json.loads(snap["gate_carol"]) == {
               "allowed": False, "kind": None, "tx": None})
    record("AC-OBP1", ok1,
           "anchor world: 2 strategies registered (results-only, no"
           " source column %s); alice single + bob pass 2099-01 bound"
           " to real spend txs (type=spend, debit legs); pre-close"
           " gates dup=%s pass-dup=%s unknown=%s denied=%s zero charge"
           " zero rows; counts strat=%d grants=%d spend=%d tx=%d"
           " entries=%d; balances %d/%d/%d/%d/%d"
           % (cols_strat, code_dup_pre, code_pdup_pre, code_unk_pre,
              code_den_pre, cnt1["obs_strategies"], cnt1["obs_grants"],
              cnt1["spend_tx"], cnt1["ledger_tx"],
              cnt1["ledger_entries"], snap["bal_alice"],
              snap["bal_bob"], snap["bal_carol"], snap["bal_dave"],
              snap["bal_pool"]))

    # -- AC-OBP2: close both pieces, reopen, byte-identical replay ---
    of.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    of2 = O.ObservationFace(led2)
    snap2 = read_faces(of2, led2)
    diffs2 = face_diffs(snap, snap2)
    ok2 = (diffs2 == [] and len(snap2) == 18
           and snap2["bal_alice"] == 1901 and snap2["bal_bob"] == 2801
           and snap2["bal_carol"] == 1000 and snap2["bal_dave"] == 500
           and snap2["bal_pool"] == 13798)
    record("AC-OBP2", ok2,
           "of.close -> led.close -> instance-2 same db/cfg reopen:"
           " all %d faces byte-identical (diffs=%s) incl."
           " registered_utc persisted value (no clock echo);"
           " digest %s"
           % (len(snap2), diffs2 or "none", evidence_digest(snap2)))

    # -- AC-OBP3: gate law survives restart, probes zero drift -------
    cnt3a = table_counts(db_path)
    bal3a = five_balances(of2, led2)
    ok_dup2, code_dup2 = expect_o_error(
        lambda: of2.buy_single("usr:alice", "strat:alpha", 99,
                               "order:obp-dup2"), O.E_OBS_DUP)
    ok_pdup2, code_pdup2 = expect_o_error(
        lambda: of2.buy_pass("usr:bob", "2099-01", 199,
                             "order:obp-pdup2"), O.E_OBS_PASS_DUP)
    ok_unk2, code_unk2 = expect_o_error(
        lambda: of2.observe("usr:bob", "strat:ghost", "2099-01"),
        O.E_OBS_UNKNOWN)
    ok_den2, code_den2 = expect_o_error(
        lambda: of2.observe("usr:carol", "strat:alpha", "2099-01"),
        O.E_OBS_DENIED)
    ok_win2, code_win2 = expect_o_error(
        lambda: of2.observe("usr:bob", "strat:beta", "2099-03"),
        O.E_OBS_DENIED)
    cnt3b = table_counts(db_path)
    bal3b = five_balances(of2, led2)
    ok3 = (ok_dup2 and code_dup2 == O.E_OBS_DUP
           and ok_pdup2 and code_pdup2 == O.E_OBS_PASS_DUP
           and ok_unk2 and code_unk2 == O.E_OBS_UNKNOWN
           and ok_den2 and code_den2 == O.E_OBS_DENIED
           and ok_win2 and code_win2 == O.E_OBS_DENIED
           and cnt3b == cnt3a and bal3b == bal3a)
    record("AC-OBP3", ok3,
           "restart-surviving gates: five probes rejected (%s/%s/%s/%s"
           "/%s) - dup-before-spend and window-door laws survive the"
           " restart; probe batch left counts %s and balances"
           " %s untouched"
           % (code_dup2, code_pdup2, code_unk2, code_den2, code_win2,
              {k: cnt3b[k] for k in ("obs_strategies", "obs_grants",
                                      "spend_tx")}, bal3b))

    # -- AC-OBP4: post-restart real-path continuation + SQL cross -----
    g_bob2 = of2.buy_pass("usr:bob", "2099-02", 199, "order:obp-b2")
    g_dave = of2.buy_single("usr:dave", "strat:beta", 49,
                            "order:obp-d1")
    head_b2, legs_b2 = spend_leg(db_path, g_bob2["spend_tx"])
    head_dv, legs_dv = spend_leg(db_path, g_dave["spend_tx"])
    snap4 = read_faces(of2, led2)
    cnt4 = table_counts(db_path)
    ent_bob2 = json.loads(snap4["ent_bob"])["grants"]
    ent_dave2 = json.loads(snap4["ent_dave"])["grants"]
    obs_bob_02 = of2.observe("usr:bob", "strat:alpha", "2099-02")
    gate_dave2 = of2.can_observe("usr:dave", "strat:beta", "2099-12")
    ok4 = (g_bob2["pass_month"] == "2099-02"
           and g_dave["strategy_id"] == "strat:beta"
           and head_b2 == "spend" and head_dv == "spend"
           and legs_b2 == ["debit"] and legs_dv == ["debit"]
           and len(ent_bob2) == 2
           and [g["pass_month"] for g in ent_bob2] == ["2099-01",
                                                       "2099-02"]
           and len(ent_dave2) == 1 and ent_dave2[0]["kind"] == "single"
           and obs_bob_02["kind"] == "pass"
           and gate_dave2["allowed"] is True
           and gate_dave2["kind"] == "single"
           and cnt4["obs_grants"] == 4 and cnt4["spend_tx"] == 4
           and cnt4["ledger_tx"] == 9 and cnt4["ledger_entries"] == 18
           and snap4["bal_bob"] == 2602 and snap4["bal_dave"] == 451
           and snap4["bal_pool"] == 14046
           and snap4["bal_alice"] == 1901 and snap4["bal_carol"] == 1000)
    record("AC-OBP4", ok4,
           "post-restart continuation: bob pass 2099-02 + dave single"
           " beta bound to two new real spend txs (spend/debit);"
           " zero-cache recompute bob grants 1->2 months"
           " %s dave 0->1 single; observe bob@2099-02 kind=pass"
           " (new window opens); dave far-month gate kind=single"
           " (permanent grant); counts grants=%d spend=%d tx=%d"
           " entries=%d; balances %d/%d/%d/%d/%d"
           % ([g["pass_month"] for g in ent_bob2], cnt4["obs_grants"],
              cnt4["spend_tx"], cnt4["ledger_tx"],
              cnt4["ledger_entries"], snap4["bal_alice"],
              snap4["bal_bob"], snap4["bal_carol"], snap4["bal_dave"],
              snap4["bal_pool"]))

    # -- AC-OBP5: frozen faces + window isolation + zero permeation ---
    gate_bob_out4 = json.loads(snap4["gate_bob_out"])
    gate_alice_far4 = json.loads(snap4["gate_alice_far"])
    ok5 = (snap4["ent_alice"] == snap["ent_alice"]
           and snap4["obs_alice_late"] == snap["obs_alice_late"]
           and snap4["ent_carol"] == snap["ent_carol"]
           and json.loads(snap4["ent_carol"])["grants"] == []
           and snap4["view_alpha"] == snap["view_alpha"]
           and snap4["view_beta"] == snap["view_beta"]
           and gate_bob_out4 == {"allowed": False, "kind": None,
                                 "tx": None}
           and gate_alice_far4["allowed"] is True
           and gate_alice_far4["kind"] == "single")
    record("AC-OBP5", ok5,
           "frozen faces: alice entitlements+observe and carol empty"
           " spine byte-identical to the anchor, registry views"
           " immutable; window isolation across restart - bob's"
           " 2099-01 pass does not cover 2099-03 (%s); alice single"
           " permanent at far month 2099-12 (kind=%s); zero"
           " permeation into carol"
           % (gate_bob_out4, gate_alice_far4["kind"]))

    # -- AC-OBP6: pure-read law ---------------------------------------
    cnt6a = table_counts(db_path)
    bal6a = five_balances(of2, led2)
    for _ in range(2):
        read_faces(of2, led2)
    for _ in range(3):
        of2.observe("usr:alice", "strat:alpha", "2099-05")
        of2.strategy_view("strat:beta")
        of2.entitlements_view("usr:bob")
    cnt6b = table_counts(db_path)
    bal6b = five_balances(of2, led2)
    ok6 = (cnt6b == cnt6a and bal6b == bal6a
           and cnt6b["obs_strategies"] == 2 and cnt6b["obs_grants"] == 4
           and cnt6b["spend_tx"] == 4 and cnt6b["ledger_tx"] == 9
           and cnt6b["ledger_entries"] == 18)
    record("AC-OBP6", ok6,
           "pure-read law: full battery x2 plus repeated single reads"
           " left counts %s and balances %s constant (reads carry"
           " zero side effects)"
           % ({k: cnt6b[k] for k in ("obs_strategies", "obs_grants",
                                     "spend_tx", "ledger_tx",
                                     "ledger_entries")}, bal6b))

    # -- AC-OBP7: third instance stability + hygiene -------------------
    of2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    of3 = O.ObservationFace(led3)
    snap7 = read_faces(of3, led3)
    diffs7 = face_diffs(snap4, snap7)
    cfg_sha_after = sha16(io_read(cfg_path))
    obsmod_sha_after = sha16(io_read(os.path.join(BASE,
                                                  "observation.py")))
    ledmod_sha_after = sha16(io_read(os.path.join(BASE, "ledger.py")))
    src_non_ascii = sum(1 for ch in io_read(os.path.abspath(__file__))
                        if ord(ch) > 127)
    tmp_outside = not os.path.realpath(tmp).startswith(repo_root)
    ok7 = (diffs7 == [] and cfg_sha_after == cfg_sha_before
           and obsmod_sha_after == obsmod_sha_before
           and ledmod_sha_after == ledmod_sha_before
           and src_non_ascii == 0 and tmp_outside)
    record("AC-OBP7", ok7,
           "second restart: instance-3 reopen replays all %d faces"
           " byte-identical to the instance-2 final state (diffs=%s);"
           " config/observation/ledger sha16 unchanged (%s/%s/%s);"
           " suite source pure ASCII (%d non-ascii); world tmp outside"
           " repo (%s)"
           % (len(snap7), diffs7 or "none", cfg_sha_after,
              obsmod_sha_after, ledmod_sha_after, src_non_ascii,
              tmp_outside))

    of3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    print("SUITE %s %d/%d" % ("PASS" if fail == 0 else "FAIL",
                             len(RESULTS) - fail, len(RESULTS)), flush=True)
    sys.exit(0 if fail == 0 else 2)


if __name__ == "__main__":
    main()
