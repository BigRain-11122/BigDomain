"""Schema versioning migrator for the BigDomain sandbox databases
(P-47 tech-infrastructure candidate; claimed as the O-20261009-1246
dispatch-d head item; acceptance criteria AC-LM1..AC-LM11 were
pre-registered in state/queue/tech.md before this code existed -
honesty law).

Chain law, one line per criterion:
- AC-LM2 versioning: PRAGMA user_version carries the schema version;
  each step runs inside one BEGIN IMMEDIATE transaction and the version
  is stamped only inside that transaction, so a failed step never moves
  the version.
- AC-LM3 forward-only: the chain is append-only; a step numbered at or
  below the current version is refused (no downgrade path exists).
- AC-LM4 ALTER-free: ALTER TABLE is banned structurally - step SQL that
  carries it is refused before anything runs. Table shape changes use
  the rebuild pattern instead, and the rebuild swap itself is ALTER-free
  (drop old -> create final -> copy -> verify -> drop staging; two
  full-fidelity copies, two verifications, zero ALTER anywhere).
- AC-LM5 dual-phase transition: during a rebuild the old and new
  representations coexist (the copy window). The swap is gated by
  agreement criteria - row count equal, then full mapped-column row
  multiset equal; any mismatch aborts the whole step with
  E_MIGRATION_VERIFY and the transaction rolls back (old table rows
  intact, no staging leftovers, version unchanged).
- AC-LM6 baseline adoption: an existing unversioned DB (user_version=0
  with user tables) is adopted by --baseline after its live fingerprint
  (user-table set with per-table column signatures from PRAGMA
  table_info, plus trigger/view/index name sets) matches the chain v1
  baseline; anything else refuses with E_BASELINE_MISMATCH.
- AC-LM7/AC-LM11 five-domain isomorphic face: one framework, one chain
  schema, five production chains (ledger/lobby/member/pay/ugc) shipping
  with empty step lists - production schemas and constructors stay
  untouched; a real schema change lands as an appended chain step.

Chain data lives in migration_chains.json next to this file (R563
data-externalization precedent). Rebuild DDL and triggers use the token
"@new" where the staging table name belongs; the framework substitutes
<table>__mig_new. Stdlib only, ASCII source, zero network.
"""

import argparse
import json
import os
import re
import sqlite3

E_MIGRATION_VERSION = "E_MIGRATION_VERSION"   # AC-LM3 forward-only refusal
E_ALTER_BANNED = "E_ALTER_BANNED"             # AC-LM4 structural ALTER ban
E_MIGRATION_VERIFY = "E_MIGRATION_VERIFY"     # AC-LM5 dual-phase criteria
E_BASELINE_MISMATCH = "E_BASELINE_MISMATCH"   # AC-LM6 adoption refusal
E_NEEDS_BASELINE = "E_NEEDS_BASELINE"         # unversioned non-empty DB
E_NO_BASELINE_TABLES = "E_NO_BASELINE_TABLES" # empty DB cannot adopt
E_CHAIN_FORMAT = "E_CHAIN_FORMAT"             # malformed chain file
E_UNKNOWN_DOMAIN = "E_UNKNOWN_DOMAIN"

STAGING_SUFFIX = "__mig_new"
NEW_TOKEN = "@new"

_ALTER_RE = re.compile(r"\bALTER\s+TABLE\b", re.IGNORECASE)


class MigrationError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


def quote_ident(name):
    return '"' + str(name).replace('"', '""') + '"'


def _check_no_alter(sql, where):
    if sql and _ALTER_RE.search(sql):
        raise MigrationError(E_ALTER_BANNED, "%s: %s" % (where, (sql or "").strip()[:120]))


def _master_names(conn, kind):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = ? AND name NOT LIKE 'sqlite_%'"
        " ORDER BY name", (kind,)).fetchall()
    return [r[0] for r in rows]


def _table_exists(conn, name):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (name,)).fetchone()
    return row is not None


