"""API open-platform developer-ecosystem face: the three rings of
third-party developer access over the token ledger sandbox
(BigDomain R1700; canon = explore-queue API open-platform row,
B5 metered face successor; claimed from the explore-lane top
open row per the R1697 carry-note).

Three rings, one per pre-registered criterion group AC-DK1..DK7
(registered in the R1700 explore-queue row before this code
existed; honesty law):

  ring 1 key issuance   : one developer key per (dev_account,
                          key_name); the api key value is a
                          deterministic sha256 derivation (zero
                          RNG); the billing ring binds through
                          the MeteredFace.register_client public
                          API (per-key enterprise client)
  ring 2 quota          : per-key per-UTC-month call cap enforced
                          by counting immutable local call rows
                          (zero UPDATE anywhere in this module);
                          a call over the cap is rejected before
                          the billing ring so nothing is charged
                          and nothing is consumed (fail-closed)
  ring 3 billing        : prepaid credit packs and per-call
                          metering delegate wholesale to the
                          MeteredFace public API (reference not
                          double-build: this module never touches
                          a metered_* table directly; the only
                          token movement is the ledger spend
                          inside metered.buy_pack)
  ring 4 lifecycle       : key revocation and rotation are
                          immutable lifecycle events in a separate
                          sqlite file (api_lifecycle.db, single
                          writer, R1681 precedent; zero ledger-schema
                          touch so the R1676 baseline fingerprints
                          stay true). A revoked or rotated-out key
                          fails closed on every write face before
                          the billing ring; a rotated successor
                          inherits the contract, the billing
                          binding (balance carries over through
                          the same metered client, zero token
                          movement, zero register re-touch) and
                          the window usage of its full ancestor
                          chain (rotation never resets the monthly
                          quota). Zero UPDATE, zero RNG.
  ring 5 rate            : per-key per-UTC-minute call cap
                          (minute_cap, 0 = off, backward
                          compatible: the legacy five-argument
                          issue_key form keeps working with the
                          ring dark). A structural reuse of the
                          quota ring: the count is immutable call
                          rows in the current minute window
                          (called_utc prefix match), and like the
                          monthly ring it is enforced over the
                          full rotate_in ancestry (rotation never
                          resets the minute ring either). The
                          rate gate sits between the kind gate and
                          the monthly quota gate and fires before
                          the billing ring: an over-rate call is
                          rejected E_AD_RATE with zero charge and
                          zero rows. The minute and monthly
                          readings stay separate in every envelope
                          (minute_window/minute_used/minute_cap
                          next to quota_used/quota_cap).
  ring 6 reject tally    : every key-attributed call-chain reject
                          (revoked, kind, rate, quota, duplicate
                          and the billing ring's own business
                          rejects) lands one immutable diagnostic
                          event in a separate sqlite file
                          (api_rejects.db, single writer, R1711
                          precedent; zero ledger-schema touch).
                          The developer-facing read faces
                          (reject_tally, key_view, dev_board)
                          aggregate those rows at read time with
                          GROUP BY COUNT per reason over the
                          current UTC month window -- the panel's
                          "why was my call rejected" profile. The
                          public reject_tally face also takes an
                          optional explicit "YYYY-MM" window so any
                          historical month stays readable (the
                          embedded faces keep the current-month
                          default).
                          Recording is best-effort: a diagnostic
                          write failure is swallowed so the
                          primary reject contract (correct code,
                          zero charge, zero call rows) stays
                          sacred. Rejects with no key attribution
                          (bad arguments, unknown key) and
                          issuance/purchase rejects stay
                          unrecorded (the panel cannot reach a
                          key that does not resolve). Zero
                          UPDATE, zero RNG, zero maintained
                          counters.

Call-chain order (AC-DK4): key gate -> kind gate -> quota gate ->
local duplicate pre-check -> billing ring meter_call -> local
immutable call row append. A billing-ring reject (no credits,
duplicate call_ref) fires before the local append so the local
log carries zero orphan rows; the engine_ref receipt is stored
verbatim (opaque external engine invocation record), zero
engine logic here (BigMoney engine reference law carried over
from metered.py).

Platform-side posture (festival/ads/showroom precedent): key
issuance, credit purchase and metered calls carry zero resident
free text, so there is no SecGate point in this module; any
future developer-generated-content face wires the SecGate
pre-gate first.

AIGC labeling: the issuer declares ai_generated per key and the
label persists on the key row (DB CHECK refuses anything but
0/1 on direct SQL); every read envelope carries it.

Non-advisory standing note: the open API is a compute-and-
visualization interface, not investment advice; the constructor
refuses an empty disclaimer and every envelope (issue/call
returns, key_view, dev_board, usage_log) carries the resident
disclaimer.

Production gates: the external API endpoint itself is a
bootstrap-time face (three-question gate + CEO authorization
first); per-key quota caps and the per-call price anchor are
P1 items for CEO, approval-only ([needs-CEO]). Sandbox quota
caps and prices are caller-supplied. No config keys are added.

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: two extra tables in the same SQLite DB (WAL, single
writer, same pattern as the ledger core). Zero UPDATE, zero RNG.
"""

