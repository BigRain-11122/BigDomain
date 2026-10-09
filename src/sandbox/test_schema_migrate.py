"""Schema migrator acceptance suite (claimed as the O-20261009-1246
dispatch-d head item; criteria AC-LM1..AC-LM11 were pre-registered in
state/queue/tech.md R1676 before any of this code existed - honesty
law).

Faces covered, one PASS line per criterion (reconcile_all counts them):
- framework/chain files, ASCII discipline, five production chains (LM1)
- chain-format guard (LM2), status/baseline/migrate CLI faces (LM2/LM6)
- ALTER-free rebuild + sql ops with data fidelity (LM4/LM5)
- forward-only refusal (LM3), structural ALTER ban (LM4)
- dual-phase criteria aborts with full tx rollback (LM5)
- baseline refusal family (LM6)
- five-domain isomorphic round trip on live constructor DBs (LM7)
- drifted-schema adoption refusal (LM6/LM7)

Exit 0 = all green. Stdlib only, ASCII source, zero network.
"""

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(BASE, "schema_migrate.py")
CHAINS = os.path.join(BASE, "migration_chains.json")

sys.path.insert(0, BASE)
for _d in ("ledger", "pay", "member", "lobby"):
    _p = os.path.join(BASE, _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import schema_migrate as SM  # noqa: E402

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def run_cli(db, domain, *actions, **kw):
    chain = kw.get("chain", CHAINS)
    proc = subprocess.run(
        [sys.executable, CLI, "--chain", chain, "--domain", domain, "--db", db]
        + list(actions),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120, cwd=BASE)
    return proc.returncode, (proc.stdout or "").strip()


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def fp_of(db):
    conn = sqlite3.connect(db)
    try:
        return SM.fingerprint(conn)
    finally:
        conn.close()


def make_world(tmp, name="world.db"):
    """Synthetic v1 world: t_users(id, name, note) with 12 rows."""
    db = os.path.join(tmp, name)
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE t_users (id INTEGER PRIMARY KEY,"
                 " name TEXT NOT NULL, note TEXT)")
    for i in range(12):
        conn.execute("INSERT INTO t_users (id, name, note) VALUES (?,?,?)",
                     (i, "u%02d" % i, "note-%d" % i))
    conn.commit()
    conn.close()
    return db


def make_rnd_world(tmp):
    """v1 world for the mapped-content criteria probe."""
    db = os.path.join(tmp, "rnd.db")
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE t_rnd (seed INTEGER PRIMARY KEY, note TEXT)")
    for i in range(12):
        conn.execute("INSERT INTO t_rnd (seed, note) VALUES (?,?)",
                     (i, "n-%d" % i))
    conn.commit()
    conn.close()
    return db


WORLD_ROWS = [(i, "u%02d" % i, "note-%d" % i) for i in range(12)]


def write_chain(path, baseline_fp, steps):
    doc = {"_doc": "synthetic test chain", "domains": {
        "synth": {"baseline": {"fingerprint": baseline_fp}, "steps": steps}}}
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(doc, handle, ensure_ascii=False, indent=2)
    return path


GOOD_STEPS = [
    {"version": 2, "name": "users-shape-v2", "ops": [
        {"kind": "rebuild", "table": "t_users",
         "new_ddl": "CREATE TABLE @new (id INTEGER PRIMARY KEY,"
                    " name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active')",
         "columns": [{"new": "id", "old": "id"}, {"new": "name", "old": "name"}]}]},
    {"version": 3, "name": "tags-and-index", "ops": [
        {"kind": "sql", "sql": "CREATE TABLE t_tags (tag_id INTEGER PRIMARY KEY,"
                               " label TEXT NOT NULL)"},
        {"kind": "sql", "sql": "CREATE INDEX idx_t_users_name ON t_users (name)"}]},
]


def t_lm1_files():
    ok = os.path.isfile(CLI) and os.path.isfile(CHAINS)
    with open(CLI, "rb") as handle:
        ok = ok and all(b < 128 for b in handle.read())
    chains = SM.read_chains(CHAINS)
    ok = ok and sorted(chains) == ["ledger", "lobby", "member", "pay", "ugc"]
    ok = ok and all(not (chains[d].get("steps") or []) for d in chains)
    check(ok, "AC-LM1 framework+chains files in place, ASCII source, five"
              " domains registered, production steps empty (AC-LM11 posture)")


def t_chain_format_guard():
    tmp = tempfile.mkdtemp(prefix="mig-t-")
    path = os.path.join(tmp, "bad.json")
    doc = {"domains": {"synth": {
        "baseline": {"fingerprint": {"tables": {}}},
        "steps": [
            {"version": 2, "name": "a", "ops": [{"kind": "sql", "sql": "SELECT 1"}]},
            {"version": 2, "name": "b", "ops": [{"kind": "sql", "sql": "SELECT 1"}]}]}}}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(doc, handle)
    try:
        SM.read_chains(path)
        ok = False
    except SM.MigrationError as exc:
        ok = exc.code == SM.E_CHAIN_FORMAT
    check(ok, "AC-LM2 chain-format guard: non-increasing step versions"
              " refused (E_CHAIN_FORMAT)")


def t_main_world():
    tmp = tempfile.mkdtemp(prefix="mig-t-")
    db = make_world(tmp)
    chain = write_chain(os.path.join(tmp, "chain.json"), fp_of(db), GOOD_STEPS)
    code, out = run_cli(db, "synth", "--status", chain=chain)
    check(code == 0 and "current=0" in out and "needs_baseline=True" in out,
          "AC-LM6 status face: unversioned live db reports needs_baseline")
    code, out = run_cli(db, "synth", "--baseline", chain=chain)
    check(code == 0 and "user_version=1" in out,
          "AC-LM6 baseline adoption on the synthetic world")
    code, out = run_cli(db, "synth", "--status", chain=chain)
    check(code == 0 and "current=1 target=3 pending=[2, 3]" in out,
          "AC-LM2 status face: current/target/pending after adoption")
    code, out = run_cli(db, "synth", "--migrate", chain=chain)
    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT id, name, status FROM t_users"
                        " ORDER BY id").fetchall()
    cols = [r[1] for r in conn.execute("PRAGMA table_info(t_users)").fetchall()]
    has_index = conn.execute("SELECT 1 FROM sqlite_master WHERE type='index'"
                             " AND name='idx_t_users_name'").fetchone()
    has_tags = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table'"
                            " AND name='t_tags'").fetchone()
    ver = conn.execute("PRAGMA user_version").fetchone()[0]
    conn.close()
    ok = (code == 0 and "user_version=3" in out and ver == 3
          and rows == [(i, "u%02d" % i, "active") for i in range(12)]
          and "note" not in cols and has_index and has_tags)
    check(ok, "AC-LM4/LM5 migrate v1->v3: ALTER-free rebuild + sql ops,"
              " data fidelity, dropped column, default fill")
    code, out = run_cli(db, "synth", "--migrate", chain=chain)
    check(code == 0 and "user_version=3" in out,
          "AC-LM2 idempotent re-run: no pending steps, version stable")
    mig = SM.SchemaMigrator(db, SM.read_chains(chain)["synth"])
    try:
        try:
            mig._apply_step(GOOD_STEPS[0])
            ok = False
        except SM.MigrationError as exc:
            ok = exc.code == SM.E_MIGRATION_VERSION
    finally:
        mig.close()
    check(ok, "AC-LM3 forward-only: step at/below current version refused"
              " (E_MIGRATION_VERSION)")


