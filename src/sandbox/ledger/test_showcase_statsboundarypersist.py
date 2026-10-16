"""Acceptance suite: stats_board zero-registry boundary world
cross-restart persistence example window (BigDomain R2010;
canon = the explore-queue stats zero-registry boundary persist
line, the R1992-reseed FIFO head). The stats_board family
(R1983 default registry board, R1988 cap-window tail read,
R1989 dual combined board) is registry-keyed: a
zero-registration world returns honest empty envelopes on all
three faces. This suite pins that boundary world across a
full-stack instance restart (persist family judgment
R1889/R1900/R1902; the R1976 AC-CBW curation boundary persist
precedent): the three empty envelopes stay byte-identical, the
limit gates still fire before any read, and the post-restart
first registration plus first place continue all three faces
with zero phantom rows.

Asserts the pre-registered criteria AC-SSZB1..AC-SSZB7 from
the R2010 claim line in state/queue/explore.md (criteria were
registered before this code existed; honesty law). Claim ruling
(registered at claim time): the pre-close world keeps the
ledger domain populated (four accounts, four certificates)
while the showcase registration axis stays empty - the
boundary isolates the registry axis, not the whole stack; no
frozen clock is needed because the board rows carry no
timestamps (the world writes do, the board output does not).

Suite-only round: zero product bytes change. This source stays
pure ASCII per the encoding discipline.

Usage: python test_showcase_statsboundarypersist.py
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
WINDOW_KEYS = {"limit", "total", "returned", "truncated"}
ROW_KEYS = {"showcase_id", "title", "ai_label", "places",
            "retracts", "displayed_now"}

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

    tmp = tempfile.mkdtemp(prefix="showcase-statsboundary-")
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
        # boundary world: ledger domain populated, showcase
        # registration axis empty (zero showcases, zero events)
        for who in ("ada", "bob", "carol", "dana"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
        cl = {}
        for who, ev, item in (
                ("ada", "evt-lamp", "lamp-cert"),
                ("bob", "evt-bell", "bell-cert"),
                ("carol", "evt-harp", "harp-cert"),
                ("dana", "evt-arch", "arch-cert")):
            cl[item] = cf.issue_certificate(
                "usr:" + who, ev, item)["cl_id"]
        shconn = sqlite3.connect(sh_path)
        ledconn = sqlite3.connect(db_path)

        # -- AC-SSZB1 zero-registry control anchor ---------------
        fam = family(sh)
        d1 = json.loads(fam["default"])
        c2 = json.loads(fam["cap2"])
        u2 = json.loads(fam["dual2"])
        ok_env = (set(d1.keys()) == DEFAULT_KEYS
                  and d1["showcase_stats_board"] == []
                  and set(c2.keys()) == CAP_KEYS
                  and c2["showcase_stats_board"] == []
                  and c2["limit"] == 2 and c2["total"] == 0
                  and c2["returned"] == 0
                  and c2["truncated"] is False
                  and set(u2.keys()) == DUAL_KEYS
                  and set(u2["window"].keys()) == WINDOW_KEYS
                  and u2["full_board"] == []
                  and u2["capped_board"] == []
                  and u2["window"] == {"limit": 2, "total": 0,
                                       "returned": 0,
                                       "truncated": False})
        fam_b = family(sh)
        record("AC-SSZB1", ok_env and fam == fam_b,
               "zero-registry world: default envelope keys=%s"
               " rows empty=%s; cap(2) keys=%s total=0 returned=0"
               " truncated=False=%s; dual(2) keys=%s window=%s"
               " both zones empty=%s; family double-read"
               " byte-identical=%s"
               % (sorted(d1.keys()),
                  d1["showcase_stats_board"] == [],
                  sorted(c2.keys()),
                  c2["truncated"] is False
                  and c2["total"] == 0 and c2["returned"] == 0,
                  sorted(u2.keys()), u2["window"],
                  u2["full_board"] == [] and
                  u2["capped_board"] == [],
                  fam == fam_b))

        # -- AC-SSZB2 bad-limit gates fire before any read -------
        probes_def = (-1, True, "2", 2.5, None)
        probes_dual = (0, -1, True, "2", 2.5, None)
        c0 = table_counts(shconn, ledconn)
        codes = []
        for bad in probes_def:
            try:
                sh.stats_board(bad)
                codes.append("no-raise")
            except S.ShowcaseError as exc:
                codes.append(exc.code)
        for bad in probes_dual:
            try:
                sh.stats_board_dual(bad)
                codes.append("no-raise")
            except S.ShowcaseError as exc:
                codes.append(exc.code)
        c1 = table_counts(shconn, ledconn)
        want_codes = [S.E_SH_BAD_LIMIT] * (len(probes_def)
                                           + len(probes_dual))
        record("AC-SSZB2",
               codes == want_codes and c0 == c1,
               "eleven bad forms (five default + six dual) all"
               " rejected E_SH_BAD_LIMIT: %s; probe batch leaves"
               " counts unchanged %s == %s (gates fire before"
               " any read, independent of the empty data face)"
               % (codes == want_codes, c0, c1))

        # -- AC-SSZB3 cross-restart byte identity ----------------
        sh.close()
        led.close()
        sh = led = None
        led2 = L.Ledger(db_path, cfg)
        gate2 = SecGate.from_config(lobby_cfg)
        sh2 = S.ShowcaseFace(led2, gate2, DISCLAIMER, sh_path)
        fam2 = family(sh2)
        double2 = fam2 == family(sh2)
        record("AC-SSZB3", fam2 == fam and double2,
               "full-stack close (sh -> led) then rebuild on"
               " same paths + same cfg bytes: three-face family"
               " {default, cap 1/2/50, dual 1/2/50}"
               " byte-identical=%s double-read self-stable=%s"
               % (fam2 == fam, double2))

        # -- AC-SSZB4 post-restart first registration ------------
        sh2.register_showcase("sh-first", "First Window", 3, True)
        d4 = sh2.stats_board()
        rows4 = d4["showcase_stats_board"]
        c2_4 = sh2.stats_board(2)
        u2_4 = sh2.stats_board_dual(2)
        row4 = rows4[0] if rows4 else {}
        ok4 = (len(rows4) == 1
               and set(row4.keys()) == ROW_KEYS
               and row4.get("showcase_id") == "sh-first"
               and row4.get("places") == 0
               and row4.get("retracts") == 0
               and row4.get("displayed_now") == 0
               and row4.get("ai_label") == 1
               and c2_4["total"] == 1 and c2_4["returned"] == 1
               and c2_4["truncated"] is False
               and c2_4["showcase_stats_board"] == rows4
               and u2_4["window"] == {"limit": 2, "total": 1,
                                      "returned": 1,
                                      "truncated": False}
               and u2_4["capped_board"] == u2_4["full_board"]
               and u2_4["full_board"] == rows4
               and dumps(d4) != fam["default"])
        record("AC-SSZB4", ok4,
               "post-restart first registration: default face"
               " exactly one honest-zero row {p=%s r=%s dn=%s"
               " ai=%s}; cap(2) total 0->1 returned=1"
               " truncated=False rows==full=%s; dual(2) window"
               "=%s capped==full=%s; zero phantom (board rows =="
               " registry rows == 1)=%s; liveness vs pre-restart"
               " empty snapshot=%s"
               % (row4.get("places"), row4.get("retracts"),
                  row4.get("displayed_now"), row4.get("ai_label"),
                  c2_4["showcase_stats_board"] == rows4,
                  u2_4["window"],
                  u2_4["capped_board"] == u2_4["full_board"],
                  len(rows4) == 1,
                  dumps(d4) != fam["default"]))

        # -- AC-SSZB5 post-restart first place + netflow ---------
        sh2.place_exhibit("usr:ada", "sh-first", cl["lamp-cert"],
                          "", False)
        d5 = sh2.stats_board()
        row5 = d5["showcase_stats_board"][0]
        c2_5 = sh2.stats_board(2)
        u2_5 = sh2.stats_board_dual(2)
        view5 = sh2.showcase_view("sh-first")
        ok5 = (row5["places"] == 1 and row5["retracts"] == 0
               and row5["displayed_now"] == 1
               and row5["displayed_now"] == row5["places"]
               - row5["retracts"]
               and c2_5["total"] == 1
               and u2_5["window"]["total"] == 1
               and len(view5["displayed"]) == 1
               and view5["displayed"][0]["cl_id"]
               == cl["lamp-cert"])
        record("AC-SSZB5", ok5,
               "post-restart first place: row {p=%s r=%s dn=%s}"
               " netflow identity holds=%s; cap(2) total==1=%s"
               " dual(2) window total==1=%s; cross-face"
               " displayed_now == len(showcase_view displayed)"
               "==1=%s (real product path: collectibles dock"
               " reconnect + SecGate caption pass)"
               % (row5["places"], row5["retracts"],
                  row5["displayed_now"],
                  row5["displayed_now"] == row5["places"]
                  - row5["retracts"],
                  c2_5["total"] == 1,
                  u2_5["window"]["total"] == 1,
                  len(view5["displayed"]) == 1))

        # -- AC-SSZB6 third instance + pure-read law -------------
        counts6a = table_counts(shconn, ledconn)
        battery_a = [dumps(sh2.stats_board()),
                     dumps(sh2.stats_board(2)),
                     dumps(sh2.stats_board_dual(2))]
        battery_b = [dumps(sh2.stats_board()),
                     dumps(sh2.stats_board(2)),
                     dumps(sh2.stats_board_dual(2))]
        counts6b = table_counts(shconn, ledconn)
        fam_final = family(sh2)
        sh2.close()
        led2.close()
        sh2 = led2 = None
        led3 = L.Ledger(db_path, cfg)
        gate3 = SecGate.from_config(lobby_cfg)
        sh3 = S.ShowcaseFace(led3, gate3, DISCLAIMER, sh_path)
        fam3 = family(sh3)
        record("AC-SSZB6",
               fam3 == fam_final and fam3 == family(sh3)
               and battery_a == battery_b and counts6a == counts6b,
               "third instance == second-instance final state"
               " byte-identical=%s sequential double-read=%s;"
               " repeat read pairs byte-identical=%s; read"
               " battery leaves counts unchanged %s == %s"
               % (fam3 == fam_final, fam3 == family(sh3),
                  battery_a == battery_b, counts6a, counts6b))
        sh3.close()
        led3.close()
        sh3 = led3 = None

        # -- AC-SSZB7 hygiene ------------------------------------
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
        reg_ok = ("ledger-showcase-statsboundary-persist" in reg_src
                  and "test_showcase_statsboundarypersist.py"
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
    record("AC-SSZB7",
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