import datetime
import hashlib
import os
import re
import sqlite3
import threading

from metered import KINDS, MeteredError

E_AD_BAD_ARGS = "E_AD_BAD_ARGS"
E_AD_DUP_KEY = "E_AD_DUP_KEY"          # same (dev, key_name) re-issue
E_AD_UNKNOWN_KEY = "E_AD_UNKNOWN_KEY"
E_AD_KIND = "E_AD_KIND"               # kind not enabled on the key
E_AD_DUP = "E_AD_DUP"                  # local call_ref replay
E_AD_QUOTA = "E_AD_QUOTA"              # window cap reached, fail-closed
E_AD_RATE = "E_AD_RATE"                # minute-window rate cap, fail-closed
E_AD_NO_DISCLAIMER = "E_AD_NO_DISCLAIMER"
E_AD_REVOKED = "E_AD_REVOKED"          # key revoked or rotated out
E_AD_ALREADY = "E_AD_ALREADY"          # double revoke / rotate a dead key

NON_ADVISORY = ("non-advisory notice: open API is a compute +"
                " visualization interface, not investment advice")

# explicit-window read format for the reject-tally public face:
# exactly YYYY-MM with month 01..12 (None on the face means the
# current UTC month, the byte-stable default)
_WINDOW_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# read-face status names (human-facing) for terminal lifecycle
# events; the event names themselves stay compact in the store
_STATUS_BY_EVENT = {"revoke": "revoked", "rotate_out": "rotated_out"}