def t_alter_ban():
    tmp = tempfile.mkdtemp(prefix="mig-t-")
    db = make_world(tmp)
    chain = write_chain(os.path.join(tmp, "chain.json"), fp_of(db), [
        {"version": 2, "name": "hand-alter", "ops": [
            {"kind": "sql",
             "sql": "ALTER TABLE t_users ADD COLUMN junk TEXT"}]}])
    run_cli(db, "synth", "--baseline", chain=chain)
    code, out = run_cli(db, "synth", "--migrate", chain=chain)
    conn = sqlite3.connect(db)
    ver = conn.execute("PRAGMA user_version").fetchone()[0]
    cols = [r[1] for r in conn.execute("PRAGMA table_info(t_users)").fetchall()]
    conn.close()
    ok = (code == 2 and SM.E_ALTER_BANNED in out and ver == 1
          and "junk" not in cols)
    check(ok, "AC-LM4 structural ALTER ban: step refused before running,"
              " db untouched")


def t_rowcount_abort():
    tmp = tempfile.mkdtemp(prefix="mig-t-")
    db = make_world(tmp)
    steps = [{"version": 2, "name": "rowcount-abort-probe", "ops": [
        {"kind": "rebuild", "table": "t_users",
         "new_ddl": "CREATE TABLE @new (id INTEGER PRIMARY KEY,"
                    " name TEXT NOT NULL)",
         "columns": [{"new": "id", "old": "id"}, {"new": "name", "old": "name"}],
         "triggers": ["CREATE TRIGGER @new_cap BEFORE INSERT ON @new"
                      " WHEN (SELECT COUNT(*) FROM @new) >= 3"
                      " BEGIN SELECT RAISE(IGNORE); END"]}]}]
    chain = write_chain(os.path.join(tmp, "chain.json"), fp_of(db), steps)
    run_cli(db, "synth", "--baseline", chain=chain)
    code, out = run_cli(db, "synth", "--migrate", chain=chain)
    conn = sqlite3.connect(db)
    ver = conn.execute("PRAGMA user_version").fetchone()[0]
    rows = conn.execute("SELECT id, name, note FROM t_users"
                        " ORDER BY id").fetchall()
    staging = conn.execute("SELECT name FROM sqlite_master WHERE"
                           " name LIKE 't_users__mig%'").fetchall()
    conn.close()
    ok = (code == 2 and SM.E_MIGRATION_VERIFY in out and "rowcount" in out
          and ver == 1 and rows == WORLD_ROWS and not staging)
    check(ok, "AC-LM5 dual-phase criteria: rowcount mismatch aborts the"
              " whole step, rollback leaves db intact (version stamp"
              " transactional)")


