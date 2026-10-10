"""City showcase curation theme face (BigDomain R1751; canon =
explore-queue curation line: themed curation = multi-showcase
grouping plus a themed tour ordering; the curation rows are a
pure-read grouping with zero token movement and zero UPDATE,
successor of the R1750 showcase face).

Design (reference, not copy): this module holds a ShowcaseFace
instance and every showcase fact (existence, titles, on-display
state, per-showcase tour stops) is read through that public API -
there is no second showcase engine here and no direct read of the
showcase tables.

Domains:

  - curation registry: a platform-registered theme that groups N
    existing showcases in a fixed registered order (position 1..N);
    the grouping is append-only and immutable after registration
    (no member removal, no reorder, no update surface);
  - themed tour: the member showcases' current on-display tours
    concatenated in registered order with GLOBAL stop numbering
    1..N across showcases (a walkable theme route).
  - theme heat board: a pure-read derived ranking of every
    curation by its members' live on-display totals (successor
    row R1753; sort is fully deterministic, zero RNG).

Hard laws (canon wording: pure-read grouping, zero token face,
zero UPDATE carried over from the showcase line):

  - zero token movement: no ledger spend exists in this module;
    registration and every read are free and side-effect free on
    the ledger (ledger_tx count constant);
  - append-only: the registry and membership rows are INSERT-only;
    the module source carries zero UPDATE statements;
  - member existence is fail-closed: an unknown showcase id in the
    registration list refuses the whole registration with zero
    rows (verified through the ShowcaseFace public read face);
  - the no-trading hard law of the collectibles line is inherited:
    no verb offers or otherwise circulates a collectible (the
    banned-verb source scan rides the suite).

Platform posture: curation registration is platform-side text
(the festival/ads/showcase-register posture) and carries no
resident-text gate point; a successor resident-text surface must
wire a SecGate pre-gate first.

AIGC labeling: curation registry rows carry a persistent ai_label
(0/1, DB CHECK) and every listing surface shows it; a resident
standing disclaimer is required at construction and rides every
envelope (non-advisory law).

Storage: one separate SQLite file (curation.db, WAL, single
writer) beside the showcase DB - zero showcase-db and zero
ledger-schema touch, so the schema fingerprint sentinel stays
clean. Stdlib only; pure ASCII.

Pre-registered criteria AC-CU1..CU7 live in the R1751
explore-queue row and were written before this code existed
(honesty law).
"""

import datetime
import os
import sqlite3
import threading

E_CU_BAD_ARGS = "E_CU_BAD_ARGS"
E_CU_DUP_CURATION = "E_CU_DUP_CURATION"
E_CU_UNKNOWN_CURATION = "E_CU_UNKNOWN_CURATION"
E_CU_UNKNOWN_SHOWCASE = "E_CU_UNKNOWN_SHOWCASE"
E_CU_NO_DISCLAIMER = "E_CU_NO_DISCLAIMER"

E_SH_UNKNOWN_SHOWCASE = "E_SH_UNKNOWN_SHOWCASE"  # docked face code

_SCHEMA = """
CREATE TABLE IF NOT EXISTS curations (
    curation_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    ai_label INTEGER NOT NULL CHECK (ai_label IN (0,1)),
    registered_utc TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS curation_members (
    curation_id TEXT NOT NULL,
    position INTEGER NOT NULL CHECK (position >= 1),
    showcase_id TEXT NOT NULL,
    added_utc TEXT NOT NULL,
    PRIMARY KEY (curation_id, position)
);
"""


def _now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class CurationError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(str(code) + (": " + str(detail) if detail else ""))
        self.code = code
        self.detail = detail


