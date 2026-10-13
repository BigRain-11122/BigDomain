"""Cross-restart persistence window for the minor guardian guard
face (BigDomain R1939; the minors seat of the R1886 persist-family
lineage - the R1933-seeded row, criteria pre-registered in the
R1939 tech.md claim row before this code existed; honesty law).
Each criterion prints PASS/FAIL with evidence; the process exits
non-zero on any FAIL.

Three-instance world on the real product path: anchor world
(four-resident spectrum: single-window minor with a spend ledger,
dual-window minor, adult pass-through, unconfigured fail-closed
minor) -> close -> reopen the same db_path -> byte-identical
battery replay -> restart-surviving gate probes -> post-restart
real-path continuation (idempotent-ref spend + brand-new minor
registered on the reopened instance) -> frozen history face +
cross-restart idempotent replay + per-(resident,date) ref-domain
law -> pure-read law -> third instance stability. day_readout /
residents_readout are caller-supplied-date pure-value read faces
with zero clock echo (minors.py no-wall-clock law), so full-dump
byte-identity holds without clock freezing and the suite stdout
stays deterministic across double runs.

Usage: python test_minors_persist.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

ROOT_MARK = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from minors import GuardError, MinorGuardFace, render_report  # noqa: E402

RESULTS = []


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(obj):
    return json.dumps(obj, sort_keys=True)


def battery(f):
    return {
        "residents": dump(f.residents_readout()),
        "kid1_d02": dump(f.day_readout("kid1", "2026-10-02")),
        "kid1_d03": dump(f.day_readout("kid1", "2026-10-03")),
        "kid1_d04": dump(f.day_readout("kid1", "2026-10-04")),
        "kid2_d02": dump(f.day_readout("kid2", "2026-10-02")),
        "kidx_d02": dump(f.day_readout("kidX", "2026-10-02")),
        "adult_d02": dump(f.day_readout("adult1", "2026-10-02")),
        "kid3_d04": dump(f.day_readout("kid3", "2026-10-04")),
    }


def table_counts(db_path):
    out = {}
    conn = sqlite3.connect(db_path)
    for tbl in ("mg_residents", "mg_limits", "mg_day_spend"):
        out[tbl] = int(conn.execute(
            "SELECT COUNT(*) FROM " + tbl).fetchone()[0])
    conn.close()
    return out


PROBE_CODES = (
    ("E_MG_TIME", lambda f: f.check_time("kid1", 1300, "2026-10-02")),
    ("E_MG_SPEND_SINGLE",
     lambda f: f.check_spend("kid1", 1500, "2026-10-02")),
    ("E_MG_SPEND_DAILY",
     lambda f: f.check_spend("kid1", 800, "2026-10-02")),
    ("E_MG_NO_LIMIT", lambda f: f.check_spend("kidX", 100, "2026-10-02")),
    ("E_MG_LIVE_BAN", lambda f: f.check_live("kid1")),
    ("E_MG_MARKETING_BAN", lambda f: f.check_marketing("kid1")),
    ("E_MG_GUARDIAN", lambda f: f.set_guardian_limits(
        "guardB", "kid1", allowed_windows=[(0, 60)],
        single_cent=100, daily_cent=100)),
    ("E_MG_DUP", lambda f: f.register_resident("kid1", True, "guardianA")),
)


def probe_batch(f):
    got = []
    for want, fn in PROBE_CODES:
        try:
            fn(f)
            got.append("NO-RAISE(want %s)" % want)
        except GuardError as ge:
            got.append(ge.code if ge.code == want
                       else "WRONG %s(want %s)" % (ge.code, want))
    return got


def adult_passthrough(f):
    return (f.check_time("adult1", 300, "2026-10-02")["scope"] == "adult"
            and f.check_spend("adult1", 999999, "2026-10-02")["scope"]
            == "adult"
            and f.check_live("adult1")["allowed"]
            and f.check_marketing("adult1")["allowed"])


def build_anchor_world(f):
    """Real product path: registration, guardian limits, spend
    ledger across two dates (the AC-MG1 spectrum)."""
    f.register_resident("kid1", True, "guardianA")
    f.register_resident("kid2", True, "guardianB")
    f.register_resident("adult1", False)
    f.register_resident("kidX", True, "guardX")
    lim1 = f.set_guardian_limits(
        "guardianA", "kid1", allowed_windows=[(1080, 1200)],
        single_cent=1000, daily_cent=1500)
    lim2 = f.set_guardian_limits(
        "guardianB", "kid2", allowed_windows=[(600, 700), (800, 900)],
        single_cent=500, daily_cent=900)
    tw = f.check_time("kid1", 1100, "2026-10-02")
    s1 = f.record_spend("kid1", 800, "2026-10-02", "tx-sub-1")
    s2 = f.record_spend("kid1", 500, "2026-10-03", "tx-sub-2")
    s3 = f.record_spend("kid2", 300, "2026-10-02", "tx-b")
    return lim1, lim2, tw, s1, s2, s3


def main():
    world = tempfile.mkdtemp(prefix="mgp_")
    db = os.path.join(world, "minors_guard.db")

    # -- AC-MGP1: anchor world + pre-close battery + probe family --
    f1 = MinorGuardFace(db_path=db)
    lim1, lim2, tw, s1, s2, s3 = build_anchor_world(f1)
    snap1 = battery(f1)
    counts1 = table_counts(db)
    probes1 = probe_batch(f1)
    ok1 = (lim1["windows"] == ["1080-1200"]
           and lim1["single_cent"] == 1000 and lim1["daily_cent"] == 1500
           and lim2["windows"] == ["0600-0700", "0800-0900"]
           and tw["allowed"] and tw["window"] == "1080-1200"
           and s1["idempotent"] is False and s1["spent_cent"] == 800
           and s2["idempotent"] is False and s2["spent_cent"] == 500
           and s3["idempotent"] is False and s3["spent_cent"] == 300
           and snap1["kid1_d02"] == dump(
               {"resident_id": "kid1", "date": "2026-10-02",
                "spent_cent": 800, "events": ["tx-sub-1"]})
           and snap1["kid1_d03"] == dump(
               {"resident_id": "kid1", "date": "2026-10-03",
                "spent_cent": 500, "events": ["tx-sub-2"]})
           and json.loads(snap1["kidx_d02"])["spent_cent"] == 0
           and json.loads(snap1["adult_d02"])["spent_cent"] == 0
           and len(json.loads(snap1["residents"])) == 4
           and probes1 == [want for want, _ in PROBE_CODES]
           and table_counts(db) == counts1
           and counts1 == {"mg_residents": 4, "mg_limits": 2,
                           "mg_day_spend": 3}
           and adult_passthrough(f1))
    record("AC-MGP1", ok1, "anchor world battery sha16=%s; 8 probes "
           "refused same-code; counts %s; adult pass-through"
           % (sha16(json.dumps(snap1, sort_keys=True)), counts1))
    f1.close()

    # -- AC-MGP2: cross-restart byte-identical battery recovery ------
    f2 = MinorGuardFace(db_path=db)
    snap2 = battery(f2)
    again = battery(f2)
    ok2 = (snap2 == snap1 and again == snap1
           and table_counts(db) == counts1)
    record("AC-MGP2", ok2, "battery replay == pre-close snapshot "
           "byte-identical (sha16=%s); second read self-identical"
           % sha16(json.dumps(snap2, sort_keys=True)))

    # -- AC-MGP3: gate laws survive restart + probe zero side-effect -
    probes2 = probe_batch(f2)
    counts3a = table_counts(db)
    pt2 = adult_passthrough(f2)
    ok3 = (probes2 == probes1 and table_counts(db) == counts3a
           and counts3a == counts1 and pt2)
    record("AC-MGP3", ok3, "8 restart probes refused same codes; "
           "3-table counts constant %s; pass-through alive"
           % counts3a)

    # -- AC-MGP4: post-restart continuation + recompute + new minor --
    r4 = f2.record_spend("kid1", 700, "2026-10-03", "tx-sub-3")
    day3 = f2.day_readout("kid1", "2026-10-03")
    f2.register_resident("kid3", True, "guardianC")
    f2.set_guardian_limits("guardianC", "kid3",
                           allowed_windows=[(540, 660)],
                           single_cent=200, daily_cent=400)
    r4b = f2.record_spend("kid3", 100, "2026-10-04", "tx-c3")
    not_minor = False
    try:
        f2.record_spend("adult1", 100, "2026-10-02", "tx-adult")
    except GuardError as ge:
        not_minor = ge.code == "E_MG_NOT_MINOR"
    ok4 = (r4["idempotent"] is False and r4["spent_cent"] == 1200
           and day3["spent_cent"] == 1200
           and day3["events"] == ["tx-sub-2", "tx-sub-3"]
           and dump(day3) != snap1["kid1_d03"]
           and r4b["idempotent"] is False and r4b["spent_cent"] == 100
           and len(f2.residents_readout()) == 5
           and not_minor
           and table_counts(db) == {"mg_residents": 5, "mg_limits": 3,
                                    "mg_day_spend": 5})
    record("AC-MGP4", ok4, "continuation recomputed 1200/[tx-sub-2,"
           " tx-sub-3] != cached pre-close; kid3 registered+limited"
           "+first spend on reopened instance; adult ledger refused")

    # -- AC-MGP5: frozen history + cross-restart idempotent replay ---
    # Amended same-window (R1883 AC-PN27 precedent): the product's
    # re-gate-first law (AC-W7, R939b/R940) means a replay whose
    # re-gate now exceeds the budget refuses - the conservative
    # fail-closed direction. Idempotent absorption is proven in a
    # re-gate-passing state (kid2 daily 300+300<=900); the kid1
    # replay after the continuation (1200+500>1500) pins the
    # refusal direction instead.
    counts5a = table_counts(db)
    rp = f2.record_spend("kid2", 300, "2026-10-02", "tx-b")
    counts5b = table_counts(db)
    day2b = f2.day_readout("kid2", "2026-10-02")
    conservative = False
    try:
        f2.record_spend("kid1", 500, "2026-10-03", "tx-sub-2")
    except GuardError as ge:
        conservative = ge.code == "E_MG_SPEND_DAILY"
    counts5c = table_counts(db)  # captured after the refusal, before dom
    dom = f2.record_spend("kid1", 300, "2026-10-04", "tx-sub-1")
    day4 = f2.day_readout("kid1", "2026-10-04")
    term2 = battery(f2)
    ok5 = (dump(f2.day_readout("kid1", "2026-10-02")) == snap1["kid1_d02"]
           and rp["idempotent"] is True and rp["spent_cent"] == 300
           and day2b["events"] == ["tx-b"]
           and counts5b == counts5a
           and conservative
           and counts5c == counts5b
           and f2.day_readout("kid1", "2026-10-03")["events"] ==
           ["tx-sub-2", "tx-sub-3"]
           and dom["idempotent"] is False and dom["spent_cent"] == 300
           and day4["events"] == ["tx-sub-1"]
           and table_counts(db)["mg_day_spend"] == 6)
    record("AC-MGP5", ok5, "history bucket frozen == pre-close; tx-b "
           "replay idempotent in re-gate-passing state (rows "
           "absorbed); tx-sub-2 replay refused by re-gate-first law "
           "(AC-W7 conservative direction, zero mutation); same ref "
           "on another date = new row (ref-domain bucket law)")

    # -- AC-MGP6: pure-read law --------------------------------------
    counts6a = table_counts(db)
    b6a = battery(f2)
    b6b = battery(f2)
    rep1 = render_report(f2, ["kid1", "kid2", "kid3", "kidX",
                              "adult1"], "2026-10-03")
    rep2 = render_report(f2, ["kid1", "kid2", "kid3", "kidX",
                              "adult1"], "2026-10-03")
    ok6 = (b6a == b6b and b6a == term2
           and table_counts(db) == counts6a and rep1 == rep2)
    record("AC-MGP6", ok6, "battery double-read byte-identical; "
           "3-table counts constant across the read batch; report "
           "double-run byte-identical (sha16=%s)" % sha16(rep1))

    # -- AC-MGP7: third instance stability + hygiene ------------------
    f2.close()
    f3 = MinorGuardFace(db_path=db)
    snap3 = battery(f3)
    plain = MinorGuardFace()
    plain.register_resident("pkid", True, "pg")
    plain.set_guardian_limits("pg", "pkid", allowed_windows=[(60, 120)],
                              single_cent=100, daily_cent=200)
    plain.record_spend("pkid", 50, "2026-10-02", "ptx-1")
    memmode = (plain.day_readout("pkid", "2026-10-02")["spent_cent"] == 50
               and len(plain.residents_readout()) == 1)
    raw = open(os.path.join(BASE, "minors.py"), "rb").read()
    src_ascii = all(b < 128 for b in raw)
    self_raw = open(os.path.abspath(__file__), "rb").read()
    self_ascii = all(b < 128 for b in self_raw)
    net_free = all(
        ("import " + m) not in self_raw.decode("ascii")
        for m in ("urllib", "requests", "socket", "http"))
    ok7 = (snap3 == term2 and memmode and src_ascii and self_ascii
           and net_free and not os.path.exists(
               os.path.join(ROOT_MARK, "minors_guard.db"))
           and len(RESULTS) == 6)
    record("AC-MGP7", ok7, "third instance == instance-2 terminal "
           "state byte-identical (sha16=%s); default db_path=None "
           "memory mode drift-free; sources pure ASCII; zero-network "
           "imports; world db outside repo" % sha16(json.dumps(snap3,
                                                   sort_keys=True)))
    f3.close()

    failed = [ac for ac, ok in RESULTS if not ok]
    print("")
    print("SUITE %s - %d/%d green" % (
        "PASS" if not failed else "FAIL", len(RESULTS) - len(failed),
        len(RESULTS)), flush=True)
    if failed:
        print("failed: %s" % ", ".join(failed), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
