"""Resident AI companion subscription face over the token
ledger sandbox (BigDomain R1689; canon = explore-queue emotional
stickiness line: AI companion dialogue / memory archive /
subscription tier; seed = C-20261009-02 emotional-stickiness
revenue gap. The AI engine itself is NOT built here - the reply
text is caller-supplied in the sandbox exactly like prices are
(the production engine wiring is a bootstrap-window item), so
this face models the compliance-bearing pipeline, not the AI).

Three domains ride on the P-47-2b token ledger:

  subscription : one account + one month window (YYYY-MM) = one
                companion pass; exactly one token spend per
                (account, month), bound to its tx (structure
                reused from the R623 observation pass reading -
                reference, no duplicate build)
  dialogue     : resident texts and companion (AI) replies are
                stored ONLY after passing the content gate
                (msgSecCheck pre-gate; sandbox = wordlist mock
                SecGate injected by the caller - the lobby gate
                product is referenced, never copied)
  memory       : append-only AI-derived memory archive rows;
                every row is anchored to a companion reply and
                carries the AIGC label structurally

Mechanism (pre-registered criteria AC-CP1..AC-CP7 live in the
R1689 explore-queue row and were written before this code
existed; honesty law):

  - subscription idempotency: a repeated purchase of the same
    (account, month) is rejected BEFORE the spend, so the
    balance never moves twice (AC-CP1); without a pass the
    dialogue gate is fail-closed with zero charge (AC-CP2).
  - content gate is fail-closed end to end: a resident text or
    an AI reply carrying a gate word is rejected with zero rows
    stored (publish-time refusal); an unwired gate refuses face
    construction (E_CP_NO_GATE); a gate runtime fault is never
    silently passed (E_CP_GATE_ERROR) (AC-CP3).
  - AIGC labeling is structural: companion reply rows always
    carry ai_label=1 - the write face has no parameter to unset
    it and the DB CHECK constraint enforces the same at the
    storage layer; resident rows carry ai_label=0 (AC-CP4).
  - memory archive is append-only: zero UPDATE surface, every
    memory row is anchored to a companion reply (resident-source
    is rejected), the same source may be archived again
    (append, not unique) (AC-CP5).
  - the non-advisory disclaimer is resident: an empty disclaimer
    refuses face construction (E_CP_NO_DISCLAIMER) and every
    dialogue return / transcript envelope carries it (AC-CP6).
  - hard law (AC-CP7): bad args are all rejected with zero side
    effects, the module stays pure ASCII, shipped config.json is
    never touched, no UPDATE statements, no network imports.

Prices are caller-supplied in the sandbox; the production price
points and any launch gating are a P1 item for CEO,
approval-only ([needs-CEO]).

Stdlib only. Encoding discipline: this module stays pure ASCII.
Storage: three extra tables in the same SQLite DB (WAL, single
writer, same pattern as the ledger core).
"""

import datetime
import json
import re
import sqlite3
import threading

E_CP_BAD_ACCOUNT = "E_CP_BAD_ACCOUNT"      # AC-CP7
E_CP_BAD_ARGS = "E_CP_BAD_ARGS"            # AC-CP3 / AC-CP5 / AC-CP7
E_CP_BAD_PRICE = "E_CP_BAD_PRICE"          # AC-CP1 / AC-CP7
E_CP_BAD_MONTH = "E_CP_BAD_MONTH"          # AC-CP1 / AC-CP7
E_CP_PASS_DUP = "E_CP_PASS_DUP"            # AC-CP1
E_CP_DENIED = "E_CP_DENIED"               # AC-CP2
E_CP_CONTENT_REJECTED = "E_CP_CONTENT_REJECTED"  # AC-CP3
E_CP_GATE_ERROR = "E_CP_GATE_ERROR"        # AC-CP3 (runtime fault)
E_CP_NO_GATE = "E_CP_NO_GATE"              # AC-CP3 (unwired gate)
E_CP_NO_DISCLAIMER = "E_CP_NO_DISCLAIMER"  # AC-CP6
E_CP_BAD_MSG = "E_CP_BAD_MSG"              # AC-CP4 / AC-CP5
E_CP_BAD_MEMORY = "E_CP_BAD_MEMORY"        # AC-CP5

