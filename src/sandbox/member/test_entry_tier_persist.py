"""Acceptance suite for the member entry-tier (patron,
C-20260927-01) activation-receipt read-face family across an
INSTANCE RESTART (BigDomain R1932 tech-queue claim row; seed =
the R1931 reseed: the entry-tier base suite pins only the
static catalog face with zero close->reopen examples, and the
activation-receipt face family (member.py activate -> the
_period_face_row envelope with tier / period_no /
credits_balance / idempotent, plus the vouchers_opened add-on)
has zero cross-instance restart example anywhere in the books -
the privileges persist sibling (AC-PRP) closed privileges_for /
has_privilege, the balance / birthcert / expiring siblings
closed theirs; this row closes the receipt family).

Family law: a fresh MemberStore instance on the same db / cfg /
live pay dock must replay the SAME grant as an idempotent
activation whose receipt is byte-identical on every
data-carrying key (the idempotent flag flips True and the
vouchers_opened add-on key is honestly absent on the replay
path), a new true-path purchase must recompute a fresh receipt
with zero cache, the refunded dead-source gate must refuse
replay on the fresh instance (the gate sits before the
idempotent lookup, R1721), reads must move zero rows, and a
second restart must replay byte-identically again.

Asserts the pre-registered criteria AC-ETP1..AC-ETP7 from the
R1932 tech.md claim line (criteria were registered before this
code existed; honesty law). Each criterion prints PASS/FAIL
with evidence; the process exits non-zero on any FAIL. The
evidence lines are clock-free (structural facts and equality
booleans only) so a double run is byte-identical.

Carrier verdict (family law): one world drives the TRUE
product path end to end - every period opens via pay order ->
place -> callback -> grant -> store.activate, the refund avatar
rides the R1721 granted->closed edge, zero fixture injection,
zero raw SQL writes. The patron entry-tier pay row is
suite-owned (tier_products fixture + one additive row); real
tier price rows stay a [needs-CEO] approval face.

This test source stays pure ASCII per the encoding discipline.

Usage: python test_entry_tier_persist.py
"""

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import test_member as TM               # noqa: E402 (world build reuse)
import member as M                     # noqa: E402 (face under test)
import catalog as C                    # noqa: E402 (substrate face)

RESULTS = []
EXPECTED = 7

CFG_PATH = os.path.join(BASE, "config.json")
MEMBER_SRC = os.path.join(BASE, "member.py")
FIXTURE_SRC = os.path.join(BASE, "test_member.py")
RUNNER_SRC = os.path.join(BASE, "..", "reconcile_all.py")
SUITE_LABEL = "member-entrytier-persist"

NET_LIBS = ("urllib", "requests", "socket", "http.client",
            "http.server")
REPLAY_DROP = ("idempotent", "vouchers_opened")
TIER_ATTRS = ("key", "monthly_credits", "period_days",
              "grace_days", "copy")
COUNT_TABLES = ("member_periods", "member_credit_events",
                "member_vouchers")
AVATARS = ("ETP-A", "ETP-B", "ETP-D")


def record(ac, ok, evidence):
    line = "%s %s | %s" % ("PASS" if ok else "FAIL", ac, evidence)
    print(line)
    if not ok:
        RESULTS.append(ac)


def norm(receipt):
    """Replay-normalized view: the idempotent flag and the
    fresh-path-only vouchers_opened add-on are dropped; every
    other key must be byte-identical across the restart."""
    return {k: v for k, v in receipt.items()
            if k not in REPLAY_DROP}


def tier_proj(tier):
    out = {}
    for attr in TIER_ATTRS:
        out[attr] = getattr(tier, attr, None)
    out["privileges"] = sorted(getattr(tier, "privileges", []))
    return out


def catalog_proj(cat):
    return {
        "tiers": {k: tier_proj(cat.tiers[k])
                  for k in sorted(cat.tiers)},
        "products": {k: cat.products[k].key
                     for k in sorted(cat.products)},
        "vouchers": {k: cat.vouchers[k]
                     for k in sorted(cat.vouchers)},
    }


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def member_counts(db_path):
    con = sqlite3.connect(db_path)
    try:
        return {t: con.execute(
            "SELECT COUNT(*) FROM %s" % t).fetchone()[0]
            for t in COUNT_TABLES}
    finally:
        con.close()


def pay_grant_lens(world):
    return {a: len(world["pay"].grants_for(a)["items"])
            for a in AVATARS}


