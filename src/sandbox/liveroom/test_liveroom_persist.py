"""R1933 liveroom risk-control read-face family cross-restart
persistence window (persist-family seat, R1886 lineage; suite-only
round - zero product change). Pre-registered criteria AC-LRP1..LRP7
live in the state/queue/tech.md claim line and were written before
this code existed (honesty law).

World (real product path, zero fixture injection): three sessions
cover every read-face shape - A = closed session with full history
(5 enters, 3 registers, AI-flagged + clean danmaku, two conversions),
B = open session (2 enters, 1 register, 1 danmaku, 1 conversion),
C = open session with zero cohort (honest empty read faces).

Read faces under proof: funnel / transcript / conversion_ledger -
none of the three echoes a timestamp, so every comparison is a
full-envelope dumps(sort_keys=True) byte equality (stronger than a
projection-band face; no clock freezing is needed for read identity,
and no evidence line prints a ts, a temp path or a tx id).

Usage: python test_liveroom_persist.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LEDGER_DIR = os.path.abspath(os.path.join(BASE, "..", "ledger"))
LOBBY_DIR = os.path.abspath(os.path.join(BASE, "..", "lobby"))
REPO_ROOT = os.path.abspath(os.path.join(BASE, "..", "..", ".."))
for _d in (BASE, LEDGER_DIR, LOBBY_DIR):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L          # noqa: E402  (P-47-2b core, reuse law)
import sec_gate as SG       # noqa: E402  (lobby gate, reuse law)
import liveroom as LR       # noqa: E402  (R608 conversion-piece face)

RESULTS = []
SESSIONS = ("s-lrpa", "s-lrpb", "s-lrpc")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def expect_live_error(fn, *codes):
    try:
        fn()
    except LR.LiveRoomError as exc:
        return exc.code in codes, exc.code
    return False, "no-error-raised"


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def build_stack(db_path, cfg):
    led = L.Ledger(db_path, cfg)
    gate = SG.SecGate(cfg["gate"]["forbidden_words"],
                      cfg["gate"]["advisory_ban_words"])
    lf = LR.LiveRoomFace(led, gate, cfg["token"]["disclaimer"],
                         cfg["token"]["ai_label_text"])
    return led, gate, lf


def table_counts(db_path):
    conn = sqlite3.connect(db_path)
    try:
        out = {}
        for tbl in ("live_sessions", "live_cohort", "live_danmaku",
                    "live_conversions"):
            out[tbl] = conn.execute(
                "SELECT COUNT(*) FROM %s" % tbl).fetchone()[0]
        out["spend_tx"] = conn.execute(
            "SELECT COUNT(*) FROM ledger_tx WHERE type = 'spend'"
        ).fetchone()[0]
        return out
    finally:
        conn.close()


def nine_reads(lf):
    out = {}
    for sid in SESSIONS:
        out["funnel:" + sid] = lf.funnel(sid)
        out["transcript:" + sid] = lf.transcript(sid)
        out["conv:" + sid] = lf.conversion_ledger(sid)
    return out


def nine_dumps(lf):
    return {key: dumps(val) for key, val in nine_reads(lf).items()}


def main():
    tmp = tempfile.mkdtemp(prefix="liveroom-lrp-")
    with open(os.path.join(LEDGER_DIR, "config.json"),
              encoding="utf-8") as handle:
        cfg = json.load(handle)
    cfg_bytes_before = open(
        os.path.join(LEDGER_DIR, "config.json"), "rb").read()
    sha_before = {name: sha256_file(path) for name, path in (
        ("liveroom.py", os.path.join(BASE, "liveroom.py")),
        ("ledger.py", os.path.join(LEDGER_DIR, "ledger.py")))}

    disc = cfg["token"]["disclaimer"]
    ai_label = cfg["token"]["ai_label_text"]
    db_path = os.path.join(tmp, "ledger.db")
    led, gate, lf = build_stack(db_path, cfg)

    # -- world: funding, then the three-session real-path spectrum ----
    led.mint_to_pool("pool:reserve", 100000, "SETTLE-LRP", "settlement")
    for who in ("amy", "ben", "cyd"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
    led.adjust([("pool:reserve", "debit", 3000), ("usr:amy", "credit", 3000)],
               "manual:lrp-fund-amy", "suite funding amy")
    led.adjust([("pool:reserve", "debit", 2000), ("usr:ben", "credit", 2000)],
               "manual:lrp-fund-ben", "suite funding ben")
    led.adjust([("pool:reserve", "debit", 2000), ("usr:cyd", "credit", 2000)],
               "manual:lrp-fund-cyd", "suite funding cyd")

    # session A: closed session with the full history chain
    lf.open_session("s-lrpa", "room-a", True, "bigcompute-risk-A")
    for i in range(5):
        lf.viewer_enter("s-lrpa", "anon-a%d" % i)
    lf.viewer_register("s-lrpa", "anon-a0", "amy")
    lf.viewer_register("s-lrpa", "anon-a1", "ben")
    lf.viewer_register("s-lrpa", "anon-a2", "cyd")
    lf.post_danmaku("s-lrpa", "anon-a0", "greetings city crowd",
                    ai_generated=True)
    lf.post_danmaku("s-lrpa", "anon-a1", "hello from ben")
    lf.cart_convert("s-lrpa", "anon-a0", 1990, "order:lrp-a-amy")
    lf.cart_convert("s-lrpa", "anon-a2", 990, "order:lrp-a-cyd")
    lf.close_session("s-lrpa")

    # session B: open session mid-funnel
    lf.open_session("s-lrpb", "room-b", True, "bigcompute-risk-B")
    lf.viewer_enter("s-lrpb", "anon-b0")
    lf.viewer_enter("s-lrpb", "anon-b1")
    lf.viewer_register("s-lrpb", "anon-b0", "amy")
    lf.post_danmaku("s-lrpb", "anon-b0", "open room talk")
    lf.cart_convert("s-lrpb", "anon-b0", 500, "order:lrp-b-amy")

    # session C: open session with zero cohort
    lf.open_session("s-lrpc", "room-c", True, "bigcompute-risk-C")

    pre = nine_dumps(lf)
    bal_amy_0 = led.balance("usr:amy")["balance"]
    bal_cyd_0 = led.balance("usr:cyd")["balance"]

    # -- AC-LRP1 control anchor: world facts + pre-close nine reads ----
    fa = lf.funnel("s-lrpa")
    ok_facts = (fa["entered"] == 5 and fa["registered"] == 3
                and fa["converted"] == 2 and fa["conversion_total"] == 2980
                and fa["room_id"] == "room-a"
                and fa["risk_control_ref"] == "bigcompute-risk-A"
                and fa["attended"] is True and fa["disclaimer"] == disc
                and fa["ai_label_text"] == ai_label
                and bal_amy_0 == 510 and bal_cyd_0 == 1010)
    conn = sqlite3.connect(db_path)
    coh = conn.execute("SELECT COUNT(*),"
                        " SUM(census_avatar_id IS NOT NULL) FROM"
                        " live_cohort WHERE session_id = 's-lrpa'"
                        ).fetchone()
    dm = conn.execute("SELECT COUNT(*), SUM(ai_generated) FROM"
                      " live_danmaku WHERE session_id = 's-lrpa'"
                      ).fetchone()
    conv = conn.execute("SELECT COUNT(*), COALESCE(SUM(price),0) FROM"
                        " live_conversions WHERE session_id = 's-lrpa'"
                        ).fetchone()
    conn.close()
    ok_sql = (coh[0] == 5 and int(coh[1]) == 3 and dm[0] == 2
              and int(dm[1]) == 1 and conv[0] == 2 and int(conv[1]) == 2980)
    lines_a = lf.transcript("s-lrpa")
    ai_lines = [ln for ln in lines_a if "greetings city crowd" in ln]
    ok_spine = (lines_a[0] == disc and lines_a[-1] == disc
                and len(ai_lines) == 1
                and ("[" + ai_label + "]") in ai_lines[0]
                and any(ln.startswith("funnel entered=5 registered=3"
                                      " converted=2 conversion_total=2980")
                        for ln in lines_a))
    rows_a = lf.conversion_ledger("s-lrpa")
    conn = sqlite3.connect(db_path)
    ok_bind = len(rows_a) == 2
    debit_sum = 0
    for r in rows_a:
        ok_bind = ok_bind and set(r) == {"viewer_id", "account_id",
                                         "price", "bound_spend_tx"}
        head = conn.execute("SELECT type FROM ledger_tx WHERE tx_id = ?",
                            (r["bound_spend_tx"],)).fetchone()
        leg = conn.execute(
            "SELECT direction, amount FROM ledger_entries"
            " WHERE tx_id = ? AND account_id = ?",
            (r["bound_spend_tx"], r["account_id"])).fetchone()
        ok_bind = ok_bind and head is not None and head[0] == "spend"
        ok_bind = ok_bind and leg is not None and leg[0] == "debit"
        debit_sum += leg[1] if leg else 0
    conn.close()
    ok_bind = ok_bind and debit_sum == 2980
    ok1 = ok_facts and ok_sql and ok_spine and ok_bind
    record("AC-LRP1", ok1, "pre-close anchor: A funnel entered=%d"
          " registered=%d converted=%d total=%d matches the SQL recount"
          " (%d/%d/%d/%d), transcript spine disclaimer-first+last with the"
          " AI line tagged, conversion ledger %d rows each binding a real"
          " spend debit (bound debit sum %d==total); balances amy=%d"
          " cyd=%d exact"
          % (fa["entered"], fa["registered"], fa["converted"],
             fa["conversion_total"], coh[0], int(coh[1]), conv[0],
             int(conv[1]), len(rows_a), debit_sum, bal_amy_0, bal_cyd_0))

    # -- AC-LRP2 cross-restart nine-face byte identity (core) ---------
    lf.close()
    led.close()
    led2, gate2, lf2 = build_stack(db_path, cfg)
    post = nine_dumps(lf2)
    ok_same = all(post[k] == pre[k] for k in pre)
    again = nine_dumps(lf2)
    ok_self = all(again[k] == post[k] for k in post)
    record("AC-LRP2", ok_same and ok_self, "stack close -> same db + same"
          " cfg bytes reopen: all nine read faces (funnel/transcript/"
          "conversion_ledger x closed/open/empty sessions) replay"
          " dumps==pre-close byte-for-byte (%d/%d) and a second read is"
          " self-identical - derived faces carry zero in-memory drift"
          % (sum(1 for k in pre if post[k] == pre[k]), len(pre)))

    # -- AC-LRP3 risk-control law survival across restart --------------
    counts_0 = table_counts(db_path)
    ok_c1, code_c1 = expect_live_error(
        lambda: lf2.cart_convert("s-lrpa", "anon-a0", 100, "order:late"),
        LR.E_LIVE_CLOSED)
    ok_c2, code_c2 = expect_live_error(
        lambda: lf2.post_danmaku("s-lrpa", "anon-a0", "after close"),
        LR.E_LIVE_CLOSED)
    bal_dup_0 = led2.balance("usr:amy")["balance"]
    ok_dup, code_dup = expect_live_error(
        lambda: lf2.cart_convert("s-lrpb", "anon-b0", 500, "order:dup"),
        LR.E_LIVE_CONV_DUP)
    bal_dup_1 = led2.balance("usr:amy")["balance"]
    ok_res, code_res = expect_live_error(
        lambda: lf2.post_danmaku("s-lrpb", "anon-b1", "anon line"),
        LR.E_LIVE_NOT_RESIDENT)
    ok_unk, code_unk = expect_live_error(
        lambda: lf2.funnel("s-ghost"), LR.E_LIVE_UNKNOWN)
    counts_1 = table_counts(db_path)
    ok3 = (ok_c1 and ok_c2 and ok_dup and ok_res and ok_unk
           and bal_dup_0 == bal_dup_1 and counts_0 == counts_1)
    record("AC-LRP3", ok3, "reopened instance enforces the risk-control"
          " law: closed-session convert/danmaku refused %s/%s, dup"
          " conversion window survives restart %s with zero charge"
          " (%d==%d), anonymous danmaku refused %s, unknown session read"
          " refused %s; probe batch left every table count and the spend"
          " count untouched" % (code_c1, code_c2, code_dup, bal_dup_0,
                               bal_dup_1, code_res, code_unk))

    # -- AC-LRP4 post-restart injection -> open-session recompute ------
    lf2.viewer_enter("s-lrpb", "anon-b2")
    lf2.viewer_register("s-lrpb", "anon-b2", "cyd")
    lf2.post_danmaku("s-lrpb", "anon-b2", "post restart hello")
    lf2.cart_convert("s-lrpb", "anon-b2", 990, "order:lrp-b-cyd")
    fb = lf2.funnel("s-lrpb")
    lines_b = lf2.transcript("s-lrpb")
    rows_b = lf2.conversion_ledger("s-lrpb")
    bal_cyd_1 = led2.balance("usr:cyd")["balance"]
    counts_2 = table_counts(db_path)
    ok_recompute = (fb["entered"] == 3 and fb["registered"] == 2
                    and fb["converted"] == 2
                    and fb["conversion_total"] == 1490
                    and len(lines_b) == 6 and len(rows_b) == 2
                    and bal_cyd_1 == bal_cyd_0 - 990
                    and counts_2["spend_tx"] == counts_1["spend_tx"] + 1
                    and dumps(fb) != pre["funnel:s-lrpb"]
                    and dumps(lines_b) != pre["transcript:s-lrpb"]
                    and dumps(rows_b) != pre["conv:s-lrpb"])
    record("AC-LRP4", ok_recompute, "restarted instance accepts new real"
          " path on the open session: enter+register+danmaku+convert"
          " recompute the B faces live (entered=%d registered=%d"
          " converted=%d total=%d, transcript %d lines, ledger %d rows)"
          " differing from the pre-close snapshots, spend count +1 and"
          " cyd balance %d==%d-990 exact"
          % (fb["entered"], fb["registered"], fb["converted"],
             fb["conversion_total"], len(lines_b), len(rows_b),
             bal_cyd_1, bal_cyd_0))

    # -- AC-LRP5 untouched faces stay byte-frozen -----------------------
    post2 = nine_dumps(lf2)
    ok_a = all(post2[k] == pre[k] for k in pre if k.startswith(
        ("funnel:s-lrpa", "transcript:s-lrpa", "conv:s-lrpa")))
    ok_c = all(post2[k] == pre[k] for k in pre if k.startswith(
        ("funnel:s-lrpc", "transcript:s-lrpc", "conv:s-lrpc")))
    fc = lf2.funnel("s-lrpc")
    lines_c = lf2.transcript("s-lrpc")
    ok_c_shape = (fc["entered"] == 0 and fc["registered"] == 0
                  and fc["converted"] == 0 and fc["conversion_total"] == 0
                  and lines_c[0] == disc and lines_c[-1] == disc
                  and len(lines_c) == 4
                  and lf2.conversion_ledger("s-lrpc") == [])
    record("AC-LRP5", ok_a and ok_c and ok_c_shape,
          "after the injection the closed-session A faces and the empty"
          " session C faces still replay == pre-close snapshots"
          " byte-for-byte (immutable rows + session isolation); C keeps"
          " the honest empty spine (%d lines, disclaimer first+last,"
          " zero danmaku, empty conversion ledger)"
          % len(lines_c))

    # -- AC-LRP6 third instance / double-restart stability --------------
    final2 = nine_dumps(lf2)
    lf2.close()
    led2.close()
    led3, gate3, lf3 = build_stack(db_path, cfg)
    post3 = nine_dumps(lf3)
    ok_i3 = all(post3[k] == final2[k] for k in final2)
    ok_orig = all(post3[k] == pre[k] for k in pre if k.startswith(
        ("funnel:s-lrpa", "transcript:s-lrpa", "conv:s-lrpa",
         "funnel:s-lrpc", "transcript:s-lrpc", "conv:s-lrpc")))
    record("AC-LRP6", ok_i3 and ok_orig, "second restart: instance three"
          " replays all nine faces == instance-two final state"
          " byte-for-byte (%d/%d) while the A/C faces still equal the"
          " original pre-close snapshots (restart x new data double"
          " burden, zero drift)"
          % (sum(1 for k in final2 if post3[k] == final2[k]),
             len(final2)))

    # -- AC-LRP7 pure-read law + hygiene --------------------------------
    counts_3 = table_counts(db_path)
    for _ in range(2):
        nine_reads(lf3)  # read battery, zero writes expected
    counts_4 = table_counts(db_path)
    ok_pure = counts_3 == counts_4
    sha_after = {name: sha256_file(path) for name, path in (
        ("liveroom.py", os.path.join(BASE, "liveroom.py")),
        ("ledger.py", os.path.join(LEDGER_DIR, "ledger.py")))}
    ok_sha = sha_after == sha_before
    cfg_bytes_after = open(
        os.path.join(LEDGER_DIR, "config.json"), "rb").read()
    ok_cfg = cfg_bytes_before == cfg_bytes_after
    src = open(os.path.join(BASE, "test_liveroom_persist.py"),
               encoding="utf-8").read()
    non_ascii = sum(1 for ch in src if ord(ch) > 127)
    import_lines = [ln.strip() for ln in src.splitlines()
                    if ln.strip().startswith("import ")
                    or ln.strip().startswith("from ")]
    net_imports = [ln for ln in import_lines
                   if any(w in ln for w in ("socket", "http", "urllib",
                                            "requests"))]
    ok_world = not tmp.startswith(REPO_ROOT)
    registry = open(os.path.join(
        os.path.dirname(BASE), "reconcile_all.py"), encoding="utf-8").read()
    ok_reg = "test_liveroom_persist.py" in registry
    ok7 = (ok_pure and ok_sha and ok_cfg and non_ascii == 0
           and not net_imports and ok_reg)
    record("AC-LRP7", ok7, "read battery leaves all four liveroom tables"
          " and the spend count untouched; product shas unchanged"
          " (liveroom.py/ledger.py, suite-only round); shipped config"
          " bytes unchanged; suite source pure ascii, network"
          " imports=%s; SUITES registry row wired=%s; world tmp outside"
          " the repo=%s"
          % (net_imports, ok_reg, ok_world))

    lf3.close()
    led3.close()
    fail = sum(1 for _, ok in RESULTS if not ok)
    extra = (len(RESULTS) == 7)
    print("SUITE %s %d/%d%s" % ("PASS" if fail == 0 and extra else "FAIL",
                                len(RESULTS) - fail, len(RESULTS),
                                "" if extra else " (criteria drift!)"),
          flush=True)
    sys.exit(0 if fail == 0 and extra else 2)


if __name__ == "__main__":
    main()