def t_content_abort():
    tmp = tempfile.mkdtemp(prefix="mig-t-")
    db = make_rnd_world(tmp)
    steps = [{"version": 2, "name": "content-abort-probe", "ops": [
        {"kind": "rebuild", "table": "t_rnd",
         "new_ddl": "CREATE TABLE @new (seed INTEGER PRIMARY KEY, rnd INTEGER)",
         "columns": [{"new": "seed", "old": "seed"},
                      {"new": "rnd", "old": "abs(random())"}]}]}]
    chain = write_chain(os.path.join(tmp, "chain.json"), fp_of(db), steps)
    run_cli(db, "synth", "--baseline", chain=chain)
    code, out = run_cli(db, "synth", "--migrate", chain=chain)
    conn = sqlite3.connect(db)
    ver = conn.execute("PRAGMA user_version").fetchone()[0]
    rows = conn.execute("SELECT seed, note FROM t_rnd"
                        " ORDER BY seed").fetchall()
    staging = conn.execute("SELECT name FROM sqlite_master WHERE"
                           " name LIKE 't_rnd__mig%'").fetchall()
    conn.close()
    ok = (code == 2 and SM.E_MIGRATION_VERIFY in out
          and "mapped-content" in out and ver == 1
          and rows == [(i, "n-%d" % i) for i in range(12)] and not staging)
    check(ok, "AC-LM5 dual-phase criteria: mapped-content mismatch aborts,"
              " db intact (non-deterministic column expressions caught)")


def t_baseline_refusals():
    # drifted world: extra table -> adoption refused, version stays 0
    tmp = tempfile.mkdtemp(prefix="mig-t-")
    db = make_world(tmp)
    clean_fp = fp_of(db)
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE t_evil (a INTEGER)")
    conn.commit()
    conn.close()
    chain = write_chain(os.path.join(tmp, "chain.json"), clean_fp, GOOD_STEPS)
    code, out = run_cli(db, "synth", "--baseline", chain=chain)
    conn = sqlite3.connect(db)
    ver = conn.execute("PRAGMA user_version").fetchone()[0]
    conn.close()
    check(code == 2 and SM.E_BASELINE_MISMATCH in out and ver == 0,
          "AC-LM6 baseline refusal: drifted schema (extra table) refused"
          " with E_BASELINE_MISMATCH")
    # empty db -> nothing to adopt
    empty = os.path.join(tmp, "empty.db")
    sqlite3.connect(empty).close()
    code, out = run_cli(empty, "synth", "--baseline", chain=chain)
    check(code == 2 and SM.E_NO_BASELINE_TABLES in out,
          "AC-LM6 baseline refusal: empty db carries no baseline (E_NO_BASELINE_TABLES)")
    # double baseline -> only from version 0
    db2 = make_world(tmp, "world2.db")
    chain2 = write_chain(os.path.join(tmp, "chain2.json"), fp_of(db2), GOOD_STEPS)
    run_cli(db2, "synth", "--baseline", chain=chain2)
    code, out = run_cli(db2, "synth", "--baseline", chain=chain2)
    check(code == 2 and SM.E_MIGRATION_VERSION in out,
          "AC-LM6 baseline refusal: second adoption refused (E_MIGRATION_VERSION)")
    # migrate before baseline -> E_NEEDS_BASELINE
    db3 = make_world(tmp, "world3.db")
    chain3 = write_chain(os.path.join(tmp, "chain3.json"), fp_of(db3), GOOD_STEPS)
    code, out = run_cli(db3, "synth", "--migrate", chain=chain3)
    check(code == 2 and SM.E_NEEDS_BASELINE in out,
          "AC-LM6 unversioned non-empty db: migrate refuses until adopted"
          " (E_NEEDS_BASELINE)")


