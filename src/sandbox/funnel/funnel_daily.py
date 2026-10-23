"""Commercialization funnel daily ring v0.1 (BigDomain FUNNEL-LOOP,
R2032; canon = docs/ops/FUNNEL-AUTOMATION-PLAN-v1.md - the BigDomain
sub-plan of GROUP-AUTOMATION-PLAN-v1.md item 4, CEO order chain
2026-10-18 20:54 / 21:11 / 23:46).

Four rings in series on a daily cadence, per the group plan item 4:

  ring 1  lead scan        leads inbox   -> leads   (lead_id idem,
         domain pre-classification by keyword match, honest fallback)
  ring 2  co-creation dispatch           -> dispatches (six-domain
         keyword routing; no-match = unrouted honest archive,
         never dropped)
  ring 3  order bookkeeping orders inbox  -> orders  (order_id idem)
  ring 4  token flow ledger flows inbox   -> flows   (flow_id idem,
         grant/spend dual kind; three-face daily account with the
         outstanding == granted - spent identity)
  rollup  daily counts + prev-day delta + a one-line good/flat
         verdict + the focus (positioning-law self-check line) + the
         standing AIGC label line, gated by the pre-commercialization
         lightweight compliance gate.

Design verdicts (registered BEFORE this code existed, honesty law -
docs/ops/FUNNEL-AUTOMATION-PLAN-v1.md section 4, AC-FN1..AC-FN7):

  - carrier: an independent SQLite file (single writer). Source
    tables (leads / dispatches / orders / flows) are append-only:
    INSERT OR IGNORE on natural keys, zero mutation statements for
    source rows. The rollups table is a derived summary face: re-
    running the same day re-derives it; with unchanged inputs the
    rewrite is byte-identical (AC-FN1), so the overwrite is honest.
  - pre-commercialization honesty: zero real leads / orders / flows
    is the expected steady state until the CEO physical prerequisites
    (merchant id, servers, domain, filing) arrive. Every ring books
    honest zero counts - never an error, never a fabricated count.
    The collection gate stays CLOSED (BLUEPRINT price-canon law):
    this ring is bookkeeping only, never a payment or launch surface.
  - determinism: the day is a caller-injected parameter; the wall
    clock is never read. Same inboxes + same day => byte-identical
    rollup envelope (AC-FN1).
  - gate scope (honest boundary): the lightweight gate scans the
    rollup envelope - the company-presented summary face - for the
    BLUEPRINT section 5.8 banned-word family. User-supplied lead
    text is a data face, not a presented face: content safety for
    user text belongs to the UGC msgSecCheck pipeline (referenced,
    not rebuilt here). A hit => gate=FAIL with the hit list
    persisted, fail-closed.
  - banned words and standing lines live in config.json (a UTF-8
    data file; this .py source stays pure ASCII - coding law).
  - inbox hygiene: an inbox entry is a regular file with the exact
    lower-case .json suffix; every other entry (other suffixes,
    directories) is junk and is skipped without being opened. Every
    in-contract file is read and fully validated BEFORE any row of
    that ring is written (all-or-nothing per ring; a bad file means
    E_FN_BAD_ARGS and zero new rows - the zero-row rejection law).

Hard laws: append-only source rows, zero dice, zero network
imports, zero wall-clock reads, pure ASCII source.
"""

import datetime
import json
import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(BASE, "config.json")


def default_paths():
    """Absolute carrier defaults, anchored to THIS module (AC-FCW, R2064).

    The CLI defaults must not depend on the caller's working directory:
    the state face is derived from the module file's own location, so a
    run from any cwd lands on the same repo-root state/funnel carrier.
    Explicitly passed paths stay the caller's business (cwd-relative
    strings are honoured as given) - two separate laws.

    Pure read by construction: it only joins strings, so calling it can
    never create a carrier, an inbox or an evidence directory.
    """
    state_face = os.path.normpath(
        os.path.join(BASE, "..", "..", "..", "state", "funnel"))
    return {
        "base": BASE,
        "state_face": state_face,
        "db": os.path.join(state_face, "funnel.db"),
        "leads_inbox": os.path.join(state_face, "inbox", "leads"),
        "orders_inbox": os.path.join(state_face, "inbox", "orders"),
        "flows_inbox": os.path.join(state_face, "inbox", "flows"),
        "config": DEFAULT_CONFIG,
    }

