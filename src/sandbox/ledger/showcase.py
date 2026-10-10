"""City digital-collectibles public showcase face (BigDomain R1750;
canon = explore-queue showcase line: public display windows plus the
chronicle walkthrough domain, inside the collectibles no-trading
hard law; seed = the R619 three-domain collectibles face).

Two domains over one append-only event record:

  - public display windows: a platform-registered showcase (with a
    slot cap) where owners put their own collectibles on public
    display, with an optional exhibit caption;
  - the chronicle walkthrough: the permanent placement/retraction
    event record (never rewritten) plus a derived tour of what is on
    display right now (placement order, stops numbered 1..N).

Hard laws (canon wording: pure internal circulation, ownership never
changes hands between accounts, permanent imprint):

  - this module never writes to the collectibles rows: a cl_id is
    referenced in showcase events only, and the owning account is
    verified through a READ-ONLY dock into the ledger DB (the
    notify pay-dock posture; reference, not copy);
  - placement and retraction move zero tokens: no ledger spend
    exists in this module, display is free;
  - event rows are append-only and the module has zero UPDATE
    surface: the display state is derived from the latest event per
    cl_id (globally one window per item at a time);
  - no verb offers or otherwise circulates a collectible between
    accounts (banned-verb source scan rides the suite); only the
    dock-verified owner can act on an item.

msgSecCheck pre-gate: exhibit captions are resident text, so a gate
with check_text must be injected at construction (the lobby SecGate
product by reference, no copy); an unwired gate refuses construction
and a gate runtime fault maps to E_SH_GATE_ERROR, never a silent
pass. Showcase registration is platform-side text (festival/ads
platform posture) and carries no gate point.

AIGC labeling: showcase registry rows and exhibit events carry a
persistent ai_label (0/1, DB CHECK) and every listing surface shows
it; a resident standing disclaimer is required at construction and
rides every envelope (non-advisory law).

Storage: one separate SQLite file (showcase.db, WAL, single writer)
beside the ledger DB - zero ledger-schema touch, so the schema
fingerprint sentinel stays clean. Stdlib only; pure ASCII.

Pre-registered criteria AC-SH1..AC-SH7 live in the R1750
explore-queue row and were written before this code existed
(honesty law).
"""

import datetime
import os
import sqlite3
import threading

E_SH_BAD_ARGS = "E_SH_BAD_ARGS"
E_SH_DUP_SHOWCASE = "E_SH_DUP_SHOWCASE"
E_SH_UNKNOWN_SHOWCASE = "E_SH_UNKNOWN_SHOWCASE"
E_SH_UNKNOWN_ITEM = "E_SH_UNKNOWN_ITEM"
E_SH_NOT_OWNER = "E_SH_NOT_OWNER"
E_SH_NOT_DISPLAYED = "E_SH_NOT_DISPLAYED"
E_SH_ALREADY_DISPLAYED = "E_SH_ALREADY_DISPLAYED"
E_SH_SHOWCASE_FULL = "E_SH_SHOWCASE_FULL"
E_SH_CONTENT_REJECTED = "E_SH_CONTENT_REJECTED"
E_SH_NO_GATE = "E_SH_NO_GATE"
E_SH_GATE_ERROR = "E_SH_GATE_ERROR"
E_SH_NO_DISCLAIMER = "E_SH_NO_DISCLAIMER"

_CONTENT_REJECTED_CODE = "E_CONTENT_REJECTED"  # lobby SecGate code

