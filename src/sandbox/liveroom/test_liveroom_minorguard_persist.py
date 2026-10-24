"""Liveroom open-session minor-guard front-door law, cross-restart.

Pre-registered criteria AC-LGM1..AC-LGM8 live in the R2075 explore-queue
row and were written before this file existed (honesty law). The R939
wiring seat only pinned single refusals; this suite pins four axes that
were never fixed:

  - gate ordering: the cheap front doors (empty args, unattended form,
    empty risk-control ref, missing opener id) must reject WITHOUT ever
    touching the guard, while the three guard-bearing forms reach
    check_live exactly once each (no door shadowed, no door skipped);
  - a refused session id is not consumed (an adult can open it later and
    the refusal leaves zero rows);
  - the minor live ban survives two full-stack restarts (the guard
    rehydrates from its own sqlite store, not from memory residue);
  - a guard-free face keeps the old behaviour byte-identical.

Stdlib only; this source stays pure ASCII (Chinese copy lives in the
product config). The sandbox world lives under the system temp dir,
never inside the repo.
"""

import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
_LEDGER = os.path.normpath(os.path.join(BASE, "..", "ledger"))
_LOBBY = os.path.normpath(os.path.join(BASE, "..", "lobby"))
_MINORS = os.path.normpath(os.path.join(BASE, "..", "minors"))
for _p in (_LEDGER, _LOBBY, _MINORS, BASE):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

import ledger as L                             # noqa: E402
import sec_gate as SG                          # noqa: E402
import minors as MG                            # noqa: E402
import liveroom as LR                          # noqa: E402

RESULTS = []
_ERRS = (LR.LiveRoomError, MG.GuardError)

EXPECTED = [
    ("empty_session", "E_LIVE_BAD_ARGS", 0),
    ("empty_room", "E_LIVE_BAD_ARGS", 0),
    ("unattended_minor", "E_LIVE_UNATTENDED", 0),
    ("empty_riskctl", "E_LIVE_BAD_ARGS", 0),
    ("missing_opener", "E_LIVE_BAD_ARGS", 0),
    ("minor", "E_MG_LIVE_BAN", 1),
    ("ghost", "E_MG_UNKNOWN", 1),
    ("adult", "OK", 1),
]


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)