def fingerprint(conn):
    """Live schema fingerprint (AC-LM6): user-table set with per-table
    column signatures (name/type/notnull/default/pk from PRAGMA
    table_info), plus trigger/view/index name sets."""
    tables = {}
    for name in _master_names(conn, "table"):
        cols = conn.execute("PRAGMA table_info(%s)" % quote_ident(name)).fetchall()
        tables[name] = [[c[1], str(c[2] or ""), int(c[3]),
                         None if c[4] is None else str(c[4]), int(c[5])]
                        for c in cols]
    return {
        "tables": tables,
        "triggers": _master_names(conn, "trigger"),
        "views": _master_names(conn, "view"),
        "indexes": _master_names(conn, "index"),
    }


def _fp_diff(want, live):
    parts = []
    wt = want.get("tables") or {}
    lt = live.get("tables") or {}
    if set(wt) != set(lt):
        parts.append("tables want=%s live=%s" % (sorted(wt), sorted(lt)))
    else:
        drift = [t for t in sorted(wt) if wt[t] != lt.get(t)]
        if drift:
            parts.append("column signature drift: %s" % drift)
    for face in ("triggers", "views", "indexes"):
        w = want.get(face) or []
        l = live.get(face) or []
        if w != l:
            parts.append("%s want=%s live=%s" % (face, w, l))
    return "; ".join(parts) or "fingerprint mismatch"


def read_chains(path):
    """Load and structurally validate the chain file (fail-closed)."""
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("domains"), dict):
        raise MigrationError(E_CHAIN_FORMAT, "domains map missing")
    for domain, chain in sorted(data["domains"].items()):
        if not isinstance(chain, dict):
            raise MigrationError(E_CHAIN_FORMAT, "domain %s not an object" % domain)
        base = (chain.get("baseline") or {}).get("fingerprint")
        if not isinstance(base, dict) or not isinstance(base.get("tables"), dict):
            raise MigrationError(E_CHAIN_FORMAT,
                                 "domain %s baseline fingerprint missing" % domain)
        steps = chain.get("steps")
        if steps is None:
            steps = []
        if not isinstance(steps, list):
            raise MigrationError(E_CHAIN_FORMAT, "domain %s steps not a list" % domain)
        last = 1
        for step in steps:
            try:
                version = int(step["version"])
                ops = step["ops"]
            except (KeyError, TypeError, ValueError):
                raise MigrationError(E_CHAIN_FORMAT,
                                     "domain %s malformed step %r" % (domain, step)) from None
            if version <= last:
                raise MigrationError(E_CHAIN_FORMAT,
                                     "domain %s step versions must increase from 2"
                                     " (got %d after %d)" % (domain, version, last))
            last = version
            if not isinstance(ops, list) or not ops:
                raise MigrationError(E_CHAIN_FORMAT,
                                     "domain %s step %d needs a non-empty ops list"
                                     % (domain, version))
            for op in ops:
                if not isinstance(op, dict) or op.get("kind") not in ("sql", "rebuild"):
                    raise MigrationError(E_CHAIN_FORMAT,
                                         "domain %s step %d bad op %r"
                                         % (domain, version, op))
                if op["kind"] == "sql" and not str(op.get("sql") or "").strip():
                    raise MigrationError(E_CHAIN_FORMAT,
                                         "domain %s step %d empty sql op" % (domain, version))
                if op["kind"] == "rebuild":
                    if not str(op.get("new_ddl") or "").strip():
                        raise MigrationError(E_CHAIN_FORMAT,
                                             "domain %s step %d rebuild without new_ddl"
                                             % (domain, version))
                    cols = op.get("columns")
                    if not isinstance(cols, list) or not cols:
                        raise MigrationError(E_CHAIN_FORMAT,
                                             "domain %s step %d rebuild without columns"
                                             % (domain, version))
                    for col in cols:
                        if not isinstance(col, dict) or "new" not in col or "old" not in col:
                            raise MigrationError(E_CHAIN_FORMAT,
                                                 "domain %s step %d bad column map %r"
                                                 % (domain, version, col))
    return data["domains"]