_SCHEMA = """
CREATE TABLE IF NOT EXISTS showcases (
    showcase_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    slot_cap INTEGER NOT NULL CHECK (slot_cap >= 1),
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0,1)),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS exhibit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    showcase_id TEXT NOT NULL,
    cl_id INTEGER NOT NULL,
    owner_id TEXT NOT NULL,
    caption TEXT NOT NULL DEFAULT '',
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0,1)),
    action TEXT NOT NULL CHECK (action IN ('place','retract')),
    acted_utc TEXT NOT NULL
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class ShowcaseError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class ShowcaseFace:
    """Public showcase face over one Ledger instance. Own SQLite file
    plus a read-only dock into the ledger DB (ownership checks);
    every mutation runs inside BEGIN IMMEDIATE on the own file."""

    def __init__(self, ledger, gate, disclaimer, db_path=None):
        if gate is None or not hasattr(gate, "check_text"):
            raise ShowcaseError(E_SH_NO_GATE, "content gate required")
        if not str(disclaimer or "").strip():
            raise ShowcaseError(E_SH_NO_DISCLAIMER,
                               "resident disclaimer required")
        self.led = ledger
        self.ledger_db_path = ledger.db_path
        self.gate = gate
        self.disclaimer = str(disclaimer)
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.abspath(self.ledger_db_path)),
                "showcase.db")
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._dock = sqlite3.connect(
            "file:%s?mode=ro" % self.ledger_db_path, uri=True)

    def close(self):
        with self._lock:
            self._conn.close()
            self._dock.close()

    # -- internal helpers ----------------------------------------------------

    def _owner_of(self, cl_id):
        """Read-only ownership dock into the collectibles rows."""
        row = self._dock.execute(
            "SELECT account_id FROM collectibles WHERE cl_id = ?",
            (cl_id,)).fetchone()
        return row[0] if row is not None else None

    def _displayed_rows(self, showcase_id):
        with self._lock:
            return self._conn.execute(
                "SELECT cl_id, owner_id, caption, ai_label, acted_utc,"
                " event_id FROM exhibit_events WHERE event_id IN"
                " (SELECT MAX(event_id) FROM exhibit_events"
                "  GROUP BY cl_id)"
                " AND action = 'place' AND showcase_id = ?"
                " ORDER BY event_id", (showcase_id,)).fetchall()

    def _check_caption(self, caption):
        """Run the injected content gate over resident caption text.
        A wordlist hit maps to E_SH_CONTENT_REJECTED; ANY other
        failure (offline gate, runtime fault) maps to E_SH_GATE_ERROR
        - never a silent pass. Zero rows on either path (AC-SH3)."""
        try:
            self.gate.check_text(str(caption))
        except Exception as exc:  # noqa: BLE001 (fail-closed wrap)
            if getattr(exc, "code", None) == _CONTENT_REJECTED_CODE:
                raise ShowcaseError(E_SH_CONTENT_REJECTED,
                                    getattr(exc, "word", ""))
            raise ShowcaseError(E_SH_GATE_ERROR, str(exc))

    # -- writer faces --------------------------------------------------------

    def register_showcase(self, showcase_id, title, slot_cap,
                           ai_generated):
        showcase_id = str(showcase_id).strip()
        title = str(title).strip()
        if not showcase_id:
            raise ShowcaseError(E_SH_BAD_ARGS, "showcase id required")
        if not title:
            raise ShowcaseError(E_SH_BAD_ARGS, "title required")
        if (not isinstance(slot_cap, int) or isinstance(slot_cap, bool)
                or slot_cap < 1):
            raise ShowcaseError(E_SH_BAD_ARGS, "slot cap must be >= 1")
        if not isinstance(ai_generated, bool):
            raise ShowcaseError(E_SH_BAD_ARGS, "ai flag must be bool")
        with self._lock:
            row = self._conn.execute(
                "SELECT showcase_id FROM showcases WHERE showcase_id = ?",
                (showcase_id,)).fetchone()
            if row is not None:
                raise ShowcaseError(E_SH_DUP_SHOWCASE, showcase_id)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO showcases (showcase_id, title,"
                    " slot_cap, ai_label, registered_utc)"
                    " VALUES (?,?,?,?,?)",
                    (showcase_id, title, slot_cap,
                     1 if ai_generated else 0, _now_utc()))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise ShowcaseError(E_SH_DUP_SHOWCASE, showcase_id)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"showcase_id": showcase_id, "title": title,
                "slot_cap": slot_cap,
                "ai_label": 1 if ai_generated else 0,
                "disclaimer": self.disclaimer}

    def _assert_item(self, owner_account, cl_id):
        if (not isinstance(cl_id, int) or isinstance(cl_id, bool)
                or cl_id < 1):
            raise ShowcaseError(E_SH_BAD_ARGS, "cl id must be >= 1")
        if not str(owner_account).startswith("usr:"):
            raise ShowcaseError(E_SH_BAD_ARGS, "owners are usr:* only")
        owner = self._owner_of(cl_id)
        if owner is None:
            raise ShowcaseError(E_SH_UNKNOWN_ITEM, str(cl_id))
        if owner != owner_account:
            raise ShowcaseError(E_SH_NOT_OWNER, str(cl_id))
        return owner

    def _assert_showcase(self, showcase_id):
        showcase_id = str(showcase_id).strip()
        if not showcase_id:
            raise ShowcaseError(E_SH_BAD_ARGS, "showcase id required")
        with self._lock:
            row = self._conn.execute(
                "SELECT slot_cap FROM showcases WHERE showcase_id = ?",
                (showcase_id,)).fetchone()
        if row is None:
            raise ShowcaseError(E_SH_UNKNOWN_SHOWCASE, showcase_id)
        return showcase_id, int(row[0])

    def place_exhibit(self, owner_account, showcase_id, cl_id,
                      caption="", ai_generated=False):
        showcase_id, slot_cap = self._assert_showcase(showcase_id)
        self._assert_item(owner_account, cl_id)
        if not isinstance(caption, str):
            raise ShowcaseError(E_SH_BAD_ARGS, "caption must be text")
        if not isinstance(ai_generated, bool):
            raise ShowcaseError(E_SH_BAD_ARGS, "ai flag must be bool")
        self._check_caption(caption)
        with self._lock:
            latest = self._conn.execute(
                "SELECT action FROM exhibit_events WHERE cl_id = ?"
                " ORDER BY event_id DESC LIMIT 1", (cl_id,)).fetchone()
            if latest is not None and latest[0] == "place":
                raise ShowcaseError(E_SH_ALREADY_DISPLAYED, str(cl_id))
            displayed = self._conn.execute(
                "SELECT COUNT(*) FROM exhibit_events WHERE event_id IN"
                " (SELECT MAX(event_id) FROM exhibit_events"
                "  GROUP BY cl_id)"
                " AND action = 'place' AND showcase_id = ?",
                (showcase_id,)).fetchone()[0]
            if int(displayed) >= slot_cap:
                raise ShowcaseError(E_SH_SHOWCASE_FULL,
                                    "%s %d/%d" % (showcase_id, int(displayed),
                                                  slot_cap))
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO exhibit_events (showcase_id, cl_id,"
                    " owner_id, caption, ai_label, action, acted_utc)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (showcase_id, cl_id, owner_account, caption,
                     1 if ai_generated else 0, "place", _now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"event_id": cur.lastrowid, "showcase_id": showcase_id,
                "cl_id": cl_id, "action": "place",
                "disclaimer": self.disclaimer}

    def retract_exhibit(self, owner_account, showcase_id, cl_id):
        showcase_id, _ = self._assert_showcase(showcase_id)
        self._assert_item(owner_account, cl_id)
        with self._lock:
            latest = self._conn.execute(
                "SELECT showcase_id, action FROM exhibit_events"
                " WHERE cl_id = ? ORDER BY event_id DESC LIMIT 1",
                (cl_id,)).fetchone()
            if (latest is None or latest[0] != showcase_id
                    or latest[1] != "place"):
                raise ShowcaseError(E_SH_NOT_DISPLAYED, str(cl_id))
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.execute(
                    "INSERT INTO exhibit_events (showcase_id, cl_id,"
                    " owner_id, caption, ai_label, action, acted_utc)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (showcase_id, cl_id, owner_account, "",
                     0, "retract", _now_utc()))
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"event_id": cur.lastrowid, "showcase_id": showcase_id,
                "cl_id": cl_id, "action": "retract",
                "disclaimer": self.disclaimer}

    # -- read faces ----------------------------------------------------------

    def showcase_view(self, showcase_id):
        showcase_id, slot_cap = self._assert_showcase(showcase_id)
        with self._lock:
            row = self._conn.execute(
                "SELECT title, ai_label FROM showcases"
                " WHERE showcase_id = ?", (showcase_id,)).fetchone()
        displayed = [{"cl_id": int(r[0]), "owner_id": r[1],
                      "caption": r[2], "ai_label": int(r[3]),
                      "placed_utc": r[4]}
                     for r in self._displayed_rows(showcase_id)]
        return {"showcase_id": showcase_id, "title": row[0],
                "slot_cap": slot_cap, "ai_label": int(row[1]),
                "displayed": displayed,
                "disclaimer": self.disclaimer}

    def chronicle(self, showcase_id=None):
        if showcase_id is not None:
            showcase_id, _ = self._assert_showcase(showcase_id)
        with self._lock:
            if showcase_id is None:
                rows = self._conn.execute(
                    "SELECT event_id, showcase_id, cl_id, owner_id,"
                    " caption, ai_label, action, acted_utc FROM"
                    " exhibit_events ORDER BY event_id").fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT event_id, showcase_id, cl_id, owner_id,"
                    " caption, ai_label, action, acted_utc FROM"
                    " exhibit_events WHERE showcase_id = ?"
                    " ORDER BY event_id", (showcase_id,)).fetchall()
        events = [{"event_id": int(r[0]), "showcase_id": r[1],
                   "cl_id": int(r[2]), "owner_id": r[3],
                   "caption": r[4], "ai_label": int(r[5]),
                   "action": r[6], "acted_utc": r[7]}
                  for r in rows]
        return {"events": events, "disclaimer": self.disclaimer}

    def chronicle_tour(self, showcase_id):
        showcase_id, slot_cap = self._assert_showcase(showcase_id)
        stops = [{"stop": i + 1, "cl_id": int(r[0]),
                  "owner_id": r[1], "caption": r[2],
                  "ai_label": int(r[3]), "placed_utc": r[4]}
                 for i, r in enumerate(self._displayed_rows(showcase_id))]
        return {"showcase_id": showcase_id, "slot_cap": slot_cap,
                "stops": stops, "disclaimer": self.disclaimer}