def dumps(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def scalar(db_path, sql):
    conn = sqlite3.connect(db_path)
    try:
        return int(conn.execute(sql).fetchone()[0])
    finally:
        conn.close()


def sha256_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class CountingGuard(object):
    """Test-side proxy: records every check_live call, delegates all
    other attributes to the real guard. Product code is untouched."""

    def __init__(self, inner):
        self.inner = inner
        self.calls = []

    def check_live(self, resident_id):
        self.calls.append(resident_id)
        return self.inner.check_live(resident_id)

    def __getattr__(self, name):
        return getattr(self.inner, name)


def build_world():
    with open(os.path.join(_LEDGER, "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    tmp = tempfile.mkdtemp(prefix="lrg-minorguard-")
    return {"tmp": tmp, "cfg": cfg,
            "ledger_db": os.path.join(tmp, "ledger.db"),
            "minors_db": os.path.join(tmp, "minors.db"),
            "legacy_db": os.path.join(tmp, "legacy.db")}


def build_instance(world):
    cfg = world["cfg"]
    led = L.Ledger(world["ledger_db"], cfg)
    guard = MG.MinorGuardFace(world["minors_db"])
    if not guard.residents_readout():
        guard.register_resident("amy", False)
        guard.register_resident("kid", True, "g1")
    gate = SG.SecGate(cfg["gate"]["forbidden_words"],
                      cfg["gate"]["advisory_ban_words"])
    face = LR.LiveRoomFace(led, gate, cfg["token"]["disclaimer"],
                           cfg["token"]["ai_label_text"],
                           minor_guard=CountingGuard(guard))
    return {"led": led, "guard": guard, "face": face}


def close_instance(inst):
    inst["face"].close()
    inst["guard"].close()
    inst["led"].close()


def code_of(fn):
    try:
        fn()
    except _ERRS as exc:
        return getattr(exc, "code", None)
    return "OK"


def front_vector(inst, adult_session):
    """Fixed-order eight-form battery on one instance. Returns the
    (label, code, guard_calls_for_this_form) vector."""
    face = inst["face"]
    guard = inst["face"].minor_guard
    out = []

    def run(label, fn):
        before = len(guard.calls)
        out.append((label, code_of(fn), len(guard.calls) - before))

    run("empty_session", lambda: face.open_session(
        "", "r1", True, "rc-1", opener_resident_id="kid"))
    run("empty_room", lambda: face.open_session(
        "s-x", "", True, "rc-1", opener_resident_id="kid"))
    run("unattended_minor", lambda: face.open_session(
        "s-u", "r1", False, "rc-1", opener_resident_id="kid"))
    run("empty_riskctl", lambda: face.open_session(
        "s-r", "r1", True, "", opener_resident_id="kid"))
    run("missing_opener", lambda: face.open_session(
        "s-m", "r1", True, "rc-1"))
    run("minor", lambda: face.open_session(
        "s-kid", "r1", True, "rc-1", opener_resident_id="kid"))
    run("ghost", lambda: face.open_session(
        "s-g", "r1", True, "rc-1", opener_resident_id="ghost"))
    run("adult", lambda: face.open_session(
        adult_session, "r1", True, "rc-1", opener_resident_id="amy"))
    return out


def snapshot(inst, sessions):
    out = {}
    for sid in sessions:
        out[sid] = {
            "funnel": dumps(inst["face"].funnel(sid)),
            "transcript": dumps(inst["face"].transcript(sid)),
            "ledger": dumps(inst["face"].conversion_ledger(sid)),
        }
    return out


def main():
    print("=== Liveroom minor-guard front-door persist suite (R2075) ===",
          flush=True)
    g8_products = {}
    for rel in ("liveroom/liveroom.py", "minors/minors.py",
                "ledger/ledger.py", "ledger/config.json"):
        g8_products[rel] = sha256_file(
            os.path.join(os.path.normpath(os.path.join(BASE, "..")), rel))

    world = build_world()
    inst = None
    legacy = None
    try:
        # -- instance 1 -------------------------------------------------
        inst = build_instance(world)
        v1 = front_vector(inst, "s-kid")
        rows1 = scalar(world["ledger_db"],
                       "SELECT COUNT(*) FROM live_sessions")
        funnel_kid = inst["face"].funnel("s-kid")
        zero_kid = (funnel_kid["entered"] == 0
                    and funnel_kid["registered"] == 0
                    and funnel_kid["converted"] == 0
                    and funnel_kid["conversion_total"] == 0)
        lgm1 = v1 == EXPECTED
        lgm2 = (rows1 == 1 and zero_kid)
        lgm3 = (scalar(world["ledger_db"],
                       "SELECT COUNT(*) FROM ledger_tx") == 0
                and scalar(world["ledger_db"],
                           "SELECT COUNT(*) FROM live_cohort") == 0
                and scalar(world["ledger_db"],
                           "SELECT COUNT(*) FROM live_danmaku") == 0
                and scalar(world["ledger_db"],
                           "SELECT COUNT(*) FROM live_conversions") == 0)
        snap1 = snapshot(inst, ["s-kid"])
        res1 = dumps(inst["guard"].residents_readout())
        close_instance(inst)
        inst = None

        # -- instance 2 (restart one) -----------------------------------
        inst = build_instance(world)
        v2 = front_vector(inst, "s2")
        rows2 = scalar(world["ledger_db"],
                       "SELECT COUNT(*) FROM live_sessions")
        res2 = dumps(inst["guard"].residents_readout())
        lgm4 = (v2 == EXPECTED and rows2 == 2 and res2 == res1)
        snap2 = snapshot(inst, ["s-kid", "s2"])
        code_minor2 = v2[5][1]
        code_ghost2 = v2[6][1]
        close_instance(inst)
        inst = None

        # -- instance 3 (restart two) -----------------------------------
        inst = build_instance(world)
        v3 = front_vector(inst, "s3")
        rows3 = scalar(world["ledger_db"],
                       "SELECT COUNT(*) FROM live_sessions")
        res3 = dumps(inst["guard"].residents_readout())
        lgm5 = (v3 == EXPECTED and rows3 == 3
                and res2 == res3 == res1)
        snap3 = snapshot(inst, ["s-kid", "s2"])
        disc = world["cfg"]["token"]["disclaimer"]
        spine_ok = True
        for sid in ("s-kid", "s2"):
            lines = inst["face"].transcript(sid)
            spine_ok = spine_ok and lines[0] == disc and lines[-1] == disc
        lgm6 = (snap1["s-kid"] == snap2["s-kid"] == snap3["s-kid"]
                and snap2["s2"] == snap3["s2"] and spine_ok)

        # -- guard-free legacy face (same world, own db) ----------------
        led2 = L.Ledger(world["legacy_db"], world["cfg"])
        gate = SG.SecGate(world["cfg"]["gate"]["forbidden_words"],
                          world["cfg"]["gate"]["advisory_ban_words"])
        legacy = LR.LiveRoomFace(led2, gate, disc,
                                 world["cfg"]["token"]["ai_label_text"])
        legacy_ok = code_of(lambda: legacy.open_session(
            "s-legacy", "r1", True, "rc-1")) == "OK"
        legacy_rows = scalar(world["legacy_db"],
                             "SELECT COUNT(*) FROM live_sessions")
        main_rows = scalar(world["ledger_db"],
                           "SELECT COUNT(*) FROM live_sessions")
        lgm7 = (legacy_ok and legacy_rows == 1 and main_rows == 3)

        # -- hygiene ----------------------------------------------------
        with open(os.path.abspath(__file__), "rb") as fh:
            raw = fh.read()
        ascii_ok = True
        try:
            raw.decode("ascii")
        except UnicodeDecodeError:
            ascii_ok = False
        net_hits = []
        for line in raw.decode("ascii", "replace").splitlines():
            stripped = line.strip()
            if not stripped.startswith(("import ", "from ")):
                continue
            for mod in ("socket", "urllib", "http", "requests", "ftplib",
                        "smtplib"):
                if stripped.split()[1].split(".")[0] == mod:
                    net_hits.append(stripped)
        registry = ""
        with open(os.path.join(_LEDGER, "..", "reconcile_all.py"),
                  encoding="utf-8") as fh:
            registry = fh.read()
        reg_ok = ("liveroom-minorguard-persist" in registry
                  and "test_liveroom_minorguard_persist.py" in registry)
        tmp_outside = not os.path.abspath(world["tmp"]).lower().startswith(
            os.path.abspath(BASE).lower())
        sha_ok = True
        for rel, digest in g8_products.items():
            now = sha256_file(
                os.path.join(os.path.normpath(os.path.join(BASE, "..")),
                             rel))
            sha_ok = sha_ok and now == digest
        count_ok = len(RESULTS) + 8 == 8
        lgm8 = (ascii_ok and not net_hits and reg_ok and tmp_outside
                and sha_ok and count_ok)
        g8_evidence = ("ascii=%s net_hits=%d registry=%s tmp_outside=%s "
                       "products_sha=%s criteria=8"
                       % (ascii_ok, len(net_hits), reg_ok, tmp_outside,
                          sha_ok))

        record("AC-LGM1", lgm1, "front-door vector leg1=%r leg2=%r leg3=%r "
               "expected=%r" % (v1, v2, v3, EXPECTED))
        record("AC-LGM2", lgm2, "refused id reusable; rows=%d funnel=%s"
               % (rows1, dumps(funnel_kid)))
        record("AC-LGM3", lgm3, "ledger_tx/cohort/danmaku/conversions all 0")
        record("AC-LGM4", lgm4, "restart1: rows=%d ban=%s unknown=%s "
               "residents_equal=%s"
               % (rows2, code_minor2, code_ghost2, res2 == res1))
        record("AC-LGM5", lgm5, "restart2: rows=%d vector_equal=%s "
               "residents_equal=%s"
               % (rows3, v3 == EXPECTED, res3 == res1))
        record("AC-LGM6", lgm6, "read faces byte-identical across three "
               "instances; disclaimer spine=%s" % spine_ok)
        record("AC-LGM7", lgm7, "legacy rows=%d main rows=%d"
               % (legacy_rows, main_rows))
        record("AC-LGM8", lgm8, g8_evidence)
    finally:
        if inst is not None:
            close_instance(inst)
        if legacy is not None:
            legacy.close()
        shutil.rmtree(world["tmp"], ignore_errors=True)

    failed = [ac for ac, ok in RESULTS if not ok]
    print("SUITE PASS %d/%d" % (len(RESULTS) - len(failed), len(RESULTS)),
          flush=True)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())