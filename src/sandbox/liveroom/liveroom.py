"""Slow-live room conversion-piece supply face (BigDomain explore
queue item, claimed round R608; launch-ops-rehearsal sec-1
consumer; division-of-labor anchor D-20260924-08: live account =
BigStream asset face, broadcast ops = BigCompute live-ops, this
company = in-room conversion-piece supply face).

The city slow-live channel is an attention funnel whose only
monetization touch on our side is the in-room conversion piece
(BLUEPRINT sec-4: "live room carries the cart = 19.9 direct
conversion"). The platform hard law is fail-closed in code:

  - unattended streaming is banned outright (BLUEPRINT sec-4
    annotation, patrol-4 E2-3 + BigCompute risk-register E1, CEO
    order "otherwise the room gets banned") -> open_session with
    attended=False is rejected before anything exists;
  - an attended session must carry a non-empty risk-control
    reference (broadcast strategy follows BigCompute risk
    control - cited here, never decided here).

Faces over one Ledger instance (same DB, own tables, WAL, single
writer, BEGIN IMMEDIATE per mutation - the venue/props family
pattern):

  open_session      attended hard gate + risk-control reference
  viewer_enter      anonymous cohort row (zero token touch)
  viewer_register   bind a census avatar (city identity); strict
                    funnel ordering: register requires enter;
                    re-register is idempotent-rejected
  post_danmaku      live-room UGC front gate: the SecGate
                    wordlist check runs BEFORE any row lands
                    (msgSecCheck-style fail-closed); anonymous
                    viewers cannot interact
  cart_convert      the conversion piece: exactly ONE token spend
                    of a caller-supplied integer price for a
                    census-registered viewer, one per viewer per
                    session; every conversion row binds its spend
                    tx (provenance law)
  close_session     after close, convert/danmaku/enter all refuse
  funnel            cohort counts derived from real state
  transcript        compliance spine: config disclaimer first and
                    last, AI-content rows carry the ai label
  conversion_ledger audit rows with bound spend tx

Isolation law: the ONLY token touch in this module is the single
spend inside cart_convert; cohort, registration, danmaku, close
and read faces move zero tokens; no verb converts anything back
or moves a conversion between viewers. Price values are
caller-supplied arguments only (19.9-style pricing stays a
[needs-CEO] P1 approval face); this module adds no config keys.

Pre-registered criteria AC-LR1..AC-LR7 live in the R608 backlog
row and were written before this code existed (honesty law).

Stdlib only. Encoding discipline: this module stays pure ASCII.
"""

import datetime
import sqlite3
import threading

E_LIVE_UNATTENDED = "E_LIVE_UNATTENDED"  # platform hard law (AC-LR1)
E_LIVE_BAD_ARGS = "E_LIVE_BAD_ARGS"
E_LIVE_UNKNOWN = "E_LIVE_UNKNOWN"         # session or in-room viewer unknown
E_LIVE_DUP = "E_LIVE_DUP"                 # re-register of a bound viewer
E_LIVE_NOT_RESIDENT = "E_LIVE_NOT_RESIDENT"  # interact without city identity
E_LIVE_CONV_DUP = "E_LIVE_CONV_DUP"      # second conversion, same window
E_LIVE_CLOSED = "E_LIVE_CLOSED"          # session already closed