def entry_products(pcfg):
    """Fixture face: the standard tier rows plus ONE additive
    patron entry-tier row whose entitlement key is the member
    catalog product key (C-20260927-01 dock face)."""
    TM.tier_products(pcfg)
    pcfg["products"]["tier_patron"] = {
        "channel": "virtual", "price_cent": 2990, "share_tokens": 0,
        "entitlement": "tier:patron",
        "copy": "sandbox dock product: patron entry tier"}
    return pcfg


def refuses(face, grant_id, avatar):
    try:
        face.activate(grant_id, avatar)
        return False, "activate returned (gate did not refuse)"
    except M.MemberError as exc:
        return (exc.code == "E_BAD_GRANT_SOURCE",
                "code=%s" % exc.code)


def main():
    pre_sha = {p: sha256_file(p) for p in
               (CFG_PATH, MEMBER_SRC, FIXTURE_SRC)}
    w = TM.build(mutate_pay=entry_products)
    try:
        store = w["store"]
        patron = store.catalog.tiers["patron"]
        monthly = patron.monthly_credits

        # ---- AC-ETP1: substrate identity + first receipt pin ----
        with open(w["mcfg_path"], encoding="utf-8") as fh:
            mcfg_disk = json.load(fh)
        cat_a = C.Catalog.from_config(mcfg_disk)
        cat_b = C.Catalog.from_config(mcfg_disk)
        proj_eq = (json.dumps(catalog_proj(cat_a), sort_keys=True)
                   == json.dumps(catalog_proj(cat_b), sort_keys=True))
        pat_in = ("tier:patron" in cat_a.products
                  and cat_a.products["tier:patron"].key == "patron")
        vouchers_wanted = sorted(
            v for v, p in store.catalog.vouchers.items()
            if p in patron.privileges)

        oid_a1, g_a1 = TM.happy(w, "tier_patron", "ETP-A", "etp-a1")
        r_a1 = store.activate(g_a1, "ETP-A")
        ok1 = (proj_eq and pat_in
               and r_a1["tier"] == "patron"
               and r_a1["product"] == "tier:patron"
               and r_a1["period_no"] == 1
               and r_a1["credits_balance"] == monthly
               and r_a1["idempotent"] is False
               and sorted(r_a1.get("vouchers_opened", []))
               == vouchers_wanted)
        record("AC-ETP1", ok1,
               "substrate proj_eq=%s patron_in_map=%s; receipt"
               " tier=%s period_no=%s credits=%s vouchers=%s"
               % (proj_eq, pat_in, r_a1["tier"], r_a1["period_no"],
                  r_a1["credits_balance"],
                  sorted(r_a1.get("vouchers_opened", []))))

        # ---- AC-ETP2: stacked renewal receipt face ----
        # the closed-bucket bump is the only road to a second live
        # order for the same avatar+product (compute_order_id
        # bucket = closed+1): refund the first order (its grant is
        # now a dead source, its period stays active) and the
        # renewal stacks on the still-active end (R1721 world
        # shape, privileges_persist EP-B family law).
        w["pay"].close_refund(oid_a1)      # granted -> closed edge
        _, g_a2 = TM.happy(w, "tier_patron", "ETP-A", "etp-a2")
        r_a2 = store.activate(g_a2, "ETP-A")
        ok2 = (r_a2["period_no"] == 2
               and r_a2["start_utc"] == r_a1["end_utc"]
               and r_a2["credits_balance"] == monthly
               and r_a2["idempotent"] is False)
        record("AC-ETP2", ok2,
               "renewal period_no=%s start==first_end=%s credits=%s"
               % (r_a2["period_no"],
                  r_a2["start_utc"] == r_a1["end_utc"],
                  r_a2["credits_balance"]))

        # sibling baseline (untouched twin)
        _, g_b = TM.happy(w, "tier_experience", "ETP-B", "etp-b1")
        r_b = store.activate(g_b, "ETP-B")

        cnt_pre = member_counts(w["member_db"])
        grants_pre = pay_grant_lens(w)

        # ---- AC-ETP3: cross-restart idempotent replay law ----
        store.close()
        f2 = M.MemberStore(w["mcfg"], w["member_db"], w["pay"])
        i_a2 = f2.activate(g_a2, "ETP-A")
        cnt_mid = member_counts(w["member_db"])
        ok3 = (norm(i_a2) == norm(r_a2)
               and i_a2["idempotent"] is True
               and "vouchers_opened" not in i_a2
               and cnt_mid["member_periods"]
               == cnt_pre["member_periods"]
               and cnt_mid["member_credit_events"]
               == cnt_pre["member_credit_events"]
               and cnt_mid["member_vouchers"]
               == cnt_pre["member_vouchers"])
        record("AC-ETP3", ok3,
               "replay norm_eq=%s idem=%s"
               " vouchers_key_absent=%s rows_frozen=%s"
               % (norm(i_a2) == norm(r_a2),
                  i_a2["idempotent"],
                  "vouchers_opened" not in i_a2,
                  cnt_mid == cnt_pre))

        # ---- AC-ETP4: post-restart fresh true-path recompute ----
        _, g_d = TM.happy(w, "tier_patron", "ETP-D", "etp-d1")
        r_d = f2.activate(g_d, "ETP-D")
        ok4 = (r_d["tier"] == "patron"
               and r_d["period_no"] == 1
               and r_d["credits_balance"] == monthly
               and r_d["idempotent"] is False
               and sorted(r_d.get("vouchers_opened", []))
               == vouchers_wanted)
        record("AC-ETP4", ok4,
               "fresh-on-f2 tier=%s period_no=%s credits=%s"
               " idem=%s" % (r_d["tier"], r_d["period_no"],
                             r_d["credits_balance"],
                             r_d["idempotent"]))

        # ---- AC-ETP5: refund dead-source gate across restart ----
        # g_a1 was activated pre-refund (its period row exists, so
        # the idempotent lookup WOULD find it) - the refunded gate
        # refusing the replay proves the gate sits BEFORE the
        # idempotent lookup (R1721) on the fresh instance.
        gate_ok, gate_ev = refuses(f2, g_a1, "ETP-A")
        record("AC-ETP5", gate_ok,
               "post-restart replay of the refunded grant %s"
               % gate_ev)

        # ---- AC-ETP6: pure-read law + untouched twin freeze ----
        i_b = f2.activate(g_b, "ETP-B")     # untouched twin replay
        cnt_before_reads = member_counts(w["member_db"])
        lens_before = pay_grant_lens(w)
        f2.activate(g_a2, "ETP-A")          # read batch (replays)
        f2.activate(g_b, "ETP-B")
        f2.activate(g_d, "ETP-D")
        grants_after_reads = pay_grant_lens(w)
        cnt_after_reads = member_counts(w["member_db"])
        ok6 = (norm(i_b) == norm(r_b)
               and i_b["idempotent"] is True
               and "vouchers_opened" not in i_b
               and cnt_after_reads == cnt_before_reads
               and grants_after_reads == lens_before)
        record("AC-ETP6", ok6,
               "twin norm_eq=%s reads_move_zero_rows=%s"
               " grant_lens_stable=%s"
               % (norm(i_b) == norm(r_b),
                  cnt_after_reads == cnt_before_reads,
                  grants_after_reads == lens_before))

        # ---- AC-ETP7: double-restart identity + hygiene ----
        f2.close()
        f3 = M.MemberStore(w["mcfg"], w["member_db"], w["pay"])
        j_a2 = f3.activate(g_a2, "ETP-A")
        j_b = f3.activate(g_b, "ETP-B")
        j_d = f3.activate(g_d, "ETP-D")
        replay_stable = (norm(j_a2) == norm(i_a2)
                         and norm(j_b) == norm(i_b)
                         and norm(j_d) == norm(r_d)
                         and j_a2["idempotent"] is True
                         and j_b["idempotent"] is True
                         and j_d["idempotent"] is True)
        post_sha = {p: sha256_file(p) for p in
                    (CFG_PATH, MEMBER_SRC, FIXTURE_SRC)}
        sha_ok = post_sha == pre_sha
        with open(__file__, "rb") as fh:
            src = fh.read()
        ascii_ok = all(b < 128 for b in src)
        import_lines = [ln for ln in src.decode("ascii").splitlines()
                        if ln.startswith("import ")
                        or ln.startswith("from ")]
        net_ok = not any(lib in ln
                         for ln in import_lines
                         for lib in NET_LIBS)
        tmp_ok = (os.path.abspath(w["tmp"])
                  .startswith(tempfile.gettempdir()))
        ok7 = (replay_stable and sha_ok and ascii_ok
               and net_ok and tmp_ok)
        record("AC-ETP7", ok7,
               "second-restart replay_eq=%s sha_ok=%s ascii=%s"
               " net_free=%s tmp_outside_repo=%s"
               % (replay_stable, sha_ok, ascii_ok, net_ok,
                  tmp_ok))

        f3.close()
    finally:
        try:
            w["pay"].close()
        except Exception:
            pass
        try:
            w["led"].close()
        except Exception:
            pass
        shutil.rmtree(w["tmp"], ignore_errors=True)

    if RESULTS:
        print("SUITE FAIL: %s" % ",".join(RESULTS))
        return 1
    print("SUITE PASS: %d/%d" % (EXPECTED, EXPECTED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