_CONTENT_REJECTED_CODE = "E_CONTENT_REJECTED"  # lobby SecGate hit
_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS companion_subs (
    sub_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    pass_month TEXT NOT NULL,
    token_price INTEGER NOT NULL CHECK (token_price > 0),
    bound_spend_tx TEXT NOT NULL,
    granted_utc TEXT NOT NULL,
    UNIQUE (account_id, pass_month)
);
CREATE TABLE IF NOT EXISTS companion_msgs (
    msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    pass_month TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('resident','companion')),
    text_content TEXT NOT NULL,
    ai_label INTEGER NOT NULL CHECK (
        (role = 'resident' AND ai_label = 0)
        OR (role = 'companion' AND ai_label = 1)),
    created_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS companion_memories (
    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    content_json TEXT NOT NULL,
    source_msg_id INTEGER NOT NULL,
    ai_label INTEGER NOT NULL CHECK (ai_label = 1),
    created_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class CompanionError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class CompanionFace:
    """AI companion subscription/dialogue/memory face over one
    Ledger instance. Own connection and lock into the same DB
    file; every mutation runs inside BEGIN IMMEDIATE. Message and
    memory rows are immutable once written (zero UPDATE
    surface). The content gate and the disclaimer are injected
    (dependency injection: the lobby SecGate product is
    referenced, never copied); a missing gate or an empty
    disclaimer refuses construction - no gate, no door."""

    def __init__(self, ledger, gate, disclaimer):
        self.led = ledger
        if gate is None or not callable(getattr(gate, "check_text", None)):
            raise CompanionError(E_CP_NO_GATE, "content gate required")
        self.gate = gate
        text = str(disclaimer or "").strip()
        if not text:
            raise CompanionError(E_CP_NO_DISCLAIMER,
                                 "resident disclaimer required")
        self.disclaimer = text
        self.db_path = ledger.db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- gate helpers (fail-closed end to end) ---------------------------

    def _gate_check(self, text):
        """Run the injected content gate. A wordlist hit maps to
        E_CP_CONTENT_REJECTED; ANY other failure (offline gate,
        runtime fault) maps to E_CP_GATE_ERROR - never a silent
        pass. Zero rows are stored on either path (AC-CP3)."""
        try:
            self.gate.check_text(text)
        except Exception as exc:  # noqa: BLE001 (fail-closed wrap)
            if getattr(exc, "code", None) == _CONTENT_REJECTED_CODE:
                raise CompanionError(E_CP_CONTENT_REJECTED,
                                     getattr(exc, "word", ""))
            raise CompanionError(E_CP_GATE_ERROR, str(exc))

    # -- writer faces ------------------------------------------------------

    @staticmethod
    def _check_price(token_price):
        if (not isinstance(token_price, int) or isinstance(token_price, bool)
                or token_price <= 0):
            raise CompanionError(E_CP_BAD_PRICE, str(token_price))

    def buy_pass(self, account_id, pass_month, token_price, ref):
        """Monthly companion pass for one YYYY-MM window: exactly
        one spend per (account, month) bound to its tx; a repeated
        purchase of the same month is rejected BEFORE the spend;
        another month is a separate legal purchase (AC-CP1)."""
        if not str(account_id or "").startswith("usr:"):
            raise CompanionError(E_CP_BAD_ACCOUNT, account_id)
        self._check_price(token_price)
        month = str(pass_month or "").strip()
        if not _MONTH_RE.match(month):
            raise CompanionError(E_CP_BAD_MONTH, month)
        ref = str(ref or "").strip()
        if not ref:
            raise CompanionError(E_CP_BAD_ARGS, "purchase ref required")
        with self._lock:
            row = self._conn.execute(
                "SELECT sub_id FROM companion_subs WHERE account_id = ?"
                " AND pass_month = ?", (account_id, month)).fetchone()
            if row is not None:
                raise CompanionError(E_CP_PASS_DUP,
                                     "%s/%s" % (month, ref))
            self.led.ensure_account(account_id,
                                    census_avatar_id=account_id[4:])
            spend_tx = self.led.spend(account_id, token_price, ref, "order")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO companion_subs (account_id, pass_month,"
                    " token_price, bound_spend_tx, granted_utc)"
                    " VALUES (?,?,?,?,?)",
                    (account_id, month, token_price, spend_tx, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise CompanionError(E_CP_PASS_DUP, "%s/%s" % (month, ref))
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"sub_id": cur.lastrowid, "account_id": account_id,
                "pass_month": month, "token_price": token_price,
                "spend_tx": spend_tx}

    def _require_pass(self, account_id, at_month):
        """Fail-closed subscription gate: without a pass for the
        month the call is rejected with zero charge (AC-CP2).
        Returns (bound_spend_tx, normalized_month)."""
        month = str(at_month or "").strip()
        if not _MONTH_RE.match(month):
            raise CompanionError(E_CP_BAD_MONTH, month)
        row = self._conn.execute(
            "SELECT bound_spend_tx FROM companion_subs"
            " WHERE account_id = ? AND pass_month = ?",
            (account_id, month)).fetchone()
        if row is None:
            raise CompanionError(E_CP_DENIED,
                                 "%s on %s" % (account_id, month))
        return row[0], month

    def converse(self, account_id, at_month, user_text):
        """Resident leg of the companion dialogue: subscription
        gate -> content gate (msgSecCheck pre-gate, publish-time
        refusal) -> exactly one resident message row with
        ai_label=0. The return envelope carries the resident
        non-advisory disclaimer (AC-CP2/CP3/CP4/CP6)."""
        if not str(account_id or "").startswith("usr:"):
            raise CompanionError(E_CP_BAD_ACCOUNT, account_id)
        text = str(user_text or "")
        if not text.strip():
            raise CompanionError(E_CP_BAD_ARGS, "text required")
        with self._lock:
            tx, month = self._require_pass(account_id, at_month)
            self._gate_check(text)   # zero rows stored on rejection
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO companion_msgs (account_id, pass_month,"
                    " role, text_content, ai_label, created_utc)"
                    " VALUES (?,?,?,?,0,?)",
                    (account_id, month, 'resident', text, _now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"msg_id": cur.lastrowid, "account_id": account_id,
                "role": "resident", "ai_label": 0, "text": text,
                "bound_sub_tx": tx, "disclaimer": self.disclaimer}

    def record_reply(self, msg_id, reply_text):
        """Companion (AI) leg: the caller supplies the reply text
        (the production AI engine is a bootstrap-window wiring;
        sandbox models the compliance pipeline). The reply passes
        the same content gate and is stored with the AIGC label
        STRUCTURALLY set - this face has no parameter to unset it
        and the DB CHECK enforces the same (AC-CP3/AC-CP4)."""
        if (not isinstance(msg_id, int) or isinstance(msg_id, bool)
                or msg_id <= 0):
            raise CompanionError(E_CP_BAD_MSG, str(msg_id))
        text = str(reply_text or "")
        if not text.strip():
            raise CompanionError(E_CP_BAD_ARGS, "reply text required")
        with self._lock:
            head = self._conn.execute(
                "SELECT account_id, pass_month, role FROM companion_msgs"
                " WHERE msg_id = ?", (msg_id,)).fetchone()
            if head is None:
                raise CompanionError(E_CP_BAD_MSG, str(msg_id))
            if head[2] != 'resident':
                raise CompanionError(E_CP_BAD_MSG,
                                     "reply anchor must be a resident msg")
            self._gate_check(text)   # zero rows stored on rejection
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO companion_msgs (account_id, pass_month,"
                    " role, text_content, ai_label, created_utc)"
                    " VALUES (?,?,?,?,1,?)",
                    (head[0], head[1], 'companion', text, _now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"msg_id": cur.lastrowid, "account_id": head[0],
                "role": "companion", "ai_label": 1, "text": text,
                "anchor_msg_id": msg_id, "disclaimer": self.disclaimer}

    def archive_memory(self, account_id, kind, content, source_msg_id):
        """Append-only AI-derived memory archive: the row must be
        anchored to a COMPANION reply of the same account (a
        resident-source anchor is rejected with zero rows); the
        AIGC label is structural (CHECK ai_label=1). The same
        source may be archived again - append, not unique
        (AC-CP5)."""
        if not str(account_id or "").startswith("usr:"):
            raise CompanionError(E_CP_BAD_ACCOUNT, account_id)
        k = str(kind or "").strip()
        if not k:
            raise CompanionError(E_CP_BAD_ARGS, "memory kind required")
        if not isinstance(content, (dict, list)) or not content:
            raise CompanionError(E_CP_BAD_ARGS,
                                 "memory content payload required")
        if (not isinstance(source_msg_id, int)
                or isinstance(source_msg_id, bool) or source_msg_id <= 0):
            raise CompanionError(E_CP_BAD_MEMORY, str(source_msg_id))
        payload = json.dumps(content, sort_keys=True)
        with self._lock:
            head = self._conn.execute(
                "SELECT account_id, role FROM companion_msgs"
                " WHERE msg_id = ?", (source_msg_id,)).fetchone()
            if head is None:
                raise CompanionError(E_CP_BAD_MEMORY, str(source_msg_id))
            if head[0] != account_id:
                raise CompanionError(E_CP_BAD_MEMORY,
                                     "source msg belongs to %s" % head[0])
            if head[1] != 'companion':
                raise CompanionError(E_CP_BAD_MEMORY,
                                     "memory source must be a companion msg")
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO companion_memories (account_id, kind,"
                    " content_json, source_msg_id, ai_label, created_utc)"
                    " VALUES (?,?,?,?,1,?)",
                    (account_id, k, payload, source_msg_id, _now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"memory_id": cur.lastrowid, "account_id": account_id,
                "kind": k, "source_msg_id": source_msg_id,
                "ai_label": 1}

    # -- read faces ----------------------------------------------------------

    def can_converse(self, account_id, at_month):
        """Pure-read subscription gate: reports the pass state
        and its bound spend tx. No token movement, no rows
        written."""
        month = str(at_month or "").strip()
        if not _MONTH_RE.match(month):
            raise CompanionError(E_CP_BAD_MONTH, month)
        with self._lock:
            row = self._conn.execute(
                "SELECT bound_spend_tx FROM companion_subs"
                " WHERE account_id = ? AND pass_month = ?",
                (account_id, month)).fetchone()
        if row is None:
            return {"allowed": False, "tx": None}
        return {"allowed": True, "tx": row[0]}

    def transcript_view(self, account_id, at_month):
        """Per-account dialogue view for one month window: rows
        carry role/text/ai_label/created; the envelope carries
        the resident non-advisory disclaimer (AC-CP6). Pure
        read."""
        month = str(at_month or "").strip()
        if not _MONTH_RE.match(month):
            raise CompanionError(E_CP_BAD_MONTH, month)
        with self._lock:
            rows = self._conn.execute(
                "SELECT msg_id, role, text_content, ai_label, created_utc"
                " FROM companion_msgs WHERE account_id = ?"
                " AND pass_month = ? ORDER BY msg_id",
                (account_id, month)).fetchall()
        return {"account_id": account_id, "pass_month": month,
                "disclaimer": self.disclaimer,
                "messages": [{"msg_id": int(r[0]), "role": r[1],
                              "text": r[2], "ai_label": int(r[3]),
                              "created_utc": r[4]} for r in rows]}

    def memory_view(self, account_id):
        """Per-account memory archive view: kind/content/source
        msg/ai_label with provenance. Pure read; rows are
        immutable once written (AC-CP5/CP6)."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT memory_id, kind, content_json, source_msg_id,"
                " ai_label, created_utc FROM companion_memories"
                " WHERE account_id = ? ORDER BY memory_id",
                (account_id,)).fetchall()
        return {"account_id": account_id,
                "disclaimer": self.disclaimer,
                "memories": [{"memory_id": int(r[0]), "kind": r[1],
                              "content": json.loads(r[2]),
                              "source_msg_id": int(r[3]),
                              "ai_label": int(r[4]),
                              "created_utc": r[5]} for r in rows]}

    def subs_view(self, account_id):
        """Per-account subscription view: month, price, bound
        spend tx (provenance) - sub rows are immutable."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT sub_id, pass_month, token_price, bound_spend_tx"
                " FROM companion_subs WHERE account_id = ?"
                " ORDER BY sub_id", (account_id,)).fetchall()
        return {"account_id": account_id,
                "subs": [{"sub_id": int(r[0]), "pass_month": r[1],
                          "token_price": int(r[2]),
                          "spend_tx": r[3]} for r in rows]}