class CurationFace:
    """Themed curation face over one ShowcaseFace instance. Own
    SQLite file; showcase facts flow exclusively through the
    ShowcaseFace public API (reference, not copy)."""

    def __init__(self, showcase_face, disclaimer, db_path=None):
        if not str(disclaimer or "").strip():
            raise CurationError(E_CU_NO_DISCLAIMER,
                               "resident disclaimer required")
        self.showcase = showcase_face
        self.disclaimer = str(disclaimer)
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.abspath(showcase_face.db_path)),
                "curation.db")
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False,
                                     isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    # -- internal helpers ----------------------------------------------------

    def _assert_curation_id(self, curation_id):
        curation_id = str(curation_id).strip()
        if not curation_id:
            raise CurationError(E_CU_BAD_ARGS, "curation id required")
        return curation_id

    def _load_register(self, curation_id):
        """Return (row, members) or raise E_CU_UNKNOWN_CURATION."""
        with self._lock:
            row = self._conn.execute(
                "SELECT title, ai_label, registered_utc FROM curations"
                " WHERE curation_id = ?", (curation_id,)).fetchone()
            if row is None:
                raise CurationError(E_CU_UNKNOWN_CURATION, curation_id)
            members = self._conn.execute(
                "SELECT position, showcase_id FROM curation_members"
                " WHERE curation_id = ? ORDER BY position",
                (curation_id,)).fetchall()
        return row, [(int(m[0]), m[1]) for m in members]

    def _verify_showcase_exists(self, showcase_id):
        """Existence check through the ShowcaseFace public read face
        (reference, not copy; zero direct showcase-table reads)."""
        try:
            self.showcase.showcase_view(showcase_id)
        except Exception as exc:  # noqa: BLE001 (docked-face wrap)
            if getattr(exc, "code", None) == E_SH_UNKNOWN_SHOWCASE:
                raise CurationError(E_CU_UNKNOWN_SHOWCASE,
                                   str(showcase_id))
            raise CurationError(E_CU_BAD_ARGS, str(exc))

    # -- writer face ---------------------------------------------------------

    def register_curation(self, curation_id, title, showcase_ids,
                          ai_generated):
        curation_id = self._assert_curation_id(curation_id)
        title = str(title).strip()
        if not title:
            raise CurationError(E_CU_BAD_ARGS, "title required")
        if isinstance(showcase_ids, (str, bytes)) or not isinstance(
                showcase_ids, (list, tuple)):
            raise CurationError(E_CU_BAD_ARGS, "showcase list required")
        ids = []
        for sid in showcase_ids:
            sid = str(sid).strip()
            if not sid:
                raise CurationError(E_CU_BAD_ARGS, "empty showcase id")
            if sid in ids:
                raise CurationError(E_CU_BAD_ARGS,
                                    "duplicate showcase id")
            ids.append(sid)
        if not ids:
            raise CurationError(E_CU_BAD_ARGS, "empty member list")
        if not isinstance(ai_generated, bool):
            raise CurationError(E_CU_BAD_ARGS, "ai flag must be bool")
        for sid in ids:
            self._verify_showcase_exists(sid)
        now = _now_utc()
        with self._lock:
            row = self._conn.execute(
                "SELECT curation_id FROM curations WHERE curation_id = ?",
                (curation_id,)).fetchone()
            if row is not None:
                raise CurationError(E_CU_DUP_CURATION, curation_id)
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.execute(
                    "INSERT INTO curations (curation_id, title,"
                    " ai_label, registered_utc) VALUES (?,?,?,?)",
                    (curation_id, title, 1 if ai_generated else 0, now))
                for pos, sid in enumerate(ids, start=1):
                    self._conn.execute(
                        "INSERT INTO curation_members (curation_id,"
                        " position, showcase_id, added_utc)"
                        " VALUES (?,?,?,?)",
                        (curation_id, pos, sid, now))
                self._conn.execute("COMMIT")
            except sqlite3.IntegrityError:
                self._conn.execute("ROLLBACK")
                raise CurationError(E_CU_DUP_CURATION, curation_id)
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
        return {"curation_id": curation_id, "title": title,
                "showcase_ids": ids,
                "ai_label": 1 if ai_generated else 0,
                "disclaimer": self.disclaimer}

    # -- read faces ----------------------------------------------------------

    def curation_view(self, curation_id):
        curation_id = self._assert_curation_id(curation_id)
        row, members = self._load_register(curation_id)
        member_rows = []
        for pos, sid in members:
            view = self.showcase.showcase_view(sid)
            member_rows.append({
                "position": pos, "showcase_id": sid,
                "title": view["title"], "slot_cap": view["slot_cap"],
                "on_display": len(view["displayed"])})
        return {"curation_id": curation_id, "title": row[0],
                "ai_label": int(row[1]), "registered_utc": row[2],
                "members": member_rows, "disclaimer": self.disclaimer}

    def curation_tour(self, curation_id):
        """Themed tour: member showcase tours concatenated in
        registered order, stops numbered globally 1..N across
        showcases (AC-CU3). Pure read; zero token movement."""
        curation_id = self._assert_curation_id(curation_id)
        row, members = self._load_register(curation_id)
        stops = []
        n = 0
        for _pos, sid in members:
            tour = self.showcase.chronicle_tour(sid)
            for stop in tour["stops"]:
                n += 1
                stops.append({"stop": n, "showcase_id": sid,
                              "cl_id": stop["cl_id"],
                              "owner_id": stop["owner_id"],
                              "caption": stop["caption"],
                              "ai_label": stop["ai_label"],
                              "placed_utc": stop["placed_utc"]})
        return {"curation_id": curation_id, "title": row[0],
                "ai_label": int(row[1]), "stops": stops,
                "disclaimer": self.disclaimer}

    def active_curations(self):
        with self._lock:
            rows = self._conn.execute(
                "SELECT curation_id, title, ai_label, registered_utc"
                " FROM curations ORDER BY rowid").fetchall()
            counts = dict(self._conn.execute(
                "SELECT curation_id, COUNT(*) FROM curation_members"
                " GROUP BY curation_id").fetchall())
        board = [{"curation_id": r[0], "title": r[1],
                  "ai_label": int(r[2]), "registered_utc": r[3],
                  "member_count": int(counts.get(r[0], 0))}
                 for r in rows]
        return {"curations": board, "disclaimer": self.disclaimer}

    def hot_board(self):
        """Theme heat board (R1753): every curation ranked by the sum
        of its member showcases' live on-display counts. Pure read
        with zero token movement and zero writes; each member count
        is derived through the ShowcaseFace public read face (the
        same derivation source curation_view uses - reference, not
        copy; zero direct showcase-table reads). The sort key is
        fully deterministic with zero RNG, zero time keys and zero
        insertion-order keys: displayed_total DESC, then
        curation_id ASC as the tie-break (the PRIMARY KEY gives a
        total order, so exactly one board order exists). A board
        over zero curations is an honest empty list."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT curation_id, title, ai_label FROM curations"
            ).fetchall()
            members_by = {}
            for cid, sid in self._conn.execute(
                    "SELECT curation_id, showcase_id FROM"
                    " curation_members ORDER BY curation_id,"
                    " position").fetchall():
                members_by.setdefault(cid, []).append(sid)
        entries = []
        for cid, title, ai_label in rows:
            heat = 0
            for sid in members_by.get(cid, []):
                view = self.showcase.showcase_view(sid)
                heat += len(view["displayed"])
            entries.append({"curation_id": cid, "title": title,
                            "ai_label": int(ai_label),
                            "member_count": len(members_by.get(cid, [])),
                            "displayed_total": heat})
        entries.sort(key=lambda e: (-e["displayed_total"],
                                    e["curation_id"]))
        board = []
        for rank, entry in enumerate(entries, start=1):
            board.append({"rank": rank,
                          "curation_id": entry["curation_id"],
                          "title": entry["title"],
                          "ai_label": entry["ai_label"],
                          "member_count": entry["member_count"],
                          "displayed_total": entry["displayed_total"]})
        return {"hot_board": board, "disclaimer": self.disclaimer}
