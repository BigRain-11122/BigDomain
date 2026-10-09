"""Baseline fingerprint regenerator for migration_chains.json (R1713
tech-queue head item; AC-BF1..AC-BF7 were pre-registered in
state/queue/tech.md before this code existed - honesty law).

Purpose: the five frozen v1 baseline fingerprints in migration_chains.json
were live-collected in R1676 from each domain's standard constructor. If a
constructor drifts (schema change without a chain step), baseline adoption
would either misfire or silently adopt a wrong shape. This CLI re-derives
the fingerprints from the live constructors and compares them against the
frozen chain baselines - drift is FAIL (E_BASELINE_MISMATCH family,
reference not copy: fingerprint/_fp_diff/read_chains come from
schema_migrate.py, single source of truth, zero drift).

Faces, one line per criterion:
- AC-BF2 --check (default, read-only): per-domain PASS/FAIL rows plus a
  verdict line; all-equal exits 0, any drift exits 2 with the _fp_diff
  detail. The domain set is self-assembled from the chain file (new
  domains in the chain are checked automatically; a chain domain without
  constructor wiring FAILs with E_REGEN_NO_WIRING - fail-closed).
- AC-BF4 --update (re-freeze): refuses chains that carry steps
  (E_REGEN_STEPS_PRESENT - real schema changes go through the migration
  chain, not silent baseline re-freeze); validates the rewritten body with
  read_chains before any disk mutation; atomic tempfile+os.replace write;
  post-check self-run after the write; an undrifted --update is a
  byte-identical no-op (indent=2 + ensure_ascii=False + trailing newline
  round-trip fidelity).

Constructor wiring below is the twin of test_schema_migrate.py
build_domain_db (canonical wiring); keep the two in sync - the AC-BF5
cross-validation (live regen fingerprints == frozen R1676 baselines)
asserts the wiring agreement through the baselines themselves.

Stdlib only, ASCII source, zero network.
"""

import argparse
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
for _d in ("ledger", "pay", "member", "lobby"):
    _p = os.path.join(BASE, _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from schema_migrate import (  # noqa: E402  reference, not copy
    E_BASELINE_MISMATCH,
    MigrationError,
    _fp_diff,
    fingerprint,
    read_chains,
)

E_REGEN_STEPS_PRESENT = "E_REGEN_STEPS_PRESENT"  # AC-BF4 gate 1 refusal
E_REGEN_NO_WIRING = "E_REGEN_NO_WIRING"          # chain domain w/o ctor wiring


def _filemod(name, path):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


def _load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def build_domain_db(domain, tmp):
    """One live DB per production constructor - twin of
    test_schema_migrate.py build_domain_db; returns the main db path with
    all handles closed."""
    import ledger as ledger_mod
    lobby_store = _filemod("regen_lobby_store",
                           os.path.join(BASE, "lobby", "store.py"))
    led_cfg = _load_json(os.path.join(BASE, "ledger", "config.json"))
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
            _load_json(os.path.join(BASE, "pay", "config.json")),
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
            _load_json(os.path.join(BASE, "pay", "config.json")),
            os.path.join(tmp, "member-pay.db"), events, led)
        store = member_mod.MemberStore(
            _load_json(os.path.join(BASE, "member", "config.json")),
            os.path.join(tmp, "member.db"), pay)
        store.close()
        pay.close()
        led.close()
        events.close()
        return os.path.join(tmp, "member.db")
    if domain == "ugc":
        ugc_store = _filemod("regen_ugc_store",
                             os.path.join(BASE, "ugc", "store.py"))
        ug = ugc_store.UGCStore(os.path.join(tmp, "ugc.db"))
        ug.close()
        return os.path.join(tmp, "ugc.db")
    raise MigrationError(E_REGEN_NO_WIRING,
                         "no constructor wiring for chain domain %r" % domain)


def live_fingerprint(domain, tmp):
    """AC-BF5: derive the live fingerprint through the canonical
    constructor (fresh DB in tmp, read-only connect, close)."""
    db = build_domain_db(domain, tmp)
    conn = sqlite3.connect(db)
    try:
        return fingerprint(conn)
    finally:
        conn.close()