apidev_posture_note = ("platform-side posture: key issuance, credit"
                       " purchase and metered calls carry zero"
                       " resident free text, so this module has no"
                       " SecGate point; any future developer-content"
                       " face wires the SecGate pre-gate first")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS api_dev_keys (
    key_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dev_account TEXT NOT NULL,
    key_name TEXT NOT NULL,
    metered_client TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    window_cap INTEGER NOT NULL CHECK (window_cap >= 1),
    minute_cap INTEGER NOT NULL DEFAULT 0 CHECK (minute_cap >= 0),
    enabled_kinds TEXT NOT NULL,
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0, 1)),
    issued_utc TEXT NOT NULL,
    UNIQUE (dev_account, key_name)
);
CREATE TABLE IF NOT EXISTS api_calls (
    call_ref TEXT PRIMARY KEY,
    key_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    engine_ref TEXT NOT NULL,
    window TEXT NOT NULL,
    called_utc TEXT NOT NULL
);
"""

# lifecycle event store: a separate sqlite file next to the ledger
# db (R1681 single-writer precedent). Keeping it out of the ledger
# DB leaves the R1676 schema_migrate baseline fingerprints true
# (this module adds zero new tables there beyond its R1700 pair).
_LC_SCHEMA = """
CREATE TABLE IF NOT EXISTS key_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id INTEGER NOT NULL,
    event TEXT NOT NULL CHECK (event IN ('revoke', 'rotate_out', 'rotate_in')),
    pair_key_id INTEGER,
    event_utc TEXT NOT NULL
);
"""

# reject-tally event store: another separate sqlite file next to
# the ledger db (same single-writer precedent as the lifecycle
# store). Keeping it out of the ledger DB leaves the R1676
# schema_migrate baseline fingerprints true, and keeping it out of
# the lifecycle store respects that file's event CHECK domain.
_RJ_SCHEMA = """
CREATE TABLE IF NOT EXISTS reject_events (
    reject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    detail TEXT NOT NULL,
    window TEXT NOT NULL,
    minute TEXT NOT NULL,
    called_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _window_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")


def _minute_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M")


def _is_int(value):
    return (isinstance(value, int) and not isinstance(value, bool))


def _sha16(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class ApiDevError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class DevKeyFace:
    """Developer-key + quota + billing face over one MeteredFace
    instance injected by reference (no copy). The billing ring is
    reached only through the metered public API; this class owns
    two local tables and its own connection/lock. Zero UPDATE,
    zero RNG: quota counts immutable call rows; the key value is
    a deterministic sha256 derivation."""

    def __init__(self, metered, disclaimer=NON_ADVISORY):
        if metered is None:
            raise ApiDevError(E_AD_BAD_ARGS, "metered face required")
        if not str(disclaimer or "").strip():
            raise ApiDevError(E_AD_NO_DISCLAIMER, "disclaimer required")
        self.metered = metered
        self.db_path = metered.db_path
        self.disclaimer = str(disclaimer)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._lc_path = os.path.join(
            os.path.dirname(os.path.abspath(self.db_path)),
            "api_lifecycle.db")
        self._lconn = sqlite3.connect(self._lc_path,
                                      check_same_thread=False,
                                      isolation_level=None)
        self._lconn.execute("PRAGMA journal_mode=WAL")
        self._lconn.executescript(_LC_SCHEMA)
        self._rj_path = os.path.join(
            os.path.dirname(os.path.abspath(self.db_path)),
            "api_rejects.db")
        self._rconn = sqlite3.connect(self._rj_path,
                                      check_same_thread=False,
                                      isolation_level=None)
        self._rconn.execute("PRAGMA journal_mode=WAL")
        self._rconn.executescript(_RJ_SCHEMA)

    def close(self):
        with self._lock:
            self._rconn.close()
            self._lconn.close()
            self._conn.close()

    # -- internal helpers ---------------------------------------------------

    def _key_row_by_name(self, dev_account, key_name):
        with self._lock:
            return self._conn.execute(
                "SELECT key_id FROM api_dev_keys"
                " WHERE dev_account = ? AND key_name = ?",
                (dev_account, key_name)).fetchone()

    def _key_row_by_apikey(self, api_key):
        with self._lock:
            return self._conn.execute(
                "SELECT key_id, dev_account, key_name, metered_client,"
                " window_cap, enabled_kinds, ai_label, minute_cap"
                " FROM api_dev_keys WHERE api_key = ?",
                (api_key,)).fetchone()

    def _window_count(self, key_id, window):
        with self._lock:
            return self._conn.execute(
                "SELECT COUNT(*) FROM api_calls"
                " WHERE key_id = ? AND window = ?",
                (key_id, window)).fetchone()[0]

    def _terminal_event(self, key_id):
        """The key's terminal lifecycle event, if any ('revoke' or
        'rotate_out'). A key with a terminal event is dead: every
        write face fails closed on it."""
        with self._lock:
            return self._lconn.execute(
                "SELECT event FROM key_events"
                " WHERE key_id = ? AND event IN"
                " ('revoke', 'rotate_out')", (key_id,)).fetchone()

    def _rotated_from(self, key_id):
        """The predecessor key_id this key was rotated in from
        (None for a freshly issued key)."""
        with self._lock:
            row = self._lconn.execute(
                "SELECT pair_key_id FROM key_events"
                " WHERE key_id = ? AND event = 'rotate_in'",
                (key_id,)).fetchone()
        return row[0] if row is not None else None

    def _ancestry_key_ids(self, key_id):
        """Full rotate_in lineage for one key: itself plus every
        predecessor reachable through rotate_in events. A rotation
        never resets the monthly window, so the successor's quota
        is enforced over the whole chain."""
        ids = [key_id]
        seen = {key_id}
        current = key_id
        while True:
            predecessor = self._rotated_from(current)
            if predecessor is None or predecessor in seen:
                break
            seen.add(predecessor)
            ids.append(predecessor)
            current = predecessor
        return ids

    def _effective_window_count(self, key_id, window):
        """Window usage of a key plus its full rotation ancestry
        (anti-evasion: rotating does not reset the monthly cap)."""
        ids = self._ancestry_key_ids(key_id)
        marks = ",".join("?" for _ in ids)
        with self._lock:
            return self._conn.execute(
                "SELECT COUNT(*) FROM api_calls"
                " WHERE window = ? AND key_id IN (" + marks + ")",
                [window] + list(ids)).fetchone()[0]

    def _effective_minute_count(self, key_id, minute):
        """Minute-window usage of a key plus its full rotation
        ancestry (the rate ring reuses the quota ring's structure:
        immutable call rows counted over the rotate_in chain; the
        minute window key is the called_utc minute prefix)."""
        ids = self._ancestry_key_ids(key_id)
        marks = ",".join("?" for _ in ids)
        with self._lock:
            return self._conn.execute(
                "SELECT COUNT(*) FROM api_calls"
                " WHERE substr(called_utc, 1, 16) = ?"
                " AND key_id IN (" + marks + ")",
                [minute] + list(ids)).fetchone()[0]

    # -- ring 6: reject tally (diagnostic event store) -------------------

    def _record_reject(self, key_id, reason, detail=""):
        """Best-effort append of one reject event to the diagnostic
        store. The primary reject contract is sacred: the caller
        still raises its own code even when this diagnostic write
        fails, so an infra-level sqlite failure is swallowed here
        (diagnostic face, not an accounting face). The window and
        minute stamps are taken fresh at record time so the row
        always carries the reject moment's own window keys."""
        try:
            with self._lock:
                self._rconn.execute(
                    "INSERT INTO reject_events (key_id, reason,"
                    " detail, window, minute, called_utc)"
                    " VALUES (?,?,?,?,?,?)",
                    (key_id, reason, detail, _window_utc(),
                     _minute_utc(), _now_utc()))
        except sqlite3.Error:
            pass

    def _reject(self, key_id, code, detail=""):
        """Record one key-attributed reject event in the tally
        store, then raise the reject. One call site per gate keeps
        the call chain readable; this helper always raises."""
        self._record_reject(key_id, code, detail)
        raise ApiDevError(code, detail)

    def _reject_tally(self, key_id, window):
        """Read-time COUNT aggregation of reject events by reason
        for one key in one window (zero maintained counters, zero
        UPDATE: the GROUP BY runs over immutable rows)."""
        with self._lock:
            rows = self._rconn.execute(
                "SELECT reason, COUNT(*) FROM reject_events"
                " WHERE key_id = ? AND window = ?"
                " GROUP BY reason ORDER BY reason",
                (key_id, window)).fetchall()
        return {r[0]: int(r[1]) for r in rows}

    # -- ring 1: key issuance --------------------------------------------------

    def issue_key(self, dev_account, key_name, window_cap, kinds,
                  ai_generated, minute_cap=0):
        """One developer key per (dev_account, key_name). The key
        value is deterministic (sha256 over account|name|issued
        timestamp, zero RNG). The billing ring binds through the
        metered register_client public API: one per-key enterprise
        client. Same (dev, name) re-issue rejects before any
        metered touch (zero rows both sides); bad arguments reject
        with zero rows. minute_cap is the per-UTC-minute rate cap
        (ring 5); 0 keeps the ring dark (legacy callers unchanged)."""
        dev_account = str(dev_account or "").strip()
        key_name = str(key_name or "").strip()
        if not dev_account.startswith("usr:"):
            raise ApiDevError(E_AD_BAD_ARGS, "dev accounts are usr:* only")
        if not key_name:
            raise ApiDevError(E_AD_BAD_ARGS, "key name required")
        if not _is_int(window_cap) or window_cap < 1:
            raise ApiDevError(E_AD_BAD_ARGS, "window_cap must be int >= 1")
        if not _is_int(minute_cap) or minute_cap < 0:
            raise ApiDevError(E_AD_BAD_ARGS, "minute_cap must be int >= 0")
        if not isinstance(ai_generated, bool):
            raise ApiDevError(E_AD_BAD_ARGS, "ai_generated must be bool")
        if not kinds:
            raise ApiDevError(E_AD_BAD_ARGS, "kinds required")
        kind_list = []
        for kind in kinds:
            if kind not in KINDS:
                raise ApiDevError(E_AD_BAD_ARGS,
                                  "unknown kind " + str(kind))
            if kind not in kind_list:
                kind_list.append(kind)
        # local pre-check first: a re-issue never touches the metered
        # ring (the helper takes its own lock; no nesting)
        if self._key_row_by_name(dev_account, key_name) is not None:
            raise ApiDevError(E_AD_DUP_KEY,
                              dev_account + "|" + key_name)
        issued_utc = _now_utc()
        metered_client = ("ent:api-" +
                         _sha16(dev_account + "|" + key_name))
        api_key = ("sk_" + hashlib.sha256(
            (dev_account + "|" + key_name + "|" + issued_utc)
            .encode("utf-8")).hexdigest()[:40])
        self.metered.register_client(metered_client, dev_account, kind_list)
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO api_dev_keys (dev_account, key_name,"
                    " metered_client, api_key, window_cap, minute_cap,"
                    " enabled_kinds, ai_label, issued_utc)"
                    " VALUES (?,?,?,?,?,?,?,?,?)",
                    (dev_account, key_name, metered_client, api_key,
                     window_cap, minute_cap, ",".join(kind_list),
                     1 if ai_generated else 0, issued_utc))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ApiDevError(E_AD_DUP_KEY,
                                  dev_account + "|" + key_name)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"dev_account": dev_account, "key_name": key_name,
                "api_key": api_key, "metered_client": metered_client,
                "window_cap": window_cap, "minute_cap": minute_cap,
                "enabled_kinds": kind_list,
                "ai_label": 1 if ai_generated else 0,
                "disclaimer": self.disclaimer}

    # -- ring 3: billing (delegated wholesale to the metered public API) ------

    def buy_credits(self, api_key, calls, unit_price, ref):
        """Prepaid credit pack for one key: full delegation to
        metered.buy_pack (exactly one token spend bound to its tx;
        duplicate refs reject before the spend, zero charge)."""
        row = self._key_row_by_apikey(str(api_key or "").strip())
        if row is None:
            raise ApiDevError(E_AD_UNKNOWN_KEY, str(api_key))
        if self._terminal_event(row[0]) is not None:
            raise ApiDevError(E_AD_REVOKED, str(api_key))
        result = self.metered.buy_pack(row[3], calls, unit_price, ref)
        return {"api_key": api_key, "credits": result["calls"],
                "spend_tx": result["spend_tx"],
                "total_price": result["total_price"],
                "disclaimer": self.disclaimer}

    # -- the call chain: key gate -> kind gate -> rate gate -> quota
    #    gate -> dup pre-check -> billing ring -> local append --------

    def call(self, api_key, kind, call_ref, engine_ref):
        """One metered API call through the rings. Rejects fire
        before the billing ring (zero charge, zero local rows);
        a billing-ring reject fires before the local append (zero
        orphan local rows). The minute rate gate (ring 5) sits
        between the kind gate and the monthly quota gate. engine_ref
        is stored verbatim, zero engine logic here."""
        api_key = str(api_key or "").strip()
        kind = str(kind or "").strip()
        call_ref = str(call_ref or "").strip()
        engine_ref = str(engine_ref or "").strip()
        if not call_ref:
            raise ApiDevError(E_AD_BAD_ARGS, "call ref required")
        if not engine_ref:
            raise ApiDevError(E_AD_BAD_ARGS, "engine ref required")
        row = self._key_row_by_apikey(api_key)
        if row is None:
            raise ApiDevError(E_AD_UNKNOWN_KEY, api_key)
        key_id, metered_client, window_cap = row[0], row[3], int(row[4])
        minute_cap = int(row[7])
        enabled = row[5].split(",")
        if self._terminal_event(key_id) is not None:
            self._reject(key_id, E_AD_REVOKED, api_key)
        if kind not in enabled:
            self._reject(key_id, E_AD_KIND, kind)
        minute = _minute_utc()
        if (minute_cap > 0
                and self._effective_minute_count(key_id, minute)
                >= minute_cap):
            self._reject(key_id, E_AD_RATE, minute)
        window = _window_utc()
        if self._effective_window_count(key_id, window) >= window_cap:
            self._reject(key_id, E_AD_QUOTA, window)
        with self._lock:
            dup = self._conn.execute(
                "SELECT 1 FROM api_calls WHERE call_ref = ?",
                (call_ref,)).fetchone()
        if dup is not None:
            self._reject(key_id, E_AD_DUP, call_ref)
        # billing ring first: its rejects leave zero local rows; its
        # business rejects (no credits, kind gate, replay) are
        # recorded in the reject tally with their own metered codes
        try:
            self.metered.meter_call(metered_client, kind, call_ref,
                                    engine_ref)
        except MeteredError as exc:
            self._record_reject(key_id, exc.code, str(exc))
            raise
        dup_race = False
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO api_calls (call_ref, key_id, kind,"
                    " engine_ref, window, called_utc)"
                    " VALUES (?,?,?,?,?,?)",
                    (call_ref, key_id, kind, engine_ref, window,
                     _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                dup_race = True
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        if dup_race:
            self._reject(key_id, E_AD_DUP, call_ref)
        return {"call_ref": call_ref, "kind": kind,
                "engine_ref": engine_ref, "window": window,
                "quota_used": self._effective_window_count(key_id,
                                                            window),
                "quota_cap": window_cap,
                "minute_window": minute,
                "minute_used": self._effective_minute_count(key_id,
                                                             minute),
                "minute_cap": minute_cap,
                "disclaimer": self.disclaimer}

    # -- read faces ------------------------------------------------------------

    def key_view(self, api_key):
        """One key's contract view: declaration + lifecycle state +
        quota state + billing-ring binding. Read-only, zero token
        movement; a revoked or rotated-out key stays readable with
        its status reported."""
        row = self._key_row_by_apikey(str(api_key or "").strip())
        if row is None:
            raise ApiDevError(E_AD_UNKNOWN_KEY, str(api_key))
        window = _window_utc()
        minute = _minute_utc()
        terminal = self._terminal_event(row[0])
        used = self._effective_window_count(row[0], window)
        minute_used = self._effective_minute_count(row[0], minute)
        return {"api_key": api_key, "dev_account": row[1],
                "key_name": row[2], "metered_client": row[3],
                "window_cap": int(row[4]), "enabled_kinds": row[5].split(","),
                "ai_label": int(row[6]), "minute_cap": int(row[7]),
                "status": _STATUS_BY_EVENT[terminal[0]]
                          if terminal is not None else "active",
                "rotated_from_key_id": self._rotated_from(row[0]),
                "window": window,
                "quota_used": used,
                "quota_remaining": int(row[4]) - used,
                "minute_window": minute,
                "minute_used": minute_used,
                "reject_tally": self._reject_tally(row[0], window),
                "disclaimer": self.disclaimer}

    def dev_board(self, dev_account):
        """The developer's key board: every key with its quota
        state plus the billing-ring reconcile reference (through
        the metered public API). Read-only, zero token movement."""
        dev_account = str(dev_account or "").strip()
        if not dev_account.startswith("usr:"):
            raise ApiDevError(E_AD_BAD_ARGS, "dev accounts are usr:* only")
        window = _window_utc()
        minute = _minute_utc()
        keys = []
        with self._lock:
            rows = self._conn.execute(
                "SELECT key_id, key_name, metered_client, api_key,"
                " window_cap, enabled_kinds, ai_label, minute_cap"
                " FROM api_dev_keys"
                " WHERE dev_account = ? ORDER BY key_id",
                (dev_account,)).fetchall()
        tally_total = {}
        for row in rows:
            terminal = self._terminal_event(row[0])
            k_tally = self._reject_tally(row[0], window)
            for reason, count in k_tally.items():
                tally_total[reason] = tally_total.get(reason, 0) + count
            keys.append({"key_name": row[1], "api_key": row[3],
                         "metered_client": row[2],
                         "window_cap": int(row[4]),
                         "enabled_kinds": row[5].split(","),
                         "ai_label": int(row[6]),
                         "minute_cap": int(row[7]),
                         "status": _STATUS_BY_EVENT[terminal[0]]
                                   if terminal is not None else "active",
                         "rotated_from_key_id": self._rotated_from(row[0]),
                         "quota_used": self._effective_window_count(
                             row[0], window),
                         "minute_window": minute,
                         "minute_used": self._effective_minute_count(
                             row[0], minute),
                         "reject_tally": k_tally,
                         "billing": self.metered.reconcile_client(row[2])})
        return {"dev_account": dev_account, "keys": keys,
                "window": window, "reject_tally_total": tally_total,
                "disclaimer": self.disclaimer}

    def usage_log(self, api_key, limit=0):
        """One key's immutable call log (call rows with their
        external engine receipts stored verbatim). Read-only,
        zero token movement. The optional limit parameterizes a
        read cap for a growing log: limit=0 (the default) keeps
        the full-log behavior byte-stable; limit>0 bounds the
        response to the most recent limit rows and adds an
        overflow block (limit/total/returned/truncated) to the
        envelope, so a large log stays a bounded payload on the
        developer panel. The key gate fires first (an unknown
        key rejects before the argument gate, the call-chain
        key-gate-first law); a bad limit (non-int, bool, or
        negative) rejects E_AD_BAD_ARGS with zero rows read."""
        row = self._key_row_by_apikey(str(api_key or "").strip())
        if row is None:
            raise ApiDevError(E_AD_UNKNOWN_KEY, str(api_key))
        if isinstance(limit, bool) or not isinstance(limit, int) \
                or limit < 0:
            raise ApiDevError(E_AD_BAD_ARGS,
                              "limit must be an integer >= 0")
        if limit == 0:
            with self._lock:
                rows = self._conn.execute(
                    "SELECT call_ref, kind, engine_ref, window, called_utc"
                    " FROM api_calls WHERE key_id = ?"
                    " ORDER BY called_utc, call_ref", (row[0],)).fetchall()
            return {"api_key": api_key,
                    "calls": [{"call_ref": r[0], "kind": r[1],
                               "engine_ref": r[2], "window": r[3],
                               "called_utc": r[4]} for r in rows],
                    "disclaimer": self.disclaimer}
        with self._lock:
            total = int(self._conn.execute(
                "SELECT COUNT(*) FROM api_calls WHERE key_id = ?",
                (row[0],)).fetchone()[0])
            rows = self._conn.execute(
                "SELECT call_ref, kind, engine_ref, window, called_utc"
                " FROM api_calls WHERE key_id = ?"
                " ORDER BY called_utc DESC, call_ref DESC"
                " LIMIT ?", (row[0], limit)).fetchall()
        rows = list(reversed(rows))
        return {"api_key": api_key,
                "calls": [{"call_ref": r[0], "kind": r[1],
                           "engine_ref": r[2], "window": r[3],
                           "called_utc": r[4]} for r in rows],
                "limit": limit, "total": total,
                "returned": len(rows),
                "truncated": total > limit,
                "disclaimer": self.disclaimer}

    def reject_tally(self, api_key, window=None):
        """One key's reject-tally diagnostic profile: counts per
        rejection reason, aggregated at read time over the
        immutable reject-event rows (the developer panel's "why
        was my call rejected" face). window=None (the default)
        keeps the current-UTC-month behavior byte-stable; an
        explicit "YYYY-MM" string reads any month window at read
        time (rows are immutable and stamped with their own
        record-time window, so a historical month stays readable
        forever); any other shape rejects E_AD_BAD_ARGS
        fail-closed before the aggregation (the key gate fires
        first, the call-chain key-gate-first law). The embedded
        faces (key_view, dev_board) keep the current-month
        default untouched. Read-only, zero token movement; a
        revoked or rotated-out key stays readable with its tally
        intact."""
        row = self._key_row_by_apikey(str(api_key or "").strip())
        if row is None:
            raise ApiDevError(E_AD_UNKNOWN_KEY, str(api_key))
        if window is None:
            window = _window_utc()
        elif not (isinstance(window, str)
                  and _WINDOW_RE.match(window)):
            raise ApiDevError(E_AD_BAD_ARGS,
                              "window must be None or YYYY-MM")
        by_reason = self._reject_tally(row[0], window)
        return {"api_key": api_key, "key_name": row[2],
                "window": window, "by_reason": by_reason,
                "total": sum(by_reason.values()),
                "disclaimer": self.disclaimer}

    # -- ring 4: key lifecycle (revoke / rotate) ------------------------------

    def revoke_key(self, api_key):
        """Revoke one key by appending one immutable 'revoke' event
        (zero UPDATE: the key row itself never changes). From that
        moment every write face (call, buy_credits) fails closed
        with E_AD_REVOKED before the billing ring: zero charge,
        zero rows, zero spend. Read faces stay open and report
        status='revoked'. Double revoke rejects E_AD_ALREADY with
        zero new event rows; revoking an already rotated-out key
        rejects E_AD_ALREADY the same way."""
        row = self._key_row_by_apikey(str(api_key or "").strip())
        if row is None:
            raise ApiDevError(E_AD_UNKNOWN_KEY, str(api_key))
        key_id = row[0]
        if self._terminal_event(key_id) is not None:
            raise ApiDevError(E_AD_ALREADY, str(api_key))
        with self._lock:
            self._lconn.execute("BEGIN IMMEDIATE")
            try:
                self._lconn.execute(
                    "INSERT INTO key_events (key_id, event,"
                    " pair_key_id, event_utc)"
                    " VALUES (?, 'revoke', NULL, ?)",
                    (key_id, _now_utc()))
                self._lconn.execute("COMMIT")
            except BaseException:
                self._lconn.execute("ROLLBACK")
                raise
        return {"api_key": api_key, "status": "revoked",
                "disclaimer": self.disclaimer}

    def rotate_key(self, api_key, new_key_name):
        """Rotate one key: the old key is invalidated (a
        'rotate_out' event; every write face fails closed on it
        afterwards) and a successor key is issued that inherits
        the contract (window_cap, minute_cap, enabled_kinds,
        ai_label) and the
        billing binding -- the same metered client, so the credit
        balance carries over with zero token movement and zero
        register re-touch. The successor never resets the monthly
        window: its effective quota usage counts its own call rows
        plus every ancestor's rows in the same window. Both events
        of the pair land in one lifecycle transaction; the name
        conflict is pre-checked before any touch, so the successor
        insert has no ordering hazard. Zero UPDATE, zero RNG: the
        successor api_key is a fresh deterministic derivation."""
        new_key_name = str(new_key_name or "").strip()
        if not new_key_name:
            raise ApiDevError(E_AD_BAD_ARGS, "new key name required")
        row = self._key_row_by_apikey(str(api_key or "").strip())
        if row is None:
            raise ApiDevError(E_AD_UNKNOWN_KEY, str(api_key))
        key_id, dev_account, old_name = row[0], row[1], row[2]
        metered_client, window_cap = row[3], int(row[4])
        enabled_kinds, ai_label = row[5], int(row[6])
        minute_cap = int(row[7])
        if self._terminal_event(key_id) is not None:
            raise ApiDevError(E_AD_ALREADY, str(api_key))
        if self._key_row_by_name(dev_account, new_key_name) is not None:
            raise ApiDevError(E_AD_DUP_KEY,
                              dev_account + "|" + new_key_name)
        issued_utc = _now_utc()
        api_key_new = ("sk_" + hashlib.sha256(
            (dev_account + "|" + new_key_name + "|" + issued_utc)
            .encode("utf-8")).hexdigest()[:40])
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO api_dev_keys (dev_account, key_name,"
                    " metered_client, api_key, window_cap, minute_cap,"
                    " enabled_kinds, ai_label, issued_utc)"
                    " VALUES (?,?,?,?,?,?,?,?,?)",
                    (dev_account, new_key_name, metered_client,
                     api_key_new, window_cap, minute_cap,
                     enabled_kinds, ai_label, issued_utc))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ApiDevError(E_AD_DUP_KEY,
                                  dev_account + "|" + new_key_name)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        new_row = self._key_row_by_apikey(api_key_new)
        new_key_id = new_row[0]
        with self._lock:
            self._lconn.execute("BEGIN IMMEDIATE")
            try:
                self._lconn.execute(
                    "INSERT INTO key_events (key_id, event,"
                    " pair_key_id, event_utc)"
                    " VALUES (?, 'rotate_out', ?, ?)",
                    (key_id, new_key_id, _now_utc()))
                self._lconn.execute(
                    "INSERT INTO key_events (key_id, event,"
                    " pair_key_id, event_utc)"
                    " VALUES (?, 'rotate_in', ?, ?)",
                    (new_key_id, key_id, _now_utc()))
                self._lconn.execute("COMMIT")
            except BaseException:
                self._lconn.execute("ROLLBACK")
                raise
        return {"dev_account": dev_account, "key_name": new_key_name,
                "api_key": api_key_new,
                "metered_client": metered_client,
                "window_cap": window_cap, "minute_cap": minute_cap,
                "enabled_kinds": enabled_kinds.split(","),
                "ai_label": ai_label,
                "rotated_from": old_name, "rotated_from_key_id": key_id,
                "disclaimer": self.disclaimer}