class SchemaMigrator:
    """One database + one chain. Single writer discipline: the caller owns
    the write window (same posture as the sandbox stores)."""

    def __init__(self, db_path, chain):
        self.db_path = db_path
        self.chain = chain
        parent = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(parent, exist_ok=True)
        self.conn = sqlite3.connect(db_path, isolation_level=None)

    def close(self):
        self.conn.close()

    # -- version faces -------------------------------------------------------

    def version(self):
        return int(self.conn.execute("PRAGMA user_version").fetchone()[0])

    def target_version(self):
        steps = self.chain.get("steps") or []
        return max([1] + [int(s["version"]) for s in steps])

    def has_tables(self):
        return len(_master_names(self.conn, "table")) > 0

    def status(self):
        cur = self.version()
        pending = [int(s["version"]) for s in (self.chain.get("steps") or [])
                   if int(s["version"]) > cur]
        return {"current": cur, "target": self.target_version(),
                "pending": pending,
                "needs_baseline": cur == 0 and self.has_tables()}

    # -- AC-LM6 baseline adoption ---------------------------------------------

    def baseline(self):
        if self.version() != 0:
            raise MigrationError(E_MIGRATION_VERSION,
                                 "baseline only from user_version=0 (current=%d)"
                                 % self.version())
        if not self.has_tables():
            raise MigrationError(E_NO_BASELINE_TABLES, "no user tables to adopt")
        live = fingerprint(self.conn)
        want = self.chain["baseline"]["fingerprint"]
        if live != want:
            raise MigrationError(E_BASELINE_MISMATCH, _fp_diff(want, live))
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            self.conn.execute("PRAGMA user_version = 1")
            self.conn.execute("COMMIT")
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise
        return 1

    # -- AC-LM2/LM3 forward chain ----------------------------------------------

    def migrate(self):
        state = self.status()
        if state["needs_baseline"]:
            raise MigrationError(E_NEEDS_BASELINE,
                                 "unversioned non-empty db - run --baseline first")
        if not state["pending"]:
            return state["current"]
        for step in sorted(self.chain.get("steps") or [],
                           key=lambda s: int(s["version"])):
            if int(step["version"]) <= self.version():
                continue  # already applied; defensive (AC-LM3 also refuses)
            self._apply_step(step)
        return self.version()

    def _apply_step(self, step):
        version = int(step["version"])
        if version <= self.version():
            raise MigrationError(E_MIGRATION_VERSION,
                                 "step %d at/below current %d (forward-only chain)"
                                 % (version, self.version()))
        # AC-LM4: structural ALTER ban, checked before anything runs.
        for op in step["ops"]:
            if op["kind"] == "sql":
                _check_no_alter(op.get("sql"), "step %d sql op" % version)
            else:
                _check_no_alter(op.get("new_ddl"), "step %d rebuild new_ddl" % version)
                for trig in op.get("triggers") or []:
                    _check_no_alter(trig, "step %d rebuild trigger" % version)
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            for op in step["ops"]:
                if op["kind"] == "sql":
                    self.conn.execute(op["sql"])
                else:
                    self._rebuild(op)
            self.conn.execute("PRAGMA user_version = %d" % version)
            self.conn.execute("COMMIT")
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise

    # -- AC-LM4/LM5 ALTER-free rebuild with dual-phase transition ----------------

    def _rebuild(self, op):
        table = str(op["table"])
        staging = table + STAGING_SUFFIX
        if _table_exists(self.conn, staging):
            raise MigrationError(E_MIGRATION_VERIFY,
                                 "leftover staging table %s" % staging)
        new_cols = ", ".join(quote_ident(c["new"]) for c in op["columns"])
        old_exprs = ", ".join(str(c["old"]) for c in op["columns"])
        # dual phase 1: copy old -> staging (both representations coexist)
        self.conn.execute(op["new_ddl"].replace(NEW_TOKEN, staging))
        for trig in op.get("triggers") or []:
            self.conn.execute(trig.replace(NEW_TOKEN, staging))
        self.conn.execute(
            "INSERT INTO %s (%s) SELECT %s FROM %s"
            % (quote_ident(staging), new_cols, old_exprs, quote_ident(table)))
        self._verify_copy(table, old_exprs, staging, new_cols)
        # swap without ALTER: drop old, create final, copy, verify, drop staging
        self.conn.execute("DROP TABLE %s" % quote_ident(table))
        self.conn.execute(op["new_ddl"].replace(NEW_TOKEN, table))
        self.conn.execute(
            "INSERT INTO %s (%s) SELECT %s FROM %s"
            % (quote_ident(table), new_cols, new_cols, quote_ident(staging)))
        self._verify_copy(staging, new_cols, table, new_cols)
        self.conn.execute("DROP TABLE %s" % quote_ident(staging))

    def _verify_copy(self, source, source_exprs, dest, dest_cols):
        """AC-LM5 criteria: row count equal, then full mapped-column row
        multiset equal. Any mismatch aborts the whole step."""
        n_src = self.conn.execute(
            "SELECT COUNT(*) FROM %s" % quote_ident(source)).fetchone()[0]
        n_dst = self.conn.execute(
            "SELECT COUNT(*) FROM %s" % quote_ident(dest)).fetchone()[0]
        if n_src != n_dst:
            raise MigrationError(E_MIGRATION_VERIFY,
                                 "rowcount %s=%d %s=%d" % (source, n_src, dest, n_dst))
        src_rows = self.conn.execute(
            "SELECT %s FROM %s" % (source_exprs, quote_ident(source))).fetchall()
        dst_rows = self.conn.execute(
            "SELECT %s FROM %s" % (dest_cols, quote_ident(dest))).fetchall()
        src_sorted = sorted((list(r) for r in src_rows), key=repr)
        dst_sorted = sorted((list(r) for r in dst_rows), key=repr)
        if src_sorted != dst_sorted:
            raise MigrationError(E_MIGRATION_VERIFY,
                                 "mapped-content mismatch %s vs %s" % (source, dest))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Sandbox schema migrator (PRAGMA user_version chain, "
                    "ALTER-free forward migration, dual-phase verify).")
    parser.add_argument("--chain", required=True, help="migration_chains.json path")
    parser.add_argument("--domain", required=True, help="chain domain name")
    parser.add_argument("--db", required=True, help="sqlite db path")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--status", action="store_true",
                        help="print current/target/pending state")
    action.add_argument("--baseline", action="store_true",
                        help="adopt an existing unversioned db as chain v1")
    action.add_argument("--migrate", action="store_true",
                        help="apply pending forward steps")
    action.add_argument("--fingerprint", action="store_true",
                        help="print the live schema fingerprint json")
    args = parser.parse_args(argv)

    try:
        chains = read_chains(args.chain)
    except MigrationError as exc:
        print("%s: %s" % (exc.code, exc.detail))
        return 2
    if args.domain not in chains:
        print("%s: %s (known: %s)" % (E_UNKNOWN_DOMAIN, args.domain,
                                      ",".join(sorted(chains))))
        return 2
    mig = SchemaMigrator(args.db, chains[args.domain])
    try:
        if args.fingerprint:
            print(json.dumps(fingerprint(mig.conn), sort_keys=True))
            return 0
        if args.status:
            state = mig.status()
            print("status domain=%s current=%d target=%d pending=%s needs_baseline=%s"
                  % (args.domain, state["current"], state["target"],
                     state["pending"], state["needs_baseline"]))
            return 0
        if args.baseline:
            version = mig.baseline()
            print("baseline ok domain=%s user_version=%d" % (args.domain, version))
            return 0
        version = mig.migrate()
        print("migrate ok domain=%s user_version=%d" % (args.domain, version))
        return 0
    except MigrationError as exc:
        print("%s: %s" % (exc.code, exc.detail))
        return 2
    finally:
        mig.close()


if __name__ == "__main__":
    raise SystemExit(main())