_SCHEMA = """
CREATE TABLE IF NOT EXISTS live_sessions (
    session_id       TEXT PRIMARY KEY,
    room_id          TEXT NOT NULL,
    attended         INTEGER NOT NULL CHECK (attended = 1),
    risk_control_ref TEXT NOT NULL,
    opened_utc       TEXT NOT NULL,
    closed_utc       TEXT
);
CREATE TABLE IF NOT EXISTS live_cohort (
    session_id       TEXT NOT NULL,
    viewer_id        TEXT NOT NULL,
    census_avatar_id TEXT,
    entered_utc      TEXT NOT NULL,
    PRIMARY KEY (session_id, viewer_id)
);
CREATE TABLE IF NOT EXISTS live_danmaku (
    dm_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT NOT NULL,
    viewer_id    TEXT NOT NULL,
    body         TEXT NOT NULL,
    ai_generated INTEGER NOT NULL DEFAULT 0,
    posted_utc   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS live_conversions (
    conv_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     TEXT NOT NULL,
    viewer_id      TEXT NOT NULL,
    account_id     TEXT NOT NULL,
    price          INTEGER NOT NULL CHECK (price > 0),
    bound_spend_tx TEXT NOT NULL,
    created_utc    TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _is_int(value):
    return (isinstance(value, int) and not isinstance(value, bool))


class LiveRoomError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class LiveRoomFace:
    """Slow-live conversion-piece supply face over one Ledger
    instance plus a SecGate wordlist gate (lobby sec_gate reuse,
    the ugc/venue family precedent)."""

    def __init__(self, ledger, gate, disclaimer_text, ai_label_text):
        self.led = ledger
        self.gate = gate
        self.disclaimer_text = str(disclaimer_text)
        self.ai_label_text = str(ai_label_text)
        self.db_path = ledger.db_path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- internal helpers ---------------------------------------------------

    def _session_row(self, session_id):
        return self._conn.execute(
            "SELECT room_id, attended, risk_control_ref, closed_utc"
            " FROM live_sessions WHERE session_id = ?",
            (session_id,)).fetchone()

    def _require_open(self, session_id):
        row = self._session_row(session_id)
        if row is None:
            raise LiveRoomError(E_LIVE_UNKNOWN, session_id)
        if row[3] is not None:
            raise LiveRoomError(E_LIVE_CLOSED, session_id)
        return row

    def _cohort_row(self, session_id, viewer_id):
        return self._conn.execute(
            "SELECT census_avatar_id FROM live_cohort"
            " WHERE session_id = ? AND viewer_id = ?",
            (session_id, viewer_id)).fetchone()

    def _require_resident(self, session_id, viewer_id):
        """Interactive faces require a census-bound city identity
        inside this session (anonymous = watch only)."""
        row = self._cohort_row(session_id, viewer_id)
        if row is None:
            raise LiveRoomError(E_LIVE_UNKNOWN, viewer_id)
        if row[0] is None:
            raise LiveRoomError(E_LIVE_NOT_RESIDENT, viewer_id)
        return row[0]

    # -- writer faces ---------------------------------------------------------

    def open_session(self, session_id, room_id, attended, risk_control_ref):
        """Register one broadcast session. The unattended FORM is
        platform-banned and refused outright; an attended session
        must cite the risk-control owner reference (BigCompute
        risk control is the citation, never a decision made here)."""
        if not str(session_id).strip() or not str(room_id).strip():
            raise LiveRoomError(E_LIVE_BAD_ARGS, "session_id/room_id required")
        if attended is not True:
            raise LiveRoomError(
                E_LIVE_UNATTENDED,
                "unattended streaming form is platform-banned")
        if not str(risk_control_ref).strip():
            raise LiveRoomError(E_LIVE_BAD_ARGS,
                                "risk_control_ref required (BigCompute"
                                " risk control citation)")
        with self._lock:
            dup = self._conn.execute(
                "SELECT COUNT(*) FROM live_sessions WHERE session_id = ?",
                (session_id,)).fetchone()[0]
            if dup:
                raise LiveRoomError(E_LIVE_DUP, session_id)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO live_sessions"
                    " (session_id, room_id, attended, risk_control_ref,"
                    "  opened_utc) VALUES (?,?,?,?,?)",
                    (session_id, room_id, 1, str(risk_control_ref),
                     _now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"session_id": session_id, "room_id": room_id,
                "attended": True,
                "risk_control_ref": str(risk_control_ref)}

    def viewer_enter(self, session_id, viewer_id):
        """Anonymous cohort entry: free watching, zero token touch.
        Idempotent per (session, viewer)."""
        if not str(viewer_id).strip():
            raise LiveRoomError(E_LIVE_BAD_ARGS, "viewer_id required")
        with self._lock:
            self._require_open(session_id)
            row = self._cohort_row(session_id, viewer_id)
            if row is not None:
                return {"viewer_id": viewer_id, "new": False}
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO live_cohort"
                    " (session_id, viewer_id, entered_utc)"
                    " VALUES (?,?,?)",
                    (session_id, viewer_id, _now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"viewer_id": viewer_id, "new": True}

    def viewer_register(self, session_id, viewer_id, census_avatar_id):
        """Bind a census avatar to an in-room viewer (the city
        identity gate for interaction and conversion). Strict
        funnel ordering: must have entered first; re-register of
        an already-bound viewer is idempotent-rejected."""
        if not str(census_avatar_id).strip():
            raise LiveRoomError(E_LIVE_BAD_ARGS, "census_avatar_id required")
        with self._lock:
            self._require_open(session_id)
            row = self._cohort_row(session_id, viewer_id)
            if row is None:
                raise LiveRoomError(E_LIVE_UNKNOWN,
                                    "viewer must enter before register")
            if row[0] is not None:
                raise LiveRoomError(E_LIVE_DUP, viewer_id)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "UPDATE live_cohort SET census_avatar_id = ?"
                    " WHERE session_id = ? AND viewer_id = ?",
                    (str(census_avatar_id), session_id, viewer_id))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"viewer_id": viewer_id,
                "census_avatar_id": str(census_avatar_id)}

    def post_danmaku(self, session_id, viewer_id, body,
                     ai_generated=False):
        """Live-room UGC face. The SecGate wordlist check runs
        BEFORE anything is recorded (fail-closed front gate:
        a rejected line never lands); interactive faces require
        the census-bound city identity."""
        if not str(body).strip():
            raise LiveRoomError(E_LIVE_BAD_ARGS, "body required")
        with self._lock:
            self._require_open(session_id)
            self._require_resident(session_id, viewer_id)
            self.gate.check_text(str(body))  # raises before any insert
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO live_danmaku"
                    " (session_id, viewer_id, body, ai_generated,"
                    "  posted_utc) VALUES (?,?,?,?,?)",
                    (session_id, viewer_id, str(body),
                     1 if ai_generated else 0, _now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"viewer_id": viewer_id, "body": str(body),
                "ai_generated": bool(ai_generated)}

    def cart_convert(self, session_id, viewer_id, price, ref):
        """The conversion piece: one cart purchase = exactly ONE
        token spend of a caller-supplied integer price, booked for
        the census-bound account of a registered viewer; one
        conversion per viewer per session (dup rejected BEFORE the
        spend, so a rejection never charges)."""
        if not _is_int(price) or price <= 0:
            raise LiveRoomError(E_LIVE_BAD_ARGS, "price must be int > 0")
        if not str(ref).strip():
            raise LiveRoomError(E_LIVE_BAD_ARGS, "order ref required")
        with self._lock:
            self._require_open(session_id)
            avatar = self._require_resident(session_id, viewer_id)
            dup = self._conn.execute(
                "SELECT COUNT(*) FROM live_conversions"
                " WHERE session_id = ? AND viewer_id = ?",
                (session_id, viewer_id)).fetchone()[0]
            if dup:
                raise LiveRoomError(E_LIVE_CONV_DUP, viewer_id)
        account_id = "usr:" + avatar
        self.led.ensure_account(account_id, census_avatar_id=avatar)
        spend_tx = self.led.spend(account_id, price, str(ref), "order")
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO live_conversions"
                    " (session_id, viewer_id, account_id, price,"
                    "  bound_spend_tx, created_utc) VALUES (?,?,?,?,?,?)",
                    (session_id, viewer_id, account_id, price, spend_tx,
                     _now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"viewer_id": viewer_id, "account_id": account_id,
                "price": price, "spend_tx_id": spend_tx}

    def close_session(self, session_id):
        """End of broadcast: after close every writer face refuses
        (E_LIVE_CLOSED). Closing itself moves zero tokens."""
        with self._lock:
            self._require_open(session_id)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "UPDATE live_sessions SET closed_utc = ?"
                    " WHERE session_id = ?", (_now_utc(), session_id))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"session_id": session_id, "closed": True}

    # -- read faces -------------------------------------------------------------

    def funnel(self, session_id):
        """Cohort counts derived from the real tables (zero
        fabricated numbers)."""
        with self._lock:
            row = self._session_row(session_id)
            if row is None:
                raise LiveRoomError(E_LIVE_UNKNOWN, session_id)
            entered = self._conn.execute(
                "SELECT COUNT(*) FROM live_cohort"
                " WHERE session_id = ?", (session_id,)).fetchone()[0]
            registered = self._conn.execute(
                "SELECT COUNT(*) FROM live_cohort"
                " WHERE session_id = ? AND census_avatar_id IS NOT NULL",
                (session_id,)).fetchone()[0]
            converted = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(price), 0)"
                " FROM live_conversions WHERE session_id = ?",
                (session_id,)).fetchone()
        return {"session_id": session_id, "room_id": row[0],
                "attended": bool(row[1]), "risk_control_ref": row[2],
                "disclaimer": self.disclaimer_text,
                "ai_label_text": self.ai_label_text,
                "entered": int(entered), "registered": int(registered),
                "converted": int(converted[0]),
                "conversion_total": int(converted[1])}

    def transcript(self, session_id):
        """Compliance spine view: the config disclaimer stands first
        and last; every danmaku row keeps its gate-passed body and
        carries the ai label when AI-generated; conversions print
        derived values only (price sums, no raw tx ids)."""
        f = self.funnel(session_id)
        lines = [self.disclaimer_text,
                 "room %s session %s attended=True risk_control=%s"
                 % (f["room_id"], f["session_id"], f["risk_control_ref"])]
        with self._lock:
            dm_rows = self._conn.execute(
                "SELECT viewer_id, body, ai_generated FROM live_danmaku"
                " WHERE session_id = ? ORDER BY dm_id",
                (session_id,)).fetchall()
        for viewer_id, body, ai_gen in dm_rows:
            tag = (" [" + self.ai_label_text + "]") if ai_gen else ""
            lines.append("danmaku %s: %s%s" % (viewer_id, body, tag))
        lines.append("funnel entered=%d registered=%d converted=%d"
                     " conversion_total=%d"
                     % (f["entered"], f["registered"], f["converted"],
                        f["conversion_total"]))
        lines.append(self.disclaimer_text)
        return lines

    def conversion_ledger(self, session_id):
        """Audit trail: every conversion row with its bound spend
        tx and account provenance."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT viewer_id, account_id, price, bound_spend_tx"
                " FROM live_conversions WHERE session_id = ?"
                " ORDER BY conv_id", (session_id,)).fetchall()
        return [{"viewer_id": r[0], "account_id": r[1], "price": int(r[2]),
                 "bound_spend_tx": r[3]} for r in rows]
