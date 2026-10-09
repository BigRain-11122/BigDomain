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
import sqlite3
import threading

from metered import KINDS

E_AD_BAD_ARGS = "E_AD_BAD_ARGS"
E_AD_DUP_KEY = "E_AD_DUP_KEY"          # same (dev, key_name) re-issue
E_AD_UNKNOWN_KEY = "E_AD_UNKNOWN_KEY"
E_AD_KIND = "E_AD_KIND"               # kind not enabled on the key
E_AD_DUP = "E_AD_DUP"                  # local call_ref replay
E_AD_QUOTA = "E_AD_QUOTA"              # window cap reached, fail-closed
E_AD_NO_DISCLAIMER = "E_AD_NO_DISCLAIMER"

NON_ADVISORY = ("non-advisory notice: open API is a compute +"
                " visualization interface, not investment advice")

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


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _window_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")


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

    def close(self):
        with self._lock:
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
                " window_cap, enabled_kinds, ai_label FROM api_dev_keys"
                " WHERE api_key = ?", (api_key,)).fetchone()

    def _window_count(self, key_id, window):
        with self._lock:
            return self._conn.execute(
                "SELECT COUNT(*) FROM api_calls"
                " WHERE key_id = ? AND window = ?",
                (key_id, window)).fetchone()[0]

    # -- ring 1: key issuance --------------------------------------------------

    def issue_key(self, dev_account, key_name, window_cap, kinds,
                  ai_generated):
        """One developer key per (dev_account, key_name). The key
        value is deterministic (sha256 over account|name|issued
        timestamp, zero RNG). The billing ring binds through the
        metered register_client public API: one per-key enterprise
        client. Same (dev, name) re-issue rejects before any
        metered touch (zero rows both sides); bad arguments reject
        with zero rows."""
        dev_account = str(dev_account or "").strip()
        key_name = str(key_name or "").strip()
        if not dev_account.startswith("usr:"):
            raise ApiDevError(E_AD_BAD_ARGS, "dev accounts are usr:* only")
        if not key_name:
            raise ApiDevError(E_AD_BAD_ARGS, "key name required")
        if not _is_int(window_cap) or window_cap < 1:
            raise ApiDevError(E_AD_BAD_ARGS, "window_cap must be int >= 1")
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
                    " metered_client, api_key, window_cap, enabled_kinds,"
                    " ai_label, issued_utc) VALUES (?,?,?,?,?,?,?,?)",
                    (dev_account, key_name, metered_client, api_key,
                     window_cap, ",".join(kind_list),
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
                "window_cap": window_cap, "enabled_kinds": kind_list,
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
        result = self.metered.buy_pack(row[3], calls, unit_price, ref)
        return {"api_key": api_key, "credits": result["calls"],
                "spend_tx": result["spend_tx"],
                "total_price": result["total_price"],
                "disclaimer": self.disclaimer}

    # -- the call chain: key gate -> kind gate -> quota gate -> dup
    #    pre-check -> billing ring -> local append --------------------------

    def call(self, api_key, kind, call_ref, engine_ref):
        """One metered API call through the three rings. Rejects
        fire before the billing ring (zero charge, zero local
        rows); a billing-ring reject fires before the local append
        (zero orphan local rows). engine_ref is stored verbatim,
        zero engine logic here."""
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
        enabled = row[5].split(",")
        if kind not in enabled:
            raise ApiDevError(E_AD_KIND, kind)
        window = _window_utc()
        if self._window_count(key_id, window) >= window_cap:
            raise ApiDevError(E_AD_QUOTA, window)
        with self._lock:
            dup = self._conn.execute(
                "SELECT 1 FROM api_calls WHERE call_ref = ?",
                (call_ref,)).fetchone()
        if dup is not None:
            raise ApiDevError(E_AD_DUP, call_ref)
        # billing ring first: its rejects leave zero local rows
        self.metered.meter_call(metered_client, kind, call_ref, engine_ref)
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
                raise ApiDevError(E_AD_DUP, call_ref)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"call_ref": call_ref, "kind": kind,
                "engine_ref": engine_ref, "window": window,
                "quota_used": self._window_count(key_id, window),
                "quota_cap": window_cap,
                "disclaimer": self.disclaimer}

    # -- read faces ------------------------------------------------------------

    def key_view(self, api_key):
        """One key's contract view: declaration + quota state +
        billing-ring binding. Read-only, zero token movement."""
        row = self._key_row_by_apikey(str(api_key or "").strip())
        if row is None:
            raise ApiDevError(E_AD_UNKNOWN_KEY, str(api_key))
        window = _window_utc()
        return {"api_key": api_key, "dev_account": row[1],
                "key_name": row[2], "metered_client": row[3],
                "window_cap": int(row[4]), "enabled_kinds": row[5].split(","),
                "ai_label": int(row[6]),
                "window": window,
                "quota_used": self._window_count(row[0], window),
                "quota_remaining": int(row[4]) -
                                   self._window_count(row[0], window),
                "disclaimer": self.disclaimer}

    def dev_board(self, dev_account):
        """The developer's key board: every key with its quota
        state plus the billing-ring reconcile reference (through
        the metered public API). Read-only, zero token movement."""
        dev_account = str(dev_account or "").strip()
        if not dev_account.startswith("usr:"):
            raise ApiDevError(E_AD_BAD_ARGS, "dev accounts are usr:* only")
        window = _window_utc()
        keys = []
        with self._lock:
            rows = self._conn.execute(
                "SELECT key_id, key_name, metered_client, api_key,"
                " window_cap, enabled_kinds, ai_label FROM api_dev_keys"
                " WHERE dev_account = ? ORDER BY key_id",
                (dev_account,)).fetchall()
        for row in rows:
            keys.append({"key_name": row[1], "api_key": row[3],
                         "metered_client": row[2],
                         "window_cap": int(row[4]),
                         "enabled_kinds": row[5].split(","),
                         "ai_label": int(row[6]),
                         "quota_used": self._window_count(row[0], window),
                         "billing": self.metered.reconcile_client(row[2])})
        return {"dev_account": dev_account, "keys": keys,
                "window": window, "disclaimer": self.disclaimer}

    def usage_log(self, api_key):
        """One key's immutable call log (call rows with their
        external engine receipts stored verbatim). Read-only,
        zero token movement."""
        row = self._key_row_by_apikey(str(api_key or "").strip())
        if row is None:
            raise ApiDevError(E_AD_UNKNOWN_KEY, str(api_key))
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