E_FN_BAD_ARGS = "E_FN_BAD_ARGS"

DOMAIN_ROUTES = (
    ("game", ("game", "play", "level", "character", "demo")),
    ("quant", ("strategy", "backtest", "quant", "factor", "etf")),
    ("media", ("video", "clip", "script", "subtitle")),
    ("life", ("resident", "persona", "story", "birth")),
    ("city", ("building", "district", "landmark", "street")),
    ("platform", ("platform", "feature", "billing", "subscription")),
)
LEAD_FALLBACK = "other"
FLOW_KINDS = ("grant", "spend")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
  lead_id TEXT PRIMARY KEY,
  day TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT '',
  domain TEXT NOT NULL,
  text TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS dispatches (
  lead_id TEXT PRIMARY KEY,
  day TEXT NOT NULL,
  route TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
  order_id TEXT PRIMARY KEY,
  day TEXT NOT NULL,
  sku TEXT NOT NULL DEFAULT '',
  amount_cent INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS flows (
  flow_id TEXT PRIMARY KEY,
  day TEXT NOT NULL,
  account TEXT NOT NULL DEFAULT '',
  kind TEXT NOT NULL,
  amount INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS rollups (
  day TEXT PRIMARY KEY,
  envelope TEXT NOT NULL,
  gate TEXT NOT NULL,
  hits TEXT NOT NULL DEFAULT '[]'
);
"""

_COUNT_KEYS = (
    "leads_day",
    "dispatches_day",
    "orders_day",
    "token_granted_day",
    "token_spent_day",
    "token_outstanding_total",
)


class FunnArgError(ValueError):
    """Raised as E_FN_BAD_ARGS - every raise means zero new rows."""


def _assert_day(day):
    if not isinstance(day, str):
        raise FunnArgError(E_FN_BAD_ARGS)
    try:
        datetime.date.fromisoformat(day)
    except ValueError:
        raise FunnArgError(E_FN_BAD_ARGS)


def _assert_inbox(inbox_dir):
    if not isinstance(inbox_dir, str) or not os.path.isdir(inbox_dir):
        raise FunnArgError(E_FN_BAD_ARGS)


def _sku_text(value):
    """Canonical text form of an order sku (R2061, AC-FSK family).

    The orders.sku column is a NOT NULL descriptive text field, so an
    absent sku is the honest blank bucket (""), never an error. A JSON
    scalar has a deterministic text form and is stringified exactly:
    text verbatim, integers as decimal digits, floats via their
    shortest repr, booleans as the lower-case JSON literals "true" /
    "false" (never Python's "True"). A container (list / dict) has no
    stable data identity - its repr is a language artifact, not data -
    so it rejects the whole ring with E_FN_BAD_ARGS under the zero-row
    law instead of booking garbage the read faces would then have to
    carry forever.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return "%d" % value
    if isinstance(value, float):
        return repr(value)
    raise FunnArgError(E_FN_BAD_ARGS)


def _classify_lead(text):
    low = str(text).lower()
    for domain, keys in DOMAIN_ROUTES:
        for key in keys:
            if key in low:
                return domain
    return LEAD_FALLBACK


class FunnelDaily:
    """Daily four-ring funnel carrier over one SQLite file."""

    def __init__(self, db_path, config_path=DEFAULT_CONFIG):
        if not isinstance(db_path, str) or not db_path:
            raise FunnArgError(E_FN_BAD_ARGS)
        with open(config_path, encoding="utf-8") as handle:
            cfg = json.load(handle)
        words = cfg.get("banned_words")
        lines = cfg.get("standing_lines")
        if not isinstance(words, list) or not isinstance(lines, dict):
            raise FunnArgError(E_FN_BAD_ARGS)
        self.banned_words = tuple(str(w) for w in words)
        self.standing_lines = lines
        self.db = sqlite3.connect(db_path)
        self.db.executescript(_SCHEMA)
        self.db.commit()

    def close(self):
        self.db.close()

    # ---- shared inbox loader (all-or-nothing per ring) ----

    def _load_inbox(self, inbox_dir):
        """Read one inbox directory under the classification law.

        An inbox entry is a REGULAR FILE whose name ends in the exact
        lower-case suffix ".json" - that is the whole inbox contract.
        Everything else is junk and is skipped honestly, never opened
        and never recursed into: other suffixes (including .JSON /
        .Json - suffix matching is byte-exact), bare names, and
        directories (even one literally named "fake.json", which is a
        directory, not a file). Junk is a data-face hygiene matter, not
        an error.

        A file that IS in the contract but cannot be honoured - bad
        JSON text, invalid UTF-8, an unreadable file, or a decoded
        value that is not an object - rejects the whole ring with
        E_FN_BAD_ARGS before any row of that ring is written (the
        zero-row rejection law). Every such face raises FunnArgError:
        no JSONDecodeError / UnicodeDecodeError / IsADirectoryError
        escapes the library boundary.
        """
        _assert_inbox(inbox_dir)
        rows = []
        for name in sorted(os.listdir(inbox_dir)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(inbox_dir, name)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, encoding="utf-8") as h:
                    item = json.load(h)
            except (ValueError, OSError):
                raise FunnArgError(E_FN_BAD_ARGS)
            if not isinstance(item, dict):
                raise FunnArgError(E_FN_BAD_ARGS)
            rows.append(item)
        return rows

    # ---- ring 1: lead scan ----

    def scan_leads(self, inbox_dir, day):
        _assert_day(day)
        rows = self._load_inbox(inbox_dir)
        for item in rows:
            lead_id = item.get("lead_id")
            if not isinstance(lead_id, str) or not lead_id:
                raise FunnArgError(E_FN_BAD_ARGS)
        seen, new = 0, 0
        for item in rows:
            seen += 1
            cur = self.db.execute(
                "INSERT OR IGNORE INTO leads "
                "(lead_id, day, source, domain, text) VALUES (?,?,?,?,?)",
                (
                    item["lead_id"],
                    day,
                    str(item.get("source", "")),
                    _classify_lead(item.get("text", "")),
                    str(item.get("text", "")),
                ),
            )
            new += cur.rowcount
        self.db.commit()
        return {"files_leads": len(rows), "leads_seen": seen, "leads_new": new}

    # ---- ring 2: co-creation dispatch ----

    def dispatch_leads(self, day):
        _assert_day(day)
        pending = self.db.execute(
            "SELECT lead_id, domain FROM leads ORDER BY lead_id"
        ).fetchall()
        new = 0
        routes = {}
        for lead_id, domain in pending:
            route = domain if domain != LEAD_FALLBACK else "unrouted"
            cur = self.db.execute(
                "INSERT OR IGNORE INTO dispatches (lead_id, day, route) "
                "VALUES (?,?,?)",
                (lead_id, day, route),
            )
            if cur.rowcount:
                new += 1
                routes[route] = routes.get(route, 0) + 1
        self.db.commit()
        return {"dispatches_new": new, "routes": routes}

    # ---- ring 3: order bookkeeping ----

    def book_orders(self, inbox_dir, day):
        _assert_day(day)
        rows = self._load_inbox(inbox_dir)
        for item in rows:
            order_id = item.get("order_id")
            if not isinstance(order_id, str) or not order_id:
                raise FunnArgError(E_FN_BAD_ARGS)
            amount = item.get("amount_cent", 0)
            if not isinstance(amount, int) or amount < 0:
                raise FunnArgError(E_FN_BAD_ARGS)
            _sku_text(item.get("sku", ""))
        seen, new = 0, 0
        for item in rows:
            seen += 1
            cur = self.db.execute(
                "INSERT OR IGNORE INTO orders "
                "(order_id, day, sku, amount_cent) VALUES (?,?,?,?)",
                (item["order_id"], day, _sku_text(item.get("sku", "")),
                 item.get("amount_cent", 0)),
            )
            new += cur.rowcount
        self.db.commit()
        return {"orders_seen": seen, "orders_new": new}

    # ---- ring 4: token flow ledger ----

    def book_token_flows(self, inbox_dir, day):
        _assert_day(day)
        rows = self._load_inbox(inbox_dir)
        for item in rows:
            flow_id = item.get("flow_id")
            kind = item.get("kind")
            amount = item.get("amount")
            if not isinstance(flow_id, str) or not flow_id:
                raise FunnArgError(E_FN_BAD_ARGS)
            if kind not in FLOW_KINDS:
                raise FunnArgError(E_FN_BAD_ARGS)
            if not isinstance(amount, int) or amount < 1:
                raise FunnArgError(E_FN_BAD_ARGS)
        seen, new = 0, 0
        for item in rows:
            seen += 1
            cur = self.db.execute(
                "INSERT OR IGNORE INTO flows "
                "(flow_id, day, account, kind, amount) VALUES (?,?,?,?,?)",
                (
                    item["flow_id"],
                    day,
                    str(item.get("account", "")),
                    item["kind"],
                    item["amount"],
                ),
            )
            new += cur.rowcount
        self.db.commit()
        return {"flows_seen": seen, "flows_new": new}

    # ---- per-account token ledger read face ----

    def account_ledger(self, day=None):
        """Per-account granted/spent/outstanding read face (R2053).

        A pure read over the append-only flows table (zero writes, zero
        cache, no wall clock): one row per account that appears in the
        window, in sorted-account order, each carrying the three keys.
        The blank account ("") is a legitimate bucket of its own - a
        flow row may honestly carry no account yet - and is never
        merged into a named account. An account whose spend exceeds its
        grant reports a negative outstanding (honest overdraft, never
        clamped to zero). Window law: day=None reads the lifetime
        ledger; an explicit day reads only that day's rows; a day with
        no rows is an honest empty face ({}), not an error. A bad day
        form raises E_FN_BAD_ARGS before any row is touched.
        """
        if day is not None:
            _assert_day(day)
        sql = ("SELECT account, kind, COALESCE(SUM(amount),0) "
               "FROM flows WHERE 1=1")
        params = []
        if day is not None:
            sql += " AND day=?"
            params.append(day)
        sql += " GROUP BY account, kind"
        accounts = {}
        for account, kind, total in self.db.execute(sql, params).fetchall():
            bucket = accounts.setdefault(
                str(account), {"granted": 0, "spent": 0})
            if kind == "grant":
                bucket["granted"] = int(total)
            elif kind == "spend":
                bucket["spent"] = int(total)
        out = {}
        for account in sorted(accounts):
            bucket = accounts[account]
            out[account] = {
                "granted": bucket["granted"],
                "spent": bucket["spent"],
                "outstanding": bucket["granted"] - bucket["spent"],
            }
        return out

    # ---- per-sku order totals read face ----

    def sku_totals(self, day=None):
        """Per-sku order totals read face (R2054, AC-FST1..AC-FST8).

        A pure read over the append-only orders table (zero writes,
        zero cache, no wall clock): one bucket per sku that appears in
        the window, carrying the order count and the summed
        amount_cent, in ascending sku (byte) order. The blank sku ("")
        is a legitimate bucket of its own - an order row may honestly
        carry no sku yet - and is never merged into a named sku.
        Window law: day=None reads the lifetime order book; an
        explicit day reads only that day's rows; a day with no rows is
        an honest empty face ({}), not an error. A bad day form raises
        E_FN_BAD_ARGS before any row is touched.
        """
        if day is not None:
            _assert_day(day)
        sql = ("SELECT sku, COUNT(*), COALESCE(SUM(amount_cent),0) "
               "FROM orders WHERE 1=1")
        params = []
        if day is not None:
            sql += " AND day=?"
            params.append(day)
        sql += " GROUP BY sku ORDER BY sku"
        out = {}
        for sku, count, amount in self.db.execute(sql, params).fetchall():
            out[str(sku)] = {
                "orders": int(count),
                "amount_cent": int(amount),
            }
        return out

    # ---- ranked per-sku order totals read face ----

    def sku_top(self, limit, day=None):
        """Ranked per-sku order totals read face (R2059, AC-FTP1..AC-FTP8).

        A pure read built on top of sku_totals (zero extra SQL, zero
        writes, zero cache, no wall clock): the same buckets, sorted by
        summed amount_cent descending with ties broken by ascending sku
        (byte) order, cut to the first `limit` buckets. Each row is
        {rank, sku, orders, amount_cent} with rank starting at 1 and
        running without gaps. The blank sku is an ordinary bucket of its
        own and competes for rank like any named bucket.

        Window law matches sku_totals: day=None ranks the lifetime order
        book; an explicit day ranks that day only; a day with no rows is
        an honest empty list ([]), never padding or phantom rows. A
        non-positive or non-integer limit raises E_FN_BAD_ARGS before any
        row is touched - a top-n face with n < 1 is meaningless, so it
        fails closed rather than returning an empty list.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise FunnArgError(E_FN_BAD_ARGS)
        totals = self.sku_totals(day)
        ranked = sorted(totals.items(),
                        key=lambda pair: (-pair[1]["amount_cent"], pair[0]))
        out = []
        for rank, (sku, bucket) in enumerate(ranked[:limit], 1):
            out.append({
                "rank": rank,
                "sku": sku,
                "orders": bucket["orders"],
                "amount_cent": bucket["amount_cent"],
            })
        return out

    # ---- dispatch route distribution read face ----

    def route_tally(self, day=None):
        """Dispatch route distribution read face (R2055, AC-FRT1..AC-FRT8).

        A pure read over the append-only dispatches table (zero writes,
        zero cache, no wall clock): one bucket per route that appears
        in the window, carrying the dispatch count, in ascending route
        (byte) order. The "unrouted" bucket is the honest no-match
        archive and is never merged into a named route; a route outside
        the six-domain table (only reachable through a direct row
        write) keeps its own key instead of being dropped. Window law:
        day=None reads the lifetime distribution; an explicit day
        reads only that day's rows; a day with no rows is an honest
        empty face ({}), not an error. A bad day form raises
        E_FN_BAD_ARGS before any row is touched.
        """
        if day is not None:
            _assert_day(day)
        sql = "SELECT route, COUNT(*) FROM dispatches WHERE 1=1"
        params = []
        if day is not None:
            sql += " AND day=?"
            params.append(day)
        sql += " GROUP BY route ORDER BY route"
        out = {}
        for route, count in self.db.execute(sql, params).fetchall():
            out[str(route)] = int(count)
        return out

    # ---- rollup + lightweight compliance gate ----

    def rollup(self, day):
        _assert_day(day)
        counts = {
            "leads_day": self.db.execute(
                "SELECT COUNT(*) FROM leads WHERE day=?", (day,)
            ).fetchone()[0],
            "dispatches_day": self.db.execute(
                "SELECT COUNT(*) FROM dispatches WHERE day=?", (day,)
            ).fetchone()[0],
            "orders_day": self.db.execute(
                "SELECT COUNT(*) FROM orders WHERE day=?", (day,)
            ).fetchone()[0],
            "token_granted_day": self.db.execute(
                "SELECT COALESCE(SUM(amount),0) FROM flows "
                "WHERE day=? AND kind='grant'",
                (day,),
            ).fetchone()[0],
            "token_spent_day": self.db.execute(
                "SELECT COALESCE(SUM(amount),0) FROM flows "
                "WHERE day=? AND kind='spend'",
                (day,),
            ).fetchone()[0],
        }
        granted_total = self.db.execute(
            "SELECT COALESCE(SUM(amount),0) FROM flows WHERE kind='grant'"
        ).fetchone()[0]
        spent_total = self.db.execute(
            "SELECT COALESCE(SUM(amount),0) FROM flows WHERE kind='spend'"
        ).fetchone()[0]
        counts["token_outstanding_total"] = granted_total - spent_total

        prev_day = (
            datetime.date.fromisoformat(day) - datetime.timedelta(days=1)
        ).isoformat()
        prev_row = self.db.execute(
            "SELECT envelope FROM rollups WHERE day=?", (prev_day,)
        ).fetchone()
        delta = None
        if prev_row is not None:
            prev_env = json.loads(prev_row[0])
            prev_counts = prev_env.get("counts", {})
            delta = {}
            for key in _COUNT_KEYS:
                delta[key] = counts[key] - prev_counts.get(key, 0)

        moved = (
            counts["leads_day"]
            + counts["dispatches_day"]
            + counts["orders_day"]
            + counts["token_granted_day"]
            + counts["token_spent_day"]
        )
        if moved:
            verdict = (
                "good: funnel advanced - leads_new=%d dispatches_new=%d "
                "orders_new=%d token_granted_day=%d token_spent_day=%d"
                % (
                    counts["leads_day"],
                    counts["dispatches_day"],
                    counts["orders_day"],
                    counts["token_granted_day"],
                    counts["token_spent_day"],
                )
            )
        else:
            verdict = (
                "flat: honest zero-activity day (pre-commercialization "
                "steady state, zero fabricated counts)"
            )
        focus = (
            "business=commercialization-funnel metric=four-ring daily "
            "counts (leads=%d dispatches=%d orders=%d token_flow=%d) "
            "target=pipeline readiness; real revenue stays gated on the "
            "CEO physical prerequisites"
            % (
                counts["leads_day"],
                counts["dispatches_day"],
                counts["orders_day"],
                counts["token_granted_day"] + counts["token_spent_day"],
            )
        )

        envelope = {
            "day": day,
            "counts": counts,
            "delta_prev_day": delta,
            "verdict_line": verdict,
            "focus": focus,
            "standing_lines": self.standing_lines,
        }
        text = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
        hits = [w for w in self.banned_words if w in text]
        gate = "FAIL" if hits else "PASS"
        envelope["gate"] = gate
        envelope["hits"] = hits
        final = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
        self.db.execute(
            "INSERT OR REPLACE INTO rollups (day, envelope, gate, hits) "
            "VALUES (?,?,?,?)",
            (day, final, gate, json.dumps(hits, ensure_ascii=False)),
        )
        self.db.commit()
        return envelope

    # ---- the daily series ----

    def run_daily(self, leads_inbox, orders_inbox, flows_inbox, day):
        _assert_day(day)
        _assert_inbox(leads_inbox)
        _assert_inbox(orders_inbox)
        _assert_inbox(flows_inbox)
        r1 = self.scan_leads(leads_inbox, day)
        r2 = self.dispatch_leads(day)
        r3 = self.book_orders(orders_inbox, day)
        r4 = self.book_token_flows(flows_inbox, day)
        env = self.rollup(day)
        return {"ring1": r1, "ring2": r2, "ring3": r3, "ring4": r4, "envelope": env}


_EVIDENCE_TOKEN = "{day}"


def _resolve_evidence(path, day):
    """Resolve the optional --evidence rotation template (AC-FCR, R2062).

    Law: a path WITHOUT braces keeps the historical single-file face -
    each run rewrites that one file (mode "w"), so a same-path reuse
    across days overwrites the earlier bytes; that is the zero-append
    carrier, never an accumulating log. A path may carry the literal
    {day} token exactly once to select the rotating per-day face (the
    token expands to the caller-injected --day, so a multi-day chain
    keeps one file per day). Any other brace form is a bad argument:
    the reject happens here, before the wiring layer creates any
    directory, so a bad template leaves zero disk artifacts.
    """
    if not path:
        return None
    if "{" in path or "}" in path:
        if path.count(_EVIDENCE_TOKEN) != 1:
            raise FunnArgError(E_FN_BAD_ARGS)
        if "{" in path.replace(_EVIDENCE_TOKEN, "") or \
                "}" in path.replace(_EVIDENCE_TOKEN, ""):
            raise FunnArgError(E_FN_BAD_ARGS)
        return path.replace(_EVIDENCE_TOKEN, day)
    return path


def main(argv=None):
    """FUNNEL-STEP daily CLI face (R2033 wiring; canon plan section 3:
    an independently runnable CLI in the reconcile_daily shape - the
    OSLoop daily round calls this with the CALLER-INJECTED day, so the
    zero-wall-clock law of the library stays intact (--day required).

    Default carrier paths live under the repo-root state/funnel/ face
    (plan section 3): funnel.db + inbox/leads + inbox/orders +
    inbox/flows. Missing inbox dirs are created empty HERE, in the
    wiring layer - this CLI is the caller, so the library law (the
    caller provides the inbox dirs) is unchanged.

    Evidence face: the envelope prints as ascii-escaped JSON (coding
    law - the evidence log stays single-dialect ASCII no matter what
    the UTF-8 config carries). Exit 0 = gate PASS; exit 2 = gate FAIL
    (fail-closed: a banned-word hit never books a green day). A
    rejected argument face - bad --day, an uncreatable wiring path,
    an unreadable carrier/config - prints ONE clean E_FN_BAD_ARGS
    line and exits 2, never a traceback (AC-FCG family, the
    reconcile_daily contract); a bad --day rejects before any disk
    artifact exists. Pure ASCII source.
    """
    import argparse

    defaults = default_paths()
    parser = argparse.ArgumentParser(
        description="FUNNEL-STEP daily four-ring run (plan section 3)")
    parser.add_argument("--day", required=True,
                        help="YYYY-MM-DD, caller-injected (zero wall-clock)")
    parser.add_argument("--db", default=defaults["db"])
    parser.add_argument("--leads-inbox", default=defaults["leads_inbox"])
    parser.add_argument("--orders-inbox", default=defaults["orders_inbox"])
    parser.add_argument("--flows-inbox", default=defaults["flows_inbox"])
    parser.add_argument("--config", default=defaults["config"])
    parser.add_argument("--evidence", default=None,
                        help="optional self-tee evidence log path (utf-8"
                             " no-BOM, LF - single dialect by construction;"
                             " the shell never owns the evidence bytes);"
                             " the literal {day} expands to --day so a"
                             " caller can keep one file per day, otherwise"
                             " the single path is rewritten each run")
    args = parser.parse_args(argv)

    # CLI fail-closed gate family (AC-FCG, R2048): every reject is
    # ONE clean E_FN_BAD_ARGS line + exit 2 (reconcile_daily family
    # contract) - never a traceback. Order: the day is validated
    # FIRST (a bad day leaves zero disk artifacts), then the
    # wiring-layer path creations are pre-gated, then the carrier
    # phase absorbs the library raises. The library raise law itself
    # is untouched (wiring-layer confinement, AC-FCG7).
    def _clean_reject():
        print(E_FN_BAD_ARGS)
        return 2

    try:
        _assert_day(args.day)
    except FunnArgError:
        return _clean_reject()
    try:
        evidence = _resolve_evidence(args.evidence, args.day)
    except FunnArgError:
        return _clean_reject()
    try:
        os.makedirs(os.path.dirname(os.path.abspath(args.db)),
                    exist_ok=True)
        for d in (args.leads_inbox, args.orders_inbox, args.flows_inbox):
            os.makedirs(d, exist_ok=True)
        if evidence:
            os.makedirs(
                os.path.dirname(os.path.abspath(evidence)),
                exist_ok=True)
    except OSError:
        return _clean_reject()
    try:
        f = FunnelDaily(args.db, config_path=args.config)
        try:
            out = f.run_daily(args.leads_inbox, args.orders_inbox,
                              args.flows_inbox, args.day)
        finally:
            f.close()
    except (FunnArgError, ValueError, sqlite3.Error, OSError):
        return _clean_reject()
    env = out["envelope"]
    lines = [
        "FUNNEL-DAILY day=%s db=%s" % (args.day, args.db),
        "ring1 leads: files=%d seen=%d new=%d"
        % (out["ring1"]["files_leads"], out["ring1"]["leads_seen"],
           out["ring1"]["leads_new"]),
        "ring2 dispatches: new=%d routes=%s"
        % (out["ring2"]["dispatches_new"],
           json.dumps(out["ring2"]["routes"], sort_keys=True)),
        "ring3 orders: seen=%d new=%d"
        % (out["ring3"]["orders_seen"], out["ring3"]["orders_new"]),
        "ring4 flows: seen=%d new=%d"
        % (out["ring4"]["flows_seen"], out["ring4"]["flows_new"]),
        "envelope %s" % json.dumps(env, ensure_ascii=True, sort_keys=True),
        "FUNNEL-DAILY %s gate=%s verdict=%s"
        % (args.day, env["gate"], env["verdict_line"]),
    ]
    for line in lines:
        print(line)
    if evidence:
        try:
            with open(evidence, "w", encoding="utf-8",
                      newline="\n") as h:
                h.write("\n".join(lines) + "\n")
        except OSError:
            return _clean_reject()
    return 0 if env["gate"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
