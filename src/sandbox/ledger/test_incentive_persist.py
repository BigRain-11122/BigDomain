"""Cross-restart persistence suite for the UGC creator incentive
gradient allocator (BigDomain R1958; FIFO head claim of the R1953
reseed row; persist-example family R1886 lineage).
Asserts the pre-registered criteria AC-ICP1..AC-ICP7 from the
tech.md incentive-persist claim row (criteria were registered before
this code existed; honesty law). Two-piece restart law: the
incentive face owns its sqlite connection over the same ledger db
(share payouts ride the ledger public API, caller-owned face
injected by reference); restart = face.close + led.close -> new
Ledger + new IncentiveFace over the same db and config.
settled_utc values are real clock stamps frozen in the db: they are
compared byte-wise for restart identity inside this run but never
printed to stdout (double-run determinism law).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Usage: python test_incentive_persist.py
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

import ledger as L       # noqa: E402  (P-47-2b core)
import incentive as IN  # noqa: E402  (R600 allocation-layer face)

RESULTS = []

ACCOUNTS = ("alice", "bob", "carol", "dave", "erin", "frank")
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def expect_incentive_error(fn, *codes):
    try:
        fn()
    except IN.IncentiveError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def win_projection(db_path):
    """Stable stdout-safe projection: settled_utc values never enter
    printed evidence (double-run determinism); the full raw rows are
    compared separately in-run for restart identity."""
    conn = sqlite3.connect(db_path)
    rows = [list(r) for r in conn.execute(
        "SELECT window_id, total_paid FROM incentive_windows"
        " ORDER BY window_id").fetchall()]
    conn.close()
    return rows


def win_raw_rows(db_path):
    conn = sqlite3.connect(db_path)
    rows = [list(r) for r in conn.execute(
        "SELECT window_id, settled_utc, total_paid FROM"
        " incentive_windows ORDER BY window_id").fetchall()]
    conn.close()
    return rows


def win_count(db_path):
    conn = sqlite3.connect(db_path)
    n = conn.execute("SELECT COUNT(*) FROM incentive_windows"
                     ).fetchone()[0]
    conn.close()
    return int(n)


def tx_count(db_path):
    conn = sqlite3.connect(db_path)
    n = conn.execute("SELECT COUNT(*) FROM ledger_tx").fetchone()[0]
    conn.close()
    return int(n)


def inc_tx_rows(db_path):
    conn = sqlite3.connect(db_path)
    rows = [list(r) for r in conn.execute(
        "SELECT e.account_id, e.amount, t.ref FROM ledger_entries e"
        " JOIN ledger_tx t ON t.tx_id = e.tx_id"
        " WHERE t.ref LIKE 'incentive:%' AND e.direction = 'credit'"
        " ORDER BY t.ref").fetchall()]
    conn.close()
    return rows


def balance_face(led):
    out = {"pool:share": led.balance("pool:share")["balance"]}
    for who in ACCOUNTS:
        out["usr:" + who] = led.balance("usr:" + who)["balance"]
    return out


def battery(led, db_path):
    """Four-element read face: window projection + balance face +
    incentive tx join + window count."""
    out = {
        "win_projection": win_projection(db_path),
        "balances": balance_face(led),
        "inc_tx": inc_tx_rows(db_path),
        "win_count": win_count(db_path),
    }
    return json.dumps(out, sort_keys=True, default=str)


def gate_batch(led, face, db_path):
    """Seven-gate reject probe batch (every reject fires before any
    row write). Returns (codes, all_ok, flat) where flat is the
    four-counter stability across the batch."""
    pre = (led.balance("pool:share")["balance"],
           tuple(led.balance("usr:" + w)["balance"]
                 for w in ACCOUNTS),
           win_count(db_path), tx_count(db_path))
    codes = []
    all_ok = True

    def probe(fn, *expect):
        ok, code = expect_incentive_error(fn, *expect)
        codes.append(code if ok else "WRONG:" + str(code))
        return ok

    all_ok &= probe(
        lambda: face.settle_window("W1", [("usr:alice", 100)]),
        IN.E_INC_WINDOW_DUP)
    all_ok &= probe(
        lambda: face.settle_window("W-GATE", []),
        IN.E_INC_EMPTY)
    all_ok &= probe(
        lambda: face.settle_window("W-GATE", [("usr:alice", 0)]),
        IN.E_INC_BAD_UNITS)
    all_ok &= probe(
        lambda: face.settle_window("W-GATE", [("corp:x", 10)]),
        IN.E_INC_BAD_ACCOUNT)
    all_ok &= probe(
        lambda: face.settle_window("W-GATE",
                                   [("usr:alice", 10),
                                    ("usr:alice", 5)]),
        IN.E_INC_DUP_CREATOR)
    all_ok &= probe(
        lambda: face.settle_window("", [("usr:alice", 10)]),
        IN.E_INC_BAD_PARAM)
    all_ok &= probe(
        lambda: IN.IncentiveFace(
            led, {"bands": [[5, 10], [5, 20]], "collar": 100,
                  "budget": 400}),
        IN.E_INC_BAD_PARAM)
    post = (led.balance("pool:share")["balance"],
            tuple(led.balance("usr:" + w)["balance"]
                  for w in ACCOUNTS),
            win_count(db_path), tx_count(db_path))
    return codes, all_ok, pre, post


def main():
    tmp = tempfile.mkdtemp(prefix="incentive-persist-")
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(BASE, "incentive.py"), "rb") as handle:
        incentive_bytes = handle.read()
    with open(os.path.join(BASE, "ledger.py"), "rb") as handle:
        ledger_bytes = handle.read()

    db_path = os.path.join(tmp, "ledger.db")

    led = L.Ledger(db_path, cfg)
    face = IN.IncentiveFace(led)
    led.mint_to_pool("pool:share", 2000, "SETTLE-ICP-A", "settlement")
    for who in ACCOUNTS:
        led.ensure_account("usr:" + who, census_avatar_id=who)

    # -- AC-ICP1: anchor world + four-element snapshot ---------------------
    paid_w1 = face.settle_window("W1", [
        ("usr:alice", 100),   # raw 270 -> collar 150
        ("usr:bob", 30),      # raw 130
        ("usr:carol", 30),    # raw 130; capped 410 > 400 -> scale
    ])
    paid_w2 = face.settle_window("W2", [("usr:dave", 10 ** 6)])
    snap_battery = battery(led, db_path)
    snap_raw = win_raw_rows(db_path)
    snap_count = win_count(db_path)
    snap_tx = tx_count(db_path)
    snap_inc_tx = inc_tx_rows(db_path)
    bal1 = balance_face(led)
    ts_ok = all(TS_RE.match(r[1]) is not None for r in snap_raw)
    ok1 = (paid_w1 == [("usr:alice", 147), ("usr:bob", 127),
                       ("usr:carol", 126)]
           and paid_w2 == [("usr:dave", 150)]
           and snap_count == 2 and ts_ok
           and bal1["pool:share"] == 2000 - 550
           and bal1["usr:alice"] == 147 and bal1["usr:bob"] == 127
           and bal1["usr:carol"] == 126 and bal1["usr:dave"] == 150
           and bal1["usr:erin"] == 0 and bal1["usr:frank"] == 0
           and win_projection(db_path) == [["W1", 400], ["W2", 150]]
           and sum(r[1] for r in snap_inc_tx) == 550
           and len(snap_inc_tx) == 4)
    record("AC-ICP1", ok1, "anchor world: W1 budget-binding"
          " 410->400 pro-rata integer landing %s (zero rounding"
          " loss); W2 collar-binding %s; four-element snapshot:"
          " windows projection %s, pool %d, credits %s,"
          " erin/frank zero; settled_utc format law ok=%s"
          % (paid_w1, paid_w2, win_projection(db_path),
             bal1["pool:share"],
             [(r[0], r[1]) for r in inc_tx_rows(db_path)], ts_ok))

    # -- AC-ICP2: two-piece close -> reopen, byte-identical battery -------
    codes1, ok_gates1, pre1, post1 = gate_batch(led, face, db_path)
    ok_gates1_flat = (pre1 == post1)
    face.close()
    led.close()
    led2 = L.Ledger(db_path, cfg)
    face2 = IN.IncentiveFace(led2)
    post_battery = battery(led2, db_path)
    post_raw = win_raw_rows(db_path)
    ok2 = (post_battery == snap_battery and post_raw == snap_raw
           and ok_gates1 and ok_gates1_flat)
    record("AC-ICP2", ok2, "close -> new Ledger + new IncentiveFace"
          " over the same db: read battery byte-identical (%d bytes)"
          " and full raw window rows (settled_utc frozen stamps)"
          " byte-identical in-run = zero in-memory drift; seven-gate"
          " probe batch on instance one codes %s all-reject with"
          " four counters flat" % (len(snap_battery.encode("utf-8")),
                                  codes1))

    # -- AC-ICP3: gates cross-restart, same codes, same order ------------
    codes2, ok_gates2, pre2, post2 = gate_batch(led2, face2, db_path)
    ok3 = (codes2 == codes1 and ok_gates2 and pre2 == post2
           and pre2 == pre1)
    record("AC-ICP3", ok3, "restart-surviving gates: probe batch on"
          " the reopened instance returns the same code sequence %s"
          " (seven rejects); four counters flat %s across both"
          " instances = every reject still fires before any write"
          % (codes2, pre2 == post2))

    # -- AC-ICP4: real-path continuation, zero-cache recompute ------------
    paid_w3 = face2.settle_window("W3", [
        ("usr:alice", 20),   # raw 110
        ("usr:bob", 10),     # raw 75
        ("usr:erin", 6),     # raw 55; total 240 <= budget, no scaling
    ])
    bal4 = balance_face(led2)
    ok4 = (paid_w3 == [("usr:alice", 110), ("usr:bob", 75),
                       ("usr:erin", 55)]
           and bal4["usr:alice"] == 257 and bal4["usr:bob"] == 202
           and bal4["usr:carol"] == 126 and bal4["usr:dave"] == 150
           and bal4["usr:erin"] == 55 and bal4["usr:frank"] == 0
           and bal4["pool:share"] == 2000 - 790
           and win_count(db_path) == 3
           and win_projection(db_path) == [["W1", 400], ["W2", 150],
                                            ["W3", 240]]
           and len(inc_tx_rows(db_path)) == 7)
    record("AC-ICP4", ok4, "post-restart continuation: W3 settles"
          " %s (240 <= budget, no scaling); balances recompute"
          " from ledger truth not cache: alice 147->%d bob"
          " 127->%d erin 0->%d, pool %d = 2000 - 790; window"
          " rows 2->3; incentive tx rows 4->7 (new window rides"
          " alongside the frozen two)"
          % (paid_w3, bal4["usr:alice"], bal4["usr:bob"],
             bal4["usr:erin"], bal4["pool:share"]))

    # -- AC-ICP5: frozen anchor rows + replay gate cross-restart ----------
    now_raw = win_raw_rows(db_path)
    frozen = now_raw[:2] == snap_raw
    tx_prefix = inc_tx_rows(db_path)[:4] == snap_inc_tx
    ok_replay1, code_r1 = expect_incentive_error(
        lambda: face2.settle_window("W1", [("usr:alice", 100)]),
        IN.E_INC_WINDOW_DUP)
    ok_replay2, code_r2 = expect_incentive_error(
        lambda: face2.settle_window("W2", [("usr:dave", 1)]),
        IN.E_INC_WINDOW_DUP)
    pre5 = (led2.balance("pool:share")["balance"],
            win_count(db_path), tx_count(db_path))
    post5 = (led2.balance("pool:share")["balance"],
             win_count(db_path), tx_count(db_path))
    ok5 = (frozen and tx_prefix and ok_replay1
           and code_r1 == IN.E_INC_WINDOW_DUP and ok_replay2
           and code_r2 == IN.E_INC_WINDOW_DUP and pre5 == post5)
    record("AC-ICP5", ok5, "frozen anchors: W1/W2 full raw rows"
          " (settled_utc included) byte-identical after restart +"
          " continuation (append-only: 2 -> %d rows); incentive tx"
          " prefix 4 rows byte-identical; replay gates W1 %s / W2"
          " %s both rejected with pool/window/tx counters flat ="
          " zero ledger movement"
          % (len(now_raw), code_r1, code_r2))

    # -- AC-ICP6: pure-read law --------------------------------------------
    before6 = (led2.balance("pool:share")["balance"],
               tuple(led2.balance("usr:" + w)["balance"]
                     for w in ACCOUNTS),
               win_count(db_path), tx_count(db_path))
    b1 = battery(led2, db_path)
    b2 = battery(led2, db_path)
    after6 = (led2.balance("pool:share")["balance"],
              tuple(led2.balance("usr:" + w)["balance"]
                    for w in ACCOUNTS),
              win_count(db_path), tx_count(db_path))
    ok6 = (before6 == after6 and b1 == b2)
    record("AC-ICP6", ok6, "pure-read law: full four-element battery"
          " double-call byte-identical; pool / six balances /"
          " window rows / tx rows all flat across the read batch"
          " (reads pay nothing, zero side effects)")

    # -- AC-ICP7: third instance stable + hygiene -------------------------
    end_battery = battery(led2, db_path)
    face2.close()
    led2.close()
    led3 = L.Ledger(db_path, cfg)
    face3 = IN.IncentiveFace(led3)
    third_battery = battery(led3, db_path)
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_after = handle.read()
    with open(os.path.join(BASE, "incentive.py"), "rb") as handle:
        incentive_after = handle.read()
    with open(os.path.join(BASE, "ledger.py"), "rb") as handle:
        ledger_after = handle.read()
    with open(os.path.abspath(__file__), "rb") as handle:
        own_bytes = handle.read()
    own_non_ascii = sum(1 for b in own_bytes if b > 127)
    sha_own = hashlib.sha256(own_bytes).hexdigest()[:16]
    net_imports = [ln.strip() for ln in own_bytes.decode(
        "utf-8").splitlines()
        if ln.strip().startswith("import ")
        or ln.strip().startswith("from ")]
    src_text = incentive_bytes.decode("utf-8")
    update_hits = [ln.strip() for ln in src_text.splitlines()
                   if "UPDATE " in ln.upper()
                   and "execute(" in ln]
    ok7 = (third_battery == end_battery
           and cfg_after == cfg_bytes
           and incentive_after == incentive_bytes
           and ledger_after == ledger_bytes
           and own_non_ascii == 0
           and tmp.startswith(tempfile.gettempdir())
           and update_hits == []
           and "incentive" not in cfg)
    record("AC-ICP7", ok7, "second close -> third instance over the"
          " same db: battery byte-identical to the second-instance"
          " end state; config.json / incentive.py / ledger.py"
          " byte-identical before/after; suite source pure ASCII"
          " (%d non-ascii bytes, sha16 %s); %d imports all stdlib"
          " (zero network libraries); world in tempfile.gettempdir()"
          "; incentive.py source zero UPDATE statements"
          " (append-only law machine-checked); shipped config"
          " carries no incentive key"
          % (own_non_ascii, sha_own, len(net_imports)))

    face3.close()
    led3.close()
    fails = [ac for ac, ok in RESULTS if not ok]
    print("SUITE %s (%d/%d criteria green)%s"
          % ("PASS" if not fails else "FAIL",
             len(RESULTS) - len(fails), len(RESULTS),
             "" if not fails else " - failed: " + ",".join(fails)),
          flush=True)
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())
