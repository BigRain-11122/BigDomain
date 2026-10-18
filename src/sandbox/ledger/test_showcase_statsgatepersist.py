"""Acceptance suite: showcase stats_board bad-argument gate
family cross-restart same-code example window (BigDomain R2035;
canon = the explore-queue stats gate family cross-restart line,
the R2010 reseed FIFO head). The R2010 boundary suite fired the
bad-limit probes on instance one only (AC-SSZB2 pre-close
probes); this successor pins the full gate family - the
E_SH_BAD_LIMIT cap forms, the E_SH_BAD_WINDOW month forms, and
the deterministic limit-before-window parameter order - as an
ordered (probe, code) vector that stays byte-identical on
instances one/two/three across two full-stack restarts (the
R1999 AC-HCWP4 gate-family cross-restart same-code precedent).
Unlike the R2010 zero-registry boundary world, this suite runs
against a populated registry axis (one active showcase with
place+retract events, one eventless showcase): the gates fire
before any read against non-empty data too, and every probe
batch leaves the three table counts unchanged on every
instance. A post-restart liveness leg proves the probe batch
never wedges the face, and the third-instance leg adds the
pure-read law.

Asserts the pre-registered criteria AC-SGB1..AC-SGB7 from the
R2035 claim annotation in state/queue/explore.md (criteria were
registered before this code existed; honesty law). Claim
rulings registered at claim time: populated-world ruling
(two showcases, the boundary world stays pinned by R2010), no
frozen clock (board rows carry no timestamps), 21-probe vector
ruling (5 default limit forms + 6 dual limit forms + 9 window
forms + 1 dual-bad order probe), same-code ruling (ordered
probe vector JSON-serialized byte-identical across instances
one/two/three over two full-stack restarts).

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline.

Usage: python test_showcase_statsgatepersist.py
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                     # noqa: E402 (P-47-2b core)
import collectibles as C               # noqa: E402 (owner face)
import showcase as S                   # noqa: E402 (face under test)
from sec_gate import SecGate           # noqa: E402 (lobby product)

EXPECTED = 7
RESULTS = []

DISCLAIMER = ("sandbox stand-in disclaimer: the showcase stats"
              " board is a display feature, not investment"
              " advice")

DEFAULT_KEYS = {"showcase_stats_board", "disclaimer"}
CAP_KEYS = {"showcase_stats_board", "disclaimer", "limit",
            "total", "returned", "truncated"}
DUAL_KEYS = {"full_board", "capped_board", "window", "disclaimer"}
ROW_KEYS = {"showcase_id", "title", "ai_label", "places",
            "retracts", "displayed_now"}

BAD_LIMIT_DEFAULT = (-1, True, "2", 2.5, None)
BAD_LIMIT_DUAL = (0, -1, True, "2", 2.5, None)
BAD_WINDOW = ("2026-13", "2026-1", "2026/10", "2026", "abcd",
              "", 2026, True, 2.5)

PRODUCT_FILES = [
    os.path.join(BASE, "showcase.py"),
    os.path.join(BASE, "config.json"),
    os.path.join(LOBBY, "config.json"),
]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def family(sh):
    """The three-face read family serialized: default full
    board, cap windows {1,2,50}, dual boards {1,2,50}."""
    out = {"default": dumps(sh.stats_board())}
    for cap in (1, 2, 50):
        out["cap%d" % cap] = dumps(sh.stats_board(cap))
    for cap in (1, 2, 50):
        out["dual%d" % cap] = dumps(sh.stats_board_dual(cap))
    return out


def battery(sh):
    """The 21-probe gate family battery as an ordered
    (probe-name, rejection-code) vector, JSON-serialized.
    Five default-face limit forms, six dual-face limit forms,
    nine window forms on the default face, and the dual-bad
    order probe (bad limit + bad window together must reject
    with the limit code first - the deterministic parameter
    gate order)."""
    out = []
    for i, bad in enumerate(BAD_LIMIT_DEFAULT):
        try:
            sh.stats_board(bad)
            out.append(["limit-def-%d" % i, "no-raise"])
        except S.ShowcaseError as exc:
            out.append(["limit-def-%d" % i, exc.code])
    for i, bad in enumerate(BAD_LIMIT_DUAL):
        try:
            sh.stats_board_dual(bad)
            out.append(["limit-dual-%d" % i, "no-raise"])
        except S.ShowcaseError as exc:
            out.append(["limit-dual-%d" % i, exc.code])
    for i, w in enumerate(BAD_WINDOW):
        try:
            sh.stats_board(0, w)
            out.append(["window-%d" % i, "no-raise"])
        except S.ShowcaseError as exc:
            out.append(["window-%d" % i, exc.code])
    try:
        sh.stats_board(-1, "abcd")
        out.append(["order-dual-bad", "no-raise"])
    except S.ShowcaseError as exc:
        out.append(["order-dual-bad", exc.code])
    return json.dumps(out)


def want_vector():
    """The expected ordered code vector: 11 E_SH_BAD_LIMIT,
    9 E_SH_BAD_WINDOW, 1 E_SH_BAD_LIMIT (order probe)."""
    out = []
    for i in range(len(BAD_LIMIT_DEFAULT)):
        out.append(["limit-def-%d" % i, S.E_SH_BAD_LIMIT])
    for i in range(len(BAD_LIMIT_DUAL)):
        out.append(["limit-dual-%d" % i, S.E_SH_BAD_LIMIT])
    for i in range(len(BAD_WINDOW)):
        out.append(["window-%d" % i, S.E_SH_BAD_WINDOW])
    out.append(["order-dual-bad", S.E_SH_BAD_LIMIT])
    return json.dumps(out)


def table_counts(shconn, ledconn):
    return {"showcases": int(shconn.execute(
                "SELECT COUNT(*) FROM showcases").fetchone()[0]),
            "exhibit_events": int(shconn.execute(
                "SELECT COUNT(*) FROM exhibit_events").fetchone()[0]),
            "collectibles": int(ledconn.execute(
                "SELECT COUNT(*) FROM collectibles").fetchone()[0])}


def main():
    pre_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg_bytes = handle.read()
    cfg = json.loads(cfg_bytes.decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))

    tmp = tempfile.mkdtemp(prefix="showcase-statsgate-")
    db_path = os.path.join(tmp, "ledger.db")
    sh_path = os.path.join(tmp, "showcase.db")
    hyg = {}
    led = sh = led2 = sh2 = led3 = sh3 = None
    shconn = ledconn = None
    try:
        led = L.Ledger(db_path, cfg)
        cf = C.CollectiblesFace(led)
        gate = SecGate.from_config(lobby_cfg)
        sh = S.ShowcaseFace(led, gate, DISCLAIMER, sh_path)
        # populated registry axis world: three accounts, three
        # certificates, two showcases (one active with a
        # place+retract history, one eventless)
        for who in ("ada", "bob", "carol"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
        cl = {}
        for who, ev, item in (
                ("ada", "evt-lamp", "lamp-cert"),
                ("bob", "evt-bell", "bell-cert"),
                ("carol", "evt-arch", "arch-cert")):
            cl[item] = cf.issue_certificate(
                "usr:" + who, ev, item)["cl_id"]
        sh.register_showcase("sh-active", "Active Window", 4,
                             False)
        sh.register_showcase("sh-empty", "Empty Window", 2,
                             False)
        sh.place_exhibit("usr:ada", "sh-active", cl["lamp-cert"],
                        "", False)
        sh.place_exhibit("usr:bob", "sh-active", cl["bell-cert"],
                        "", False)
        sh.retract_exhibit("usr:ada", "sh-active",
                           cl["lamp-cert"])
        shconn = sqlite3.connect(sh_path)
        ledconn = sqlite3.connect(db_path)

        # -- AC-SGB1 populated-world control anchor -------------
        fam = family(sh)
        fam_b = family(sh)
        d1 = json.loads(fam["default"])
        rows = d1["showcase_stats_board"]
        dense = (len(rows) == 2
                 and all(set(r.keys()) == ROW_KEYS for r in rows))
        netflow = all(
            r["displayed_now"] == r["places"] - r["retracts"]
            for r in rows)
        active = next((r for r in rows
                       if r["showcase_id"] == "sh-active"), None)
        empty = next((r for r in rows
                      if r["showcase_id"] == "sh-empty"), None)
        ok_active = (active is not None
                     and active["places"] == 2
                     and active["retracts"] == 1
                     and active["displayed_now"] == 1)
        ok_empty = (empty is not None
                    and empty["places"] == 0
                    and empty["retracts"] == 0
                    and empty["displayed_now"] == 0)
        ok_sort = (rows[0]["showcase_id"] == "sh-active"
                   and rows[1]["showcase_id"] == "sh-empty")
        record("AC-SGB1",
               dense and netflow and ok_active and ok_empty
               and ok_sort and fam == fam_b,
               "populated world: registry-dense rows=%s"
               " netflow identity=%s active row {p=2 r=1"
               " dn=1}=%s eventless row honest zeros=%s"
               " decisive sort active-first=%s family"
               " double-read byte-identical=%s"
               % (dense, netflow, ok_active, ok_empty, ok_sort,
                  fam == fam_b))

        # -- AC-SGB2 instance-one baseline battery --------------
        v1 = battery(sh)
        c0 = table_counts(shconn, ledconn)
        v1b = battery(sh)
        c1 = table_counts(shconn, ledconn)
        want = want_vector()
        record("AC-SGB2",
               v1 == want and c0 == c1 and v1 == v1b,
               "baseline battery: 21 probes (5 default limit +"
               " 6 dual limit + 9 window + 1 order) all reject"
               " with the expected ordered code vector=%s;"
               " probe batch double-run byte-identical=%s;"
               " counts unchanged %s == %s (gates fire before"
               " any read on the populated face)"
               % (v1 == want, v1 == v1b, c0, c1))

        # -- AC-SGB3 cross-restart same-code (instance two) -----
        sh.close()
        led.close()
        sh = led = None
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path)
        fam2 = family(sh2)
        c2a = table_counts(shconn, ledconn)
        v2 = battery(sh2)
        c2b = table_counts(shconn, ledconn)
        record("AC-SGB3",
               v2 == v1 and c2a == c2b and fam2 == fam,
               "full-stack close (sh -> led) then rebuild on"
               " same paths + same cfg bytes: identical battery"
               " vector byte-identical to baseline (same-code)="
               " %s; instance-two probe batch zero side effects"
               " %s == %s; read family byte-identical across"
               " restart=%s"
               % (v2 == v1, c2a, c2b, fam2 == fam))

        # -- AC-SGB4 post-restart liveness ----------------------
        sh2.register_showcase("sh-live", "Live Window", 3,
                              False)
        sh2.place_exhibit("usr:carol", "sh-live",
                          cl["arch-cert"], "", False)
        fam2b = family(sh2)
        d4 = json.loads(fam2b["default"])
        rows4 = d4["showcase_stats_board"]
        live = next((r for r in rows4
                     if r["showcase_id"] == "sh-live"), None)
        view4 = sh2.showcase_view("sh-live")
        ok4 = (len(rows4) == 3
               and live is not None
               and live["places"] == 1
               and live["retracts"] == 0
               and live["displayed_now"] == 1
               and len(view4["displayed"]) == 1
               and view4["displayed"][0]["cl_id"]
               == cl["arch-cert"]
               and all(r["displayed_now"] == r["places"]
                       - r["retracts"] for r in rows4)
               and fam2b != fam2)
        record("AC-SGB4", ok4,
               "post-restart liveness on instance two: real"
               " write path (register + place) grows the board"
               " registry-dense to 3 rows=%s; new row {p=1 r=0"
               " dn=1} netflow holds=%s; showcase_view displayed"
               " exactly the placed cert=%s; family changed only"
               " via the real write=%s"
               % (len(rows4) == 3,
                  live is not None and live["displayed_now"]
                  == live["places"] - live["retracts"],
                  len(view4["displayed"]) == 1
                  and view4["displayed"][0]["cl_id"]
                  == cl["arch-cert"],
                  fam2b != fam2))

        # -- AC-SGB5 third instance + pure-read law -------------
        counts5a = table_counts(shconn, ledconn)
        read_a = [dumps(sh2.stats_board()),
                  dumps(sh2.stats_board(2)),
                  dumps(sh2.stats_board_dual(2))]
        read_b = [dumps(sh2.stats_board()),
                  dumps(sh2.stats_board(2)),
                  dumps(sh2.stats_board_dual(2))]
        counts5b = table_counts(shconn, ledconn)
        fam2final = family(sh2)
        v2final = battery(sh2)
        sh2.close()
        led2.close()
        sh2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        gate3 = SecGate.from_config(lobby_cfg)
        sh3 = S.ShowcaseFace(led3, gate3, DISCLAIMER, sh_path)
        fam3 = family(sh3)
        v3 = battery(sh3)
        record("AC-SGB5",
               v3 == v1 and fam3 == fam2final
               and read_a == read_b and counts5a == counts5b
               and v2final == v1,
               "third instance: battery vector == baseline"
               " (same-code across the second restart)=%s; read"
               " family == instance-two final state"
               " (liveness write survives the restart)=%s;"
               " pre-close read battery double-run"
               " byte-identical=%s; read battery leaves counts"
               " unchanged %s == %s"
               % (v3 == v1, fam3 == fam2final,
                  read_a == read_b, counts5a, counts5b))
        sh3.close()
        led3.close()
        sh3 = led3 = None

        # -- AC-SGB6 cross-instance vector identity -------------
        d6 = json.loads(fam3["default"])
        c6 = json.loads(fam3["cap2"])
        u6 = json.loads(fam3["dual2"])
        keys_stable = (set(d6.keys()) == DEFAULT_KEYS
                       and set(c6.keys()) == CAP_KEYS
                       and set(u6.keys()) == DUAL_KEYS
                       and set(json.loads(fam["default"]).keys())
                       == DEFAULT_KEYS
                       and set(json.loads(fam2b["cap2"]).keys())
                       == CAP_KEYS
                       and set(json.loads(fam["dual2"]).keys())
                       == DUAL_KEYS)
        record("AC-SGB6",
               v1 == v2 == v3 and keys_stable,
               "cross-instance same-code summary: ordered probe"
               " vectors V1 == V2 == V3 byte-identical=%s"
               " (two full-stack restarts, three instances);"
               " envelope key sets constant across instances"
               " (default/cap/dual)=%s"
               % (v1 == v2 == v3, keys_stable))

        # -- AC-SGB7 hygiene ------------------------------------
        with open(os.path.abspath(__file__), "rb") as handle:
            own_bytes = handle.read()
        ascii_ok = all(b < 128 for b in own_bytes)
        net_ok = True
        for line in own_bytes.decode("ascii").splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith(
                    "from "):
                if any(w in stripped for w in
                       ("urllib", "requests", "socket", "http")):
                    net_ok = False
        reg_path = os.path.normpath(
            os.path.join(BASE, "..", "reconcile_all.py"))
        with open(reg_path, encoding="utf-8") as handle:
            reg_src = handle.read()
        reg_ok = ("ledger-showcase-statsgatepersist" in reg_src
                  and "test_showcase_statsgatepersist.py"
                  in reg_src)
        expected_ok = len(RESULTS) == EXPECTED - 1
        outside = tmp not in os.path.abspath(BASE)
        hyg = {"ascii_ok": ascii_ok, "net_ok": net_ok,
               "reg_ok": reg_ok, "expected_ok": expected_ok,
               "outside": outside}
    finally:
        for obj in (sh, led, sh2, led2, sh3, led3):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
        if shconn is not None:
            shconn.close()
        if ledconn is not None:
            ledconn.close()

    post_sha = {p: sha256_file(p) for p in PRODUCT_FILES}
    sha_ok = pre_sha == post_sha
    record("AC-SGB7",
           hyg.get("ascii_ok") and hyg.get("net_ok")
           and hyg.get("reg_ok") and hyg.get("expected_ok")
           and hyg.get("outside") and sha_ok,
           "suite pure ASCII=%s net-clean=%s registry-wired=%s"
           " expected-count=%s world outside repo=%s"
           " product-sha stable=%s"
           % (hyg.get("ascii_ok"), hyg.get("net_ok"),
              hyg.get("reg_ok"), hyg.get("expected_ok"),
              hyg.get("outside"), sha_ok))

    ok_all = len(RESULTS) == EXPECTED and all(
        ok for _ac, ok in RESULTS)
    print("SUITE %s %d/%d" % ("PASS" if ok_all else "FAIL",
                              sum(1 for _a, ok in RESULTS if ok),
                              EXPECTED), flush=True)
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