def _filemod(name, path):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


def build_domain_db(domain, tmp):
    """One live DB per production constructor (test_pay.py / test_member.py
    wiring posture); returns the main db path, all handles closed."""
    import ledger as ledger_mod
    lobby_store = _filemod("mig_lobby_store",
                           os.path.join(BASE, "lobby", "store.py"))
    led_cfg = load_json(os.path.join(BASE, "ledger", "config.json"))
    if domain == "ledger":
        led = ledger_mod.Ledger(os.path.join(tmp, "ledger.db"), led_cfg)
        led.close()
        return os.path.join(tmp, "ledger.db")
    if domain == "lobby":
        ev = lobby_store.EventStore(os.path.join(tmp, "events.db"))
        ev.close()
        return os.path.join(tmp, "events.db")
    if domain == "pay":
        import orders as orders_mod
        events = lobby_store.EventStore(os.path.join(tmp, "pay-events.db"))
        led = ledger_mod.Ledger(os.path.join(tmp, "pay-ledger.db"), led_cfg)
        pay = orders_mod.PayOrders(
            load_json(os.path.join(BASE, "pay", "config.json")),
            os.path.join(tmp, "pay.db"), events, led)
        pay.close()
        led.close()
        events.close()
        return os.path.join(tmp, "pay.db")
    if domain == "member":
        import orders as orders_mod
        import member as member_mod
        events = lobby_store.EventStore(os.path.join(tmp, "member-events.db"))
        led = ledger_mod.Ledger(os.path.join(tmp, "member-ledger.db"), led_cfg)
        pay = orders_mod.PayOrders(
            load_json(os.path.join(BASE, "pay", "config.json")),
            os.path.join(tmp, "member-pay.db"), events, led)
        store = member_mod.MemberStore(
            load_json(os.path.join(BASE, "member", "config.json")),
            os.path.join(tmp, "member.db"), pay)
        store.close()
        pay.close()
        led.close()
        events.close()
        return os.path.join(tmp, "member.db")
    if domain == "ugc":
        ugc_store = _filemod("mig_ugc_store",
                             os.path.join(BASE, "ugc", "store.py"))
        ug = ugc_store.UGCStore(os.path.join(tmp, "ugc.db"))
        ug.close()
        return os.path.join(tmp, "ugc.db")
    raise SystemExit("unknown domain %s" % domain)


def t_five_domain(domain):
    tmp = tempfile.mkdtemp(prefix="mig-five-")
    db = build_domain_db(domain, tmp)
    c1, s1 = run_cli(db, domain, "--status")
    c2, s2 = run_cli(db, domain, "--baseline")
    c3, s3 = run_cli(db, domain, "--status")
    c4, s4 = run_cli(db, domain, "--migrate")
    ok = (c1 == 0 and "current=0" in s1 and "needs_baseline=True" in s1
          and c2 == 0 and "user_version=1" in s2
          and c3 == 0 and "current=1 target=1 pending=[]" in s3
          and c4 == 0 and "user_version=1" in s4)
    check(ok, "AC-LM7 five-domain face [%s]: constructor db ->"
              " adopt -> status -> migrate round trip" % domain)


def t_five_domain_negative():
    tmp = tempfile.mkdtemp(prefix="mig-five-")
    db = build_domain_db("ledger", tmp)
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE t_drift_probe (a INTEGER)")
    conn.commit()
    conn.close()
    code, out = run_cli(db, "ledger", "--baseline")
    check(code == 2 and SM.E_BASELINE_MISMATCH in out,
          "AC-LM6/LM7 five-domain negative: drifted production schema"
          " refuses adoption")


def main():
    t_lm1_files()
    t_chain_format_guard()
    t_main_world()
    t_alter_ban()
    t_rowcount_abort()
    t_content_abort()
    t_baseline_refusals()
    for domain in ("ledger", "lobby", "pay", "member", "ugc"):
        t_five_domain(domain)
    t_five_domain_negative()
    print("SUITE PASS %d/%d" % (PASSES, PASSES + FAILS))
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
