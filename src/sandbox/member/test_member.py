"""Acceptance suite for the membership entitlement sandbox (P-47-5b).

Asserts the pre-registered criteria AC-M1..AC-M16 from
docs/spec/membership-spec.md section 1 (criteria were registered before
any implementation; honesty law). One PASS/FAIL line per criterion with
evidence; the process exits non-zero on any FAIL.

Provenance (takeover, honesty law): config.json / catalog.py /
member.py on disk were drafted by the dead 17:34 beat round whose
self-check flagged two lock-nesting deadlocks and a commit/rollback
hazard; this takeover re-audited every lock path and commit boundary,
found the flagged flaws already absent in the final on-disk text (the
author's last write evidently landed the fix), fixed two residual bugs
it found itself (voucher pick by id-hash order; renewal start behind
now), added the two additive pay read faces activation needs
(grant_row / grants_for grant_id), and wrote sweep.py / reconcile.py /
this suite.

Usage: python test_member.py
"""

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
_LOBBY = os.path.normpath(os.path.join(BASE, "..", "lobby"))
_PAY = os.path.normpath(os.path.join(BASE, "..", "pay"))
_LEDGER = os.path.normpath(os.path.join(BASE, "..", "ledger"))
for _p in (_LOBBY, _PAY, _LEDGER, BASE):
    # deterministic order: BASE, _LEDGER, _PAY, _LOBBY - member modules
    # win over same-named pay modules; sec_gate resolves to the lobby
    # product, orders/ledger to the pay/ledger products (same contract
    # as member.py; the 17:34 round's lesson about path order applies)
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import catalog as C                              # noqa: E402 (this package)
import reconcile as RC                           # noqa: E402 (this package)
# reconcile MUST bind before member: importing member pulls in the pay
# orders product whose own path dance re-orders sys.path with PAY first,
# which would shadow this package's same-named reconcile (the 17:34
# round's path-order lesson, recurring at the cross-piece level)
import member as M                               # noqa: E402 (this package)
import orders as pay_orders                      # noqa: E402 (pay product)
import adapters as A                             # noqa: E402 (pay product)
from ledger import Ledger, LedgerError           # noqa: E402 (ledger product)
from sec_gate import GateOfflineError            # noqa: E402 (lobby product)
import store as lobby_store                      # noqa: E402 (lobby product)

RESULTS = []
FIAT_TOKEN_SUBSTRINGS = ("price", "amount", "cent", "fee", "yuan", "rmb",
                         "cny", "token", "coin")


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def expect_code(fn, *codes):
    try:
        fn()
    except (M.MemberError, pay_orders.PayError, LedgerError) as exc:
        return exc.code in codes, "%s (detail=%s)" % (exc.code, exc.detail or "-")
    except GateOfflineError as exc:
        return "E_GATE_OFFLINE" in codes, "E_GATE_OFFLINE: %s" % exc
    return False, "no-error-raised"