def check_rows(chain_path):
    """AC-BF2: build every chain domain's live fingerprint and compare it
    with the frozen baseline. Returns [(domain, ok, detail), ...];
    malformed chain file raises MigrationError (caller exits 2)."""
    chains = read_chains(chain_path)
    tmp = tempfile.mkdtemp(prefix="fpregen-")
    rows = []
    try:
        for domain in sorted(chains):
            want = chains[domain]["baseline"]["fingerprint"]
            try:
                live = live_fingerprint(domain, tmp)
            except MigrationError as exc:
                rows.append((domain, False,
                             "%s: %s" % (exc.code, exc.detail)))
                continue
            if live == want:
                rows.append((domain, True, ""))
            else:
                rows.append((domain, False, _fp_diff(want, live)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return rows


def _atomic_write(path, text):
    fd, tmp_path = tempfile.mkstemp(
        prefix=".fpregen-cand-", dir=os.path.dirname(os.path.abspath(path)))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def update_face(chain_path):
    """AC-BF4: re-freeze baselines from live constructors."""
    with open(chain_path, encoding="utf-8") as handle:
        raw = handle.read()
    data = json.loads(raw)
    chains = data["domains"]
    for domain in sorted(chains):
        steps = chains[domain].get("steps") or []
        if steps:
            raise MigrationError(
                E_REGEN_STEPS_PRESENT,
                "domain %s carries %d step(s); real schema changes go "
                "through the migration chain, not baseline re-freeze"
                % (domain, len(steps)))
    tmp = tempfile.mkdtemp(prefix="fpregen-upd-")
    try:
        changed = []
        for domain in sorted(chains):
            live = live_fingerprint(domain, tmp)
            if chains[domain]["baseline"]["fingerprint"] != live:
                chains[domain]["baseline"]["fingerprint"] = live
                changed.append(domain)
            print("UPDATED domain=%s" % domain, flush=True)
        new_text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        # gate 2: the rewritten body must structurally validate before any
        # disk mutation happens on the real chain file.
        candidate = os.path.join(tmp, "candidate.json")
        with open(candidate, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(new_text)
        read_chains(candidate)
        if new_text == raw:
            print("no-op: regenerated chains file is byte-identical", flush=True)
            print("verdict REGEN domains=%d changed=0" % len(chains), flush=True)
            return 0
        _atomic_write(chain_path, new_text)
        print("rewrote %s (changed domains: %s)" %
              (chain_path, ",".join(changed) or "none"), flush=True)
        rows = check_rows(chain_path)
        for domain, ok, detail in rows:
            if not ok:
                print("FAIL post-check domain=%s E_BASELINE_MISMATCH: %s"
                      % (domain, detail), flush=True)
                print("verdict REGEN post-check=DRIFT", flush=True)
                return 2
        print("post-check CLEAN domains=%d" % len(rows), flush=True)
        print("verdict REGEN domains=%d changed=%d" % (len(chains), len(changed)),
              flush=True)
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Regenerate/verify migration_chains.json baseline "
                    "fingerprints against live domain constructors "
                    "(drift is FAIL; --update re-freezes, refusing chains "
                    "that carry steps).")
    parser.add_argument("--chain", required=True,
                        help="migration_chains.json path")
    action = parser.add_mutually_exclusive_group(required=False)
    action.add_argument("--check", action="store_true",
                        help="compare live-derived fingerprints with the "
                             "chain baselines (default; read-only)")
    action.add_argument("--update", action="store_true",
                        help="re-freeze baselines from live constructors "
                             "(refuses chains with steps; atomic write + "
                             "post-check)")
    args = parser.parse_args(argv)

    if args.update:
        try:
            return update_face(args.chain)
        except MigrationError as exc:
            print("%s: %s" % (exc.code, exc.detail))
            return 2
    try:
        rows = check_rows(args.chain)
    except MigrationError as exc:
        print("%s: %s" % (exc.code, exc.detail))
        return 2
    drift = 0
    for domain, ok, detail in rows:
        if ok:
            print("PASS domain=%s baseline matches live constructor "
                  "(R1676 cross-validation)" % domain, flush=True)
        else:
            drift += 1
            print("FAIL domain=%s %s: %s" % (domain, E_BASELINE_MISMATCH, detail),
                  flush=True)
    if drift:
        print("verdict DRIFT domains=%d/%d" % (drift, len(rows)), flush=True)
        return 2
    print("verdict CLEAN domains=%d" % len(rows), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