def raw_sql(db_path, sql, args=()):
    """Execute raw SQL as a bare connection (foreign keys OFF - the
    tampering posture); return None on success or the error string."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(sql, args)
        conn.commit()
        return None
    except sqlite3.Error as exc:
        return str(exc)
    finally:
        conn.close()


def db_query(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql, args).fetchall()
    finally:
        conn.close()


def db_exec(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(sql, args)
        conn.commit()
    finally:
        conn.close()


def run_cli(script, args_list):
    proc = subprocess.run([sys.executable, os.path.join(BASE, script)]
                          + args_list, capture_output=True, text=True,
                          encoding="utf-8", timeout=180, cwd=BASE)
    return (proc.returncode, (proc.stdout or "").strip(),
            (proc.stderr or "").strip())


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def tier_products(pcfg):
    """Temporary pay price rows whose entitlement keys are the member
    catalog product keys (sandbox dock face; real tier price rows are a
    [needs-CEO] approval face and are never recorded here)."""
    pcfg["products"]["tier_experience"] = {
        "channel": "virtual", "price_cent": 1990, "share_tokens": 0,
        "entitlement": "tier:experience",
        "copy": "sandbox dock product: experience tier"}
    pcfg["products"]["tier_mayor"] = {
        "channel": "virtual", "price_cent": 4990, "share_tokens": 0,
        "entitlement": "tier:mayor",
        "copy": "sandbox dock product: mayor tier"}
    pcfg["products"]["tier_cocreator"] = {
        "channel": "virtual", "price_cent": 9900, "share_tokens": 0,
        "entitlement": "tier:cocreator",
        "copy": "sandbox dock product: cocreator tier"}
    return pcfg


def build(mutate_member=None, mutate_pay=tier_products):
    tmp = tempfile.mkdtemp(prefix="member-ac-")
    mcfg = load_json(os.path.join(BASE, "config.json"))
    if mutate_member:
        mcfg = mutate_member(json.loads(json.dumps(mcfg)))
    mcfg_path = os.path.join(tmp, "member-config.json")
    with open(mcfg_path, "w", encoding="utf-8") as handle:
        json.dump(mcfg, handle, ensure_ascii=False, indent=2)
    pcfg = load_json(os.path.join(_PAY, "config.json"))
    if mutate_pay:
        pcfg = mutate_pay(json.loads(json.dumps(pcfg)))
    pcfg_path = os.path.join(tmp, "pay-config.json")
    with open(pcfg_path, "w", encoding="utf-8") as handle:
        json.dump(pcfg, handle, ensure_ascii=False, indent=2)
    led_cfg = load_json(os.path.join(_LEDGER, "config.json"))
    events = lobby_store.EventStore(os.path.join(tmp, "events.db"))
    led = Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
    led.mint_to_pool("pool:share", 1000000, "SETTLE-MEMBER-1", "settlement")
    pay = pay_orders.PayOrders(pcfg, os.path.join(tmp, "pay.db"), events, led)
    store = M.MemberStore(mcfg, os.path.join(tmp, "member.db"), pay)
    return {"tmp": tmp, "mcfg": mcfg, "mcfg_path": mcfg_path,
            "pcfg_path": pcfg_path, "events": events, "led": led,
            "pay": pay, "chans": A.from_config(pcfg), "store": store,
            "member_db": os.path.join(tmp, "member.db"),
            "pay_db": os.path.join(tmp, "pay.db"),
            "ledger_db": os.path.join(tmp, "ledger.db"),
            "events_db": os.path.join(tmp, "events.db")}


def tear(world):
    world["store"].close()
    world["pay"].close()
    world["led"].close()
    shutil.rmtree(world["tmp"], ignore_errors=True)


def happy(world, product_id, avatar, nonce):
    """create -> place -> valid callback -> granted; return (order_id,
    grant_id) - the grant id rides the additive pay read face."""
    resp = world["pay"].create_order(product_id, avatar)
    oid = resp["order_id"]
    world["pay"].place_order(oid)
    amount = world["pay"].order_detail(oid)["amount_cent"]
    cb = world["chans"][resp["channel"]].make_callback(oid, amount, nonce)
    world["pay"].handle_callback(cb)
    items = world["pay"].grants_for(avatar)["items"]
    return oid, items[-1]["grant_id"]


def period_of(world, avatar, no=1):
    return world["store"].balance_face(avatar)["periods"][no - 1]["period_id"]


def main():
    w = build()
    try:
        store, pay = w["store"], w["pay"]
        mdb, pdb, ldb, edb = (w["member_db"], w["pay_db"], w["ledger_db"],
                              w["events_db"])
        mcfg = w["mcfg"]
        gate_word = str(mcfg["gate"]["forbidden_words"][0])
        ban_word = str(mcfg["copy_ban_words"][0])
        far = "2030-01-01T00:00:00Z"

        # ---- AC-M1: catalog single source + bad-config refusals ------
        bads = []
        for name, mutate in (
                ("no-tiers", lambda c: c.pop("tiers")),
                ("negative-credits",
                 lambda c: c["tiers"]["experience"].__setitem__(
                     "monthly_credits", -1)),
                ("unknown-priv",
                 lambda c: c["tiers"]["experience"].__setitem__(
                     "privileges", ["magic_wand"])),
                ("no-copy",
                 lambda c: c["tiers"]["experience"].__setitem__("copy", "")),
                ("no-disclaimer",
                 lambda c: c["compliance"].pop("disclaimer"))):
            cfg = json.loads(json.dumps(mcfg))
            try:
                mutate(cfg)
                C.Catalog.from_config(cfg)
                bads.append(name + ":accepted")
            except GateOfflineError:
                bads.append(name + ":refused")
        oid_e, gid_e = happy(w, "tier_experience", "AV-101", "n-e1")
        r101 = store.activate(gid_e, "AV-101",
                              client_hints={"tier": "cocreator",
                                            "privileges": ["private_room"]})
        record("AC-M1", all(b.endswith(":refused") for b in bads)
               and r101["tier"] == "experience",
               "bad-configs %s; client tier claim ignored (activated tier=%s)"
               % (",".join(bads), r101["tier"]))

        # ---- AC-M2: activation idempotence + grant-source truth -------
        oid_m, gid_m = happy(w, "tier_mayor", "AV-102", "n-m1")
        r1 = store.activate(gid_m, "AV-102")
        grants_before = db_query(
            mdb, "SELECT COUNT(*) FROM member_credit_events WHERE"
            " reason = 'grant' AND ref_type = 'activation'")[0][0]
        r2 = store.activate(gid_m, "AV-102")
        grants_after = db_query(
            mdb, "SELECT COUNT(*) FROM member_credit_events WHERE"
            " reason = 'grant' AND ref_type = 'activation'")[0][0]
        # renewal = next-cycle new order (spec section 0); the bucket
        # only opens when the first order reaches its terminal closed
        # state via the legal granted->closed edge (refund-close face;
        # the refund policy itself stays [needs-CEO], AC-MP4 - the test
        # only walks the machine's own legal edge, no policy is invented)
        db_exec(pdb, "UPDATE pay_orders SET status = 'closed'"
                " WHERE order_id = ?", (oid_m,))
        oid_m2, gid_m2 = happy(w, "tier_mayor", "AV-102", "n-m2")
        r3 = store.activate(gid_m2, "AV-102")
        ok_fake, ev_fake = expect_code(
            lambda: store.activate("FORGED-GRANT-ID", "AV-102"),
            M.E_BAD_GRANT_SOURCE)
        ok_owner, ev_owner = expect_code(
            lambda: store.activate(gid_m, "AV-999"), M.E_BAD_GRANT_SOURCE)
        record("AC-M2",
               r1["tier"] == "mayor" and r1["vouchers_opened"]
               and r2["period_id"] == r1["period_id"] and r2["idempotent"]
               and grants_after == grants_before
               and r3["period_no"] == 2
               and r3["start_utc"] == r1["end_utc"]
               and ok_fake and ok_owner,
               "mayor opened v=%s; replay same-period=%s regrant=%d;"
               " stack p2 start==p1.end=%s; forged=%s owner-mismatch=%s"
               % (r1["vouchers_opened"], r2["idempotent"],
                  grants_after - grants_before,
                  r3["start_utc"] == r1["end_utc"], ok_fake, ok_owner))

        # ---- AC-M3 setup: birth-cert-only paid product ----------------
        oid_p, gid_p = happy(w, "pack_compute_19_9", "AV-104", "n-p1")
        rp = store.activate(gid_p, "AV-104")
        bf104 = store.birth_cert_face("AV-104")
        ok_nobind, ev_nobind = expect_code(
            lambda: store.activate(gid_p, ""), M.E_NO_BINDING)

        # ---- AC-M13 measured around the AV-103 flow -------------------
        # (anchored AFTER happy(): the pay.success event at grant time is
        # the pay domain's own AC-Y14 stream - the member domain must add
        # zero rows on top of it)
        oid_c, gid_c = happy(w, "tier_cocreator", "AV-103", "n-c1")
        ev_before = db_query(edb, "SELECT COUNT(*) FROM events")[0][0]
        rc1 = store.activate(gid_c, "AV-103")
        store.consume_credits("AV-103", 7, ref="svc-1",
                              ref_type="service_ticket")
        store.consume_credits("AV-103", 23, ref="svc-2",
                               ref_type="service_ticket")
        store.refund_credits("AV-103", 5, rc1["period_id"], ref="svc-1",
                             ref_type="service_ticket")
        ev_after = db_query(edb, "SELECT COUNT(*) FROM events")[0][0]
        audit_kinds = {r[0] for r in db_query(
            mdb, "SELECT DISTINCT kind FROM member_audit")}
        record("AC-M13", ev_before == ev_after
               and {"period", "credits", "voucher"} <= audit_kinds,
               "public-stream rows before=%d after=%d (zero double"
               " writes); audit kinds=%s"
               % (ev_before, ev_after, sorted(audit_kinds)))

        # ---- AC-M4: credit conservation three-point boundary ----------
        # journal so far: +30 grant, -7, -23 consume, +5 refund => 5
        bal = store.balance_face("AV-103")["periods"][0]["balance"]
        ok_over, ev_over = expect_code(
            lambda: store.consume_credits("AV-103", 9999), M.E_NO_CREDITS)
        bal_over = store.balance_face("AV-103")["periods"][0]["balance"]
        ok_refcap, ev_refcap = expect_code(
            lambda: store.refund_credits("AV-103", 26, rc1["period_id"]),
            M.E_REFUND_EXCEEDS)
        store.consume_credits("AV-103", 5, ref="svc-3",
                               ref_type="service_ticket")
        bal_zero = store.balance_face("AV-103")["periods"][0]["balance"]
        ok_zero, ev_zero = expect_code(
            lambda: store.consume_credits("AV-103", 1), M.E_NO_CREDITS)
        ok_noperiod, ev_noperiod = expect_code(
            lambda: store.consume_credits("AV-105", 1), M.E_PERIOD_EXPIRED)
        sums = db_query(
            mdb, "SELECT reason, SUM(delta) FROM member_credit_events"
            " WHERE period_id = ? GROUP BY reason", (rc1["period_id"],))
        total = sum(r[1] for r in sums)
        record("AC-M4", bal == 5 and ok_over and bal_over == 5 and ok_refcap
               and bal_zero == 0 and ok_zero and ok_noperiod and total == 0,
               "30-7-23+5=balance %d; overdraw refused=%s balance-untouched"
               "=%s; refund-cap refused=%s; drain->%d; zero-draw refused=%s;"
               " no-period refused=%s; journal sums=%s"
               % (bal, ok_over, bal_over == 5, ok_refcap, bal_zero, ok_zero,
                  ok_noperiod, dict(sums)))

        # ---- AC-M5: server-side privilege authority --------------------
        privs = store.privileges_for(
            "AV-101", client_hints={"tier": "cocreator",
                                    "privileges": ["private_room"]})
        ok_hint6, ev_hint6 = expect_code(
            lambda: store.has_privilege("AV-101", "chat_highlight",
                                        client_hints={"tier": "mayor"}),
            M.E_TIER_REQUIRED)
        record("AC-M5", privs["privileges"] == ["basic_badge",
                                                "emoji_pack_standard"]
               and "private_room" not in privs["privileges"] and ok_hint6,
               "forged client tier/privileges ignored (got %s); forged"
               " privilege claim refused=%s"
               % (privs["privileges"], ok_hint6))

        # ---- AC-M6: tier-match enforcement ------------------------------
        ok_low, ev_low = expect_code(
            lambda: store.has_privilege("AV-101", "priority_queue"),
            M.E_TIER_REQUIRED)
        ok_none, ev_none = expect_code(
            lambda: store.has_privilege("AV-105", "chat_highlight"),
            M.E_NO_ACTIVE_PERIOD)
        hi = store.has_privilege("AV-102", "chat_highlight")
        record("AC-M6", ok_low and ok_none and hi["granted"]
               and hi["tier"] == "mayor",
               "experience->cocreator privilege refused=%s; no-period"
               " refused=%s; mayor chat_highlight granted tier=%s"
               % (ok_low, ok_none, hi["tier"]))

        # ---- AC-M7: member text gate + unwired-gate refusal ------------
        ok_gate, ev_gate = expect_code(
            lambda: store.set_voucher_text("AV-102", "building_naming",
                                            "bad " + gate_word),
            M.E_CONTENT_REJECTED)
        vtext = db_query(
            mdb, "SELECT demand_text FROM member_vouchers WHERE"
            " census_avatar_id = 'AV-102' AND voucher_type ="
            " 'building_naming'")[0][0]
        rtext = store.set_voucher_text("AV-102", "building_naming",
                                      "tower one naming")
        rc_ready, out_ready, err_ready = run_cli(
            "member.py", ["--config", w["mcfg_path"], "--db",
                          os.path.join(w["tmp"], "cli-member.db"),
                          "--pay-config", w["pcfg_path"], "--pay-db",
                          os.path.join(w["tmp"], "cli-pay.db"),
                          "--events-db", os.path.join(w["tmp"], "cli-ev.db"),
                          "--ledger-db", os.path.join(w["tmp"], "cli-led.db"),
                          "--ledger-config",
                          os.path.join(_LEDGER, "config.json")])
        nogate = json.loads(json.dumps(mcfg))
        nogate.pop("gate")
        nogate_path = os.path.join(w["tmp"], "nogate.json")
        with open(nogate_path, "w", encoding="utf-8") as handle:
            json.dump(nogate, handle, ensure_ascii=False)
        rc_nogate, out_nogate, err_nogate = run_cli(
            "member.py", ["--config", nogate_path, "--db",
                          os.path.join(w["tmp"], "ng-member.db"),
                          "--pay-config", w["pcfg_path"], "--pay-db",
                          os.path.join(w["tmp"], "ng-pay.db"),
                          "--events-db", os.path.join(w["tmp"], "ng-ev.db"),
                          "--ledger-db", os.path.join(w["tmp"], "ng-led.db"),
                          "--ledger-config",
                          os.path.join(_LEDGER, "config.json")])
        record("AC-M7", ok_gate and vtext is None and rtext["demand_text_set"]
               and rc_ready == 0 and rc_nogate == 2,
               "gate hit refused=%s zero-writes (text=%s); clean text set;"
               " readiness rc=%d; unwired gate rc=%d (%s)"
               % (ok_gate, vtext, rc_ready, rc_nogate,
                  (err_nogate or out_nogate)[:60]))

        # ---- AC-M8: AIGC marker faces -----------------------------------
        comp = store.companion_face("AV-102",
                                    client_hints={"ai_generated": 0})
        record("AC-M8", rp["ai_generated"] == 0 and comp["ai_generated"] == 1
               and comp.get("ai_label") == mcfg["compliance"]["ai_label"]
               and rc1["ai_generated"] == 0,
               "machine faces ai_generated=0 (activation=%d); AI copy face"
               " ai_generated=%d label=%s; client 0-forgery ignored"
               % (rc1["ai_generated"], comp["ai_generated"],
                  comp.get("ai_label")))

        # ---- AC-M9: resident non-advisory disclaimer --------------------
        faces = [rp, store.privileges_for("AV-101"),
                 store.balance_face("AV-103")]
        ok_disc = all(f.get("disclaimer") == mcfg["compliance"]["disclaimer"]
                     and f.get("persistent") for f in faces)
        record("AC-M9", ok_disc,
               "disclaimer resident on %d sampled faces, persistent=%s"
               % (len(faces), all(f.get("persistent") for f in faces)))

        # ---- AC-M10: zero fiat fields ------------------------------------
        hits = []
        for (table,) in db_query(
                mdb, "SELECT name FROM sqlite_master WHERE type = 'table'"
                " AND name NOT LIKE 'sqlite_%'"):
            for row in db_query(mdb, "PRAGMA table_info(%s)" % table):
                low = str(row[1]).lower()
                if any(s in low for s in FIAT_TOKEN_SUBSTRINGS):
                    hits.append("%s.%s" % (table, row[1]))
        err_fiat = raw_sql(
            mdb, "INSERT INTO member_periods (price_cent) VALUES (1)")
        record("AC-M10", not hits and err_fiat
               and ("no column named" in err_fiat
                    or "no such column" in err_fiat),
               "fiat/token-named columns=%s; raw fiat-column inject"
               " refused=%s" % (hits or "none", err_fiat))

        # ---- AC-M11: quota/token two-domain isolation --------------------
        member_tables = {r[0] for r in db_query(
            mdb, "SELECT name FROM sqlite_master WHERE type = 'table'")}
        ledger_tables = {r[0] for r in db_query(
            ldb, "SELECT name FROM sqlite_master WHERE type = 'table'")}
        quota_hits = []
        for table in ledger_tables:
            for row in db_query(ldb, "PRAGMA table_info(%s)" % table):
                low = str(row[1]).lower()
                if any(s in low for s in ("credit", "quota", "voucher")):
                    quota_hits.append("%s.%s" % (table, row[1]))
        err_token = raw_sql(mdb, "INSERT INTO ledger_entries VALUES (1)")
        err_quota = raw_sql(ldb, "INSERT INTO member_periods VALUES (1)")
        record("AC-M11",
               not any(t.startswith("ledger") for t in member_tables)
               and not any(t.startswith("member") for t in ledger_tables)
               and not quota_hits
               and err_token and "no such table" in err_token
               and err_quota and "no such table" in err_quota,
               "member db has zero ledger tables; ledger db has zero member"
               " tables; ledger quota-named columns=%s; cross-domain raw"
               " writes both refused (%s / %s)"
               % (quota_hits or "none",
                  (err_token or "")[:40], (err_quota or "")[:40]))

        # ---- AC-M16 (part): voucher law on the shared world --------------
        used102 = store.use_voucher("AV-102", "building_naming")
        ok_dup = raw_sql(
            mdb, "INSERT INTO member_vouchers (voucher_id,"
            " census_avatar_id, period_id, voucher_type, status) VALUES"
            " ('DUP-V', 'AV-102', ?, 'building_naming', 'unused')",
            (r1["period_id"],))
        ok_unauth, ev_unauth = expect_code(
            lambda: store.set_voucher_text("AV-101", "building_naming", "x"),
            M.E_TIER_REQUIRED)
        ok_nov, ev_nov = expect_code(
            lambda: store.set_voucher_text("AV-105", "building_naming", "x"),
            M.E_NO_ACTIVE_PERIOD)
        record("AC-M16", used102["status"] == "used" and ok_dup
               and "UNIQUE" in ok_dup and ok_unauth and ok_nov,
               "use=%s; duplicate voucher UNIQUE-refused=%s; experience-tier"
               " voucher request refused=%s; no-period voucher request"
               " refused=%s (reuse/expiry legs on world two)"
               % (used102["status"], "UNIQUE" in (ok_dup or ""), ok_unauth,
                  ok_nov))

        # ---- AC-M12: lifecycle state machine + idempotent sweep ---------
        err_born = raw_sql(
            mdb, "INSERT INTO member_periods (period_id, census_avatar_id,"
            " product_id, tier, period_no, start_utc, end_utc, status,"
            " source_grant_id) VALUES ('X-P', 'AV-900', 'tier:mayor',"
            " 'mayor', 9, '2026-09-24T00:00:00Z', '2026-10-24T00:00:00Z',"
            " 'expired', 'X-G')")
        err_vback = raw_sql(
            mdb, "UPDATE member_vouchers SET status = 'unused' WHERE"
            " status = 'used'")
        n1 = store.sweep_expired(now=far)
        journal_before = db_query(
            mdb, "SELECT COUNT(*) FROM member_credit_events")[0][0]
        n2 = store.sweep_expired(now=far)
        journal_after = db_query(
            mdb, "SELECT COUNT(*) FROM member_credit_events")[0][0]
        err_pback = raw_sql(
            mdb, "UPDATE member_periods SET status = 'active' WHERE"
            " status = 'expired'")
        expired_rows = db_query(
            mdb, "SELECT COUNT(*) FROM member_periods WHERE"
            " status = 'expired'")[0][0]
        expire_events = db_query(
            mdb, "SELECT COUNT(*) FROM member_credit_events WHERE"
            " reason = 'expire'")[0][0]
        expire_audits = db_query(
            mdb, "SELECT COUNT(*) FROM member_audit WHERE"
            " kind = 'expire'")[0][0]
        priv102 = store.privileges_for("AV-102")
        bal103 = store.balance_face("AV-103")["periods"][0]["balance"]
        record("AC-M12", "E_BAD_TRANSITION" in (err_born or "")
               and "E_BAD_TRANSITION" in (err_vback or "")
               and "E_BAD_TRANSITION" in (err_pback or "")
               and n1 == 4 and n2 == 0
               and journal_after == journal_before
               and expired_rows == 4 and expire_events == 3
               and expire_audits == 4 and not priv102["active"]
               and bal103 == 0,
               "born-expired/rollback REJ=%s/%s/%s; sweep expired=%d re-run=%d"
               " journal-stable=%s; expire events=%d (AV-103 balance already"
               " 0 - nothing to forfeit) audits=%d; post-sweep active=%s"
               " balance103=%d"
               % ("E_BAD_TRANSITION" in (err_born or ""),
                  "E_BAD_TRANSITION" in (err_vback or ""),
                  "E_BAD_TRANSITION" in (err_pback or ""), n1, n2,
                  journal_after == journal_before, expire_events,
                  expire_audits, priv102["active"], bal103))

        # ---- AC-M3 (close): permanent birth cert survives expiry ---------
        bf101 = store.birth_cert_face("AV-101")
        grants101 = pay.grants_for("AV-101")
        record("AC-M3", rp["birth_cert"] and rp["permanent"] and rp["tier"] is None
               and bf104["birth_cert"] and bf104["member_domain_marker"]
               and ok_nobind and bf101["birth_cert"] and bf101["permanent"]
               and grants101["items"] and not priv102["active"],
               "paid non-tier product birth-cert=%s permanent=%s;"
               " no-binding refused=%s; after tier expiry birth-cert=%s"
               " marker=%s judgement-source items=%d (privileges closed=%s)"
               % (rp["birth_cert"], rp["permanent"], ok_nobind,
                  bf101["birth_cert"], bf101["member_domain_marker"],
                  len(grants101["items"]), not priv102["active"]))

        # ---- AC-M14: reconcile six checks, clean + tamper families -------
        fails_clean = RC.run_checks(mdb, pdb, ldb, mcfg, now=far)
        rc0, out0, _ = run_cli(
            "reconcile.py", ["--member-db", mdb, "--pay-db", pdb,
                             "--ledger-db", ldb, "--config", w["mcfg_path"],
                             "--now", far])
        record("AC-M14", not fails_clean and rc0 == 0,
               "clean world: findings=%s cli-rc=%d (%s)"
               % (fails_clean or "none", rc0, out0.splitlines()[0][:60]
                  if out0 else "-"))
    finally:
        tear(w)

    # ---- world two: voucher lifecycle legs + tamper injections ----------
    w2 = build()
    try:
        store2, mdb2, pdb2, ldb2 = (w2["store"], w2["member_db"],
                                   w2["pay_db"], w2["ledger_db"])
        mcfg2 = w2["mcfg"]
        far = "2030-01-01T00:00:00Z"
        _, g201 = happy(w2, "tier_mayor", "AV-201", "n-w1")
        _, g202 = happy(w2, "tier_experience", "AV-202", "n-w2")
        _, g204 = happy(w2, "tier_mayor", "AV-204", "n-w4")
        r201 = store2.activate(g201, "AV-201")
        store2.activate(g202, "AV-202")
        store2.activate(g204, "AV-204")
        store2.set_voucher_text("AV-201", "building_naming", "harbor gate")
        used = store2.use_voucher("AV-201", "building_naming")
        ok_reuse, ev_reuse = expect_code(
            lambda: store2.use_voucher("AV-201", "building_naming"),
            M.E_VOUCHER_USED)
        ok_nov2, ev_nov2 = expect_code(
            lambda: store2.use_voucher("AV-203", "building_naming"),
            M.E_NO_ACTIVE_PERIOD)
        rc_sweep, out_sweep, err_sweep = run_cli(
            "sweep.py", ["--config", w2["mcfg_path"], "--db", mdb2,
                         "--pay-config", w2["pcfg_path"], "--pay-db", pdb2,
                         "--events-db", w2["events_db"], "--ledger-db", ldb2,
                         "--ledger-config",
                         os.path.join(_LEDGER, "config.json"), "--now", far])
        ok_exp, ev_exp = expect_code(
            lambda: store2.use_voucher("AV-204", "building_naming"),
            M.E_VOUCHER_USED)
        v204 = db_query(
            mdb2, "SELECT status FROM member_vouchers WHERE"
            " census_avatar_id = 'AV-204'")[0][0]
        exp_audit = db_query(
            mdb2, "SELECT COUNT(*) FROM member_audit WHERE"
            " kind = 'voucher' AND detail LIKE '%expired%'")[0][0]
        record("AC-M16", used["status"] == "used" and ok_reuse and ok_nov2
               and ok_exp and v204 == "expired" and exp_audit >= 1
               and rc_sweep == 0,
               "use=%s; re-use refused=%s; no-voucher avatar refused=%s;"
               " expired-with-period refused=%s (status=%s, audit rows=%d);"
               " sweep cli rc=%d out=%s"
               % (used["status"], ok_reuse, ok_nov2, ok_exp, v204,
                  exp_audit, rc_sweep, (out_sweep or err_sweep)[:40]))

        # tamper families (AC-M14 legs): each injection -> named check
        def tamper(tag, expected, sql, args=()):
            err = raw_sql(mdb2, sql, args)
            if err is not None:
                record("AC-M14", False,
                       "%s injection failed to land: %s" % (tag, err))
                return
            fails = RC.run_checks(mdb2, pdb2, ldb2, mcfg2, now=far)
            hit = any(f.startswith(expected + ":") for f in fails)
            record("AC-M14", hit,
                   "%s -> %s" % (tag,
                                 next((f for f in fails
                                       if f.startswith(expected + ":")),
                                       "no finding")))

        pid202 = period_of(w2, "AV-202")
        tamper("fake-period", "check1",
               "INSERT INTO member_periods (period_id, census_avatar_id,"
               " product_id, tier, period_no, start_utc, end_utc, status,"
               " source_grant_id) VALUES ('FAKE-PERIOD-1', 'AV-950',"
               " 'tier:experience', 'experience', 9,"
               " '2030-06-01T00:00:00Z', '2030-07-01T00:00:00Z',"
               " 'active', 'FAKE-GRANT-1')")
        tamper("credits-out-of-thin-air", "check2",
               "INSERT INTO member_credit_events (event_id,"
               " census_avatar_id, period_id, delta, reason, ref_type,"
               " ts_utc) VALUES ('FAKE-EV-1', 'AV-201', 'NO-SUCH-PERIOD',"
               " 5, 'grant', 'activation', '2030-01-01T00:00:00Z')")
        audit_victim = db_query(
            mdb2, "SELECT audit_id FROM member_audit WHERE kind = 'credits'"
            " LIMIT 1")[0][0]
        tamper("deleted-audit-row", "check5",
               "DELETE FROM member_audit WHERE audit_id = ?",
               (audit_victim,))
        tamper("privilege-row-overreach", "check3",
               "INSERT INTO member_vouchers (voucher_id, census_avatar_id,"
               " period_id, voucher_type, status) VALUES ('FAKE-V-1',"
               " 'AV-202', ?, 'building_naming', 'unused')", (pid202,))
        tamper("forged-grant-source", "check1",
               "UPDATE member_periods SET source_grant_id = 'FORGED-9'"
               " WHERE period_id = ?", (pid202,))
        tamper("fiat-column-injected", "check4",
               "ALTER TABLE member_periods ADD COLUMN price_cent INTEGER")
        tamper("past-due-active-residue", "check6",
               "INSERT INTO member_periods (period_id, census_avatar_id,"
               " product_id, tier, period_no, start_utc, end_utc, status,"
               " source_grant_id) VALUES ('FAKE-PERIOD-2', 'AV-999',"
               " 'tier:experience', 'experience', 9,"
               " '2019-01-01T00:00:00Z', '2020-01-01T00:00:00Z',"
               " 'active', 'FAKE-GRANT-2')")
        rc2, out2, _ = run_cli(
            "reconcile.py", ["--member-db", mdb2, "--pay-db", pdb2,
                             "--ledger-db", ldb2, "--config", w2["mcfg_path"],
                             "--now", far])
        last = [f for f in RESULTS if f[0] == "AC-M14"]
        record("AC-M14", rc2 == 2 and last, "tampered world cli rc=%d (%s)"
               % (rc2, out2.splitlines()[0][:60] if out2 else "-"))
    finally:
        tear(w2)

    # ---- AC-M15: banned marketing copy never opens (fail closed) --------
    bad_copy = json.loads(json.dumps(load_json(
        os.path.join(BASE, "config.json"))))
    bad_copy["tiers"]["experience"]["copy"] += ban_word
    try:
        C.Catalog.from_config(bad_copy)
        ok15 = False
        ev15 = "banned tier copy accepted"
    except GateOfflineError as exc:
        ok15 = True
        ev15 = "banned tier copy refused: %s" % exc
    record("AC-M15", ok15, ev15)

    failed = [ac for ac, ok in RESULTS if not ok]
    counts = {}
    for ac, _ in RESULTS:
        counts[ac] = counts.get(ac, 0) + 1
    print("suite: %d assertions over %d criteria; failed=%s"
          % (len(RESULTS), len(counts), failed or "none"), flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
