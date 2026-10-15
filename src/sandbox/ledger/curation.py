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
  - board rank-change diff: a pure-read movement face over two
    board snapshots (successor row R1770). The module never
    stores a snapshot (zero storage); the caller holds the
    previous hot_board() result and the current side is derived
    from the live hot_board() read - the single derivation
    source, no second aggregation engine. Four states: rise,
    fall, entered, dropped; steady rows are omitted (a change
    face lists changes, a fully-steady world yields an honest
    empty delta).

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
import re
import sqlite3
import threading

E_CU_BAD_ARGS = "E_CU_BAD_ARGS"
E_CU_DUP_CURATION = "E_CU_DUP_CURATION"
E_CU_UNKNOWN_CURATION = "E_CU_UNKNOWN_CURATION"
E_CU_UNKNOWN_SHOWCASE = "E_CU_UNKNOWN_SHOWCASE"
E_CU_NO_DISCLAIMER = "E_CU_NO_DISCLAIMER"
E_CU_BAD_WINDOW = "E_CU_BAD_WINDOW"

E_SH_UNKNOWN_SHOWCASE = "E_SH_UNKNOWN_SHOWCASE"  # docked face code

# Strict ASCII month-window form YYYY-MM (R1996): [0-9] classes
# reject Unicode digit look-alikes; no strip, so a trailing
# newline or any surrounding whitespace refuses (fail-closed,
# zero ambiguity).
_WINDOW_RE = re.compile(r"([0-9]{4})-(0[1-9]|1[0-2])")

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

    def _assert_window(self, window):
        """Month-window gate (R1996): strict ASCII YYYY-MM, the
        dedicated per-parameter family code E_CU_BAD_WINDOW, and
        the gate fires before any read so even a zero-curation
        world refuses a malformed window with zero read side
        effects. None is the default-form sentinel and never
        reaches here."""
        if (not isinstance(window, str)
                or _WINDOW_RE.fullmatch(window) is None):
            raise CurationError(E_CU_BAD_WINDOW,
                                "window must be a strict YYYY-MM"
                                " month string")
        return window

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

    def hot_board(self, window=None):
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
        over zero curations is an honest empty list.
        Month-window scoped form (R1996): an explicit strict
        YYYY-MM window re-scopes every member count through the
        ShowcaseFace showcase_view_window public read face - the
        window heat counts only the items whose latest
        window-recorded event is a place (the record-time law:
        events slice by their acted_utc record month, so an item
        placed in an earlier month with no window-recorded event
        stays off the window board while remaining on the live
        all-time board). The window gate fires before any read
        (E_CU_BAD_WINDOW family code, zero read side effects on
        refusal); the default None form is byte-for-byte the
        R1753 contract and only an explicit window adds the
        envelope window key. AC-CJM1..CJM3 (R1996)."""
        if window is not None:
            window = self._assert_window(window)
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
                if window is None:
                    view = self.showcase.showcase_view(sid)
                else:
                    view = self.showcase.showcase_view_window(
                        sid, window)
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
        env = {"hot_board": board, "disclaimer": self.disclaimer}
        if window is not None:
            env["window"] = window
        return env

    def hot_board_delta(self, prev_board):
        """Board rank-change diff (R1770): pure-read movement face
        over two heat-board snapshots. The previous snapshot is
        caller-held (zero storage: this module never persists a
        board); the current side is derived from the live
        hot_board() read - the single derivation source, zero
        second aggregation engine, zero direct showcase reads.
        Four states: rise (current rank above prev, delta =
        prev_rank - current_rank > 0), fall (delta < 0), entered
        (registered after the snapshot: prev_rank None) and
        dropped (in the snapshot but not on the current board:
        current_rank None; the registry is append-only so an
        in-world drop cannot occur - the state is still derived
        honestly for a caller-supplied cross-world snapshot).
        Steady rows are omitted: this is a change face, and a
        fully-steady world returns an honest empty delta. Row
        order is fully deterministic: state groups in the fixed
        order rise, fall, entered, dropped; inside a group rows
        sort by current_rank (dropped: prev_rank) ascending with
        curation_id ascending as the never-firing total
        tie-break. Zero token movement, zero writes, zero RNG."""
        if isinstance(prev_board, dict):
            rows_in = prev_board.get("hot_board")
            src_rows = rows_in if isinstance(rows_in, list) else None
        elif isinstance(prev_board, (list, tuple)):
            src_rows = list(prev_board)
        else:
            src_rows = None
        if not isinstance(src_rows, list):
            raise CurationError(E_CU_BAD_ARGS,
                               "prev board rows required")
        prev = {}
        for row in src_rows:
            if not isinstance(row, dict):
                raise CurationError(E_CU_BAD_ARGS,
                                   "prev row must be a dict")
            cid = row.get("curation_id")
            if not isinstance(cid, str) or not cid.strip():
                raise CurationError(E_CU_BAD_ARGS,
                                   "prev row curation id required")
            rank = row.get("rank")
            if (isinstance(rank, bool) or not isinstance(rank, int)
                    or rank < 1):
                raise CurationError(E_CU_BAD_ARGS,
                                   "prev rank must be int >= 1")
            if cid in prev:
                raise CurationError(E_CU_BAD_ARGS,
                                   "duplicate prev curation id")
            prev[cid] = (rank, row.get("ai_label"))
        current = self.hot_board()
        cur_by = {b["curation_id"]: b for b in current["hot_board"]}
        rise, fall, entered, dropped = [], [], [], []
        for cid, brow in cur_by.items():
            if cid not in prev:
                entered.append({"curation_id": cid,
                                "ai_label": brow["ai_label"],
                                "state": "entered",
                                "prev_rank": None,
                                "current_rank": brow["rank"],
                                "delta": None})
                continue
            prank = prev[cid][0]
            if brow["rank"] == prank:
                continue  # steady: a change face lists changes
            delta = prank - brow["rank"]
            row = {"curation_id": cid, "ai_label": brow["ai_label"],
                   "state": "rise" if delta > 0 else "fall",
                   "prev_rank": prank,
                   "current_rank": brow["rank"], "delta": delta}
            (rise if delta > 0 else fall).append(row)
        for cid, (prank, ai_label) in prev.items():
            if cid not in cur_by:
                dropped.append({"curation_id": cid,
                                "ai_label": (ai_label if (
                                    isinstance(ai_label, int)
                                    and not isinstance(ai_label,
                                                       bool))
                                    else None),
                                "state": "dropped",
                                "prev_rank": prank,
                                "current_rank": None,
                                "delta": None})
        rise.sort(key=lambda r: (r["current_rank"], r["curation_id"]))
        fall.sort(key=lambda r: (r["current_rank"], r["curation_id"]))
        entered.sort(key=lambda r: (r["current_rank"],
                                    r["curation_id"]))
        dropped.sort(key=lambda r: (r["prev_rank"], r["curation_id"]))
        delta_rows = rise + fall + entered + dropped
        return {"hot_board_delta": delta_rows,
                "disclaimer": self.disclaimer}

    def cold_board(self):
        """Zero-heat theme board (R1970): every curation whose
        members show a live on-display total of zero - the honest
        inverse filter of the heat board, a cold shelf of themes
        with nothing currently shown. Pure read with zero token
        movement and zero writes. The single derivation source is
        the live hot_board() read (reference face, not a copy):
        the cold rows are exactly the hot rows whose
        displayed_total is zero, re-ranked 1..N with the row shape
        unchanged - zero second aggregation engine, zero direct
        showcase reads, zero cached counters. The hot board's
        deterministic sort already places the zero-heat block in
        curation_id ASC order, and the explicit id sort keeps
        that law independent of the parent ordering. A world with
        zero curations, or a world where every theme carries live
        items, returns an honest empty board. Zero RNG, zero time
        keys, zero insertion-order keys; the envelope carries the
        standing disclaimer and every row keeps its ai_label."""
        board = self.hot_board()
        cold = [row for row in board["hot_board"]
                if row["displayed_total"] == 0]
        cold.sort(key=lambda r: r["curation_id"])
        rows = []
        for rank, row in enumerate(cold, start=1):
            rows.append({"rank": rank,
                         "curation_id": row["curation_id"],
                         "title": row["title"],
                         "ai_label": row["ai_label"],
                         "member_count": row["member_count"],
                         "displayed_total": row["displayed_total"]})
        return {"cold_board": rows, "disclaimer": self.disclaimer}

    def boards_combined(self, window=None):
        """Combined hot+cold dual board (R1974): one envelope that
        presents the heat board and the cold shelf side by side -
        the hot/cold complementary law made visible in a single
        read (AC-CJ1..CJ7 were registered in the explore-queue
        seed row before this code existed; honesty law). Pure
        read with zero token movement and zero writes. The single
        derivation source is ONE live hot_board() call (reference
        face, not a copy): the hot zone is exactly the heat>0
        rows of that snapshot, re-ranked 1..M with the parent
        (-displayed_total, curation_id) order preserved by the
        filter; the cold zone is exactly the zero-heat rows,
        re-ranked 1..K in curation_id ASC (the cold_board law).
        The two zones are disjoint by construction and their
        union is the full snapshot row set (M+K==N) - the
        complement law enforced on the single source, zero
        second aggregation engine, zero direct showcase reads,
        zero cached counters. Zero RNG, zero time keys, zero
        insertion-order keys; the envelope carries totals and
        the standing disclaimer, and every row keeps its
        ai_label.
        Month-window scoped form (R1996): an explicit strict
        YYYY-MM window re-scopes the single hot_board(window)
        call, so both zones carry the window-recorded display
        heat (the record-time law) while the registry stays the
        dense axis - every registered curation appears (a
        zero-window-event month yields the honest all-cold
        board, hot zone empty). The window gate fires before
        any read (E_CU_BAD_WINDOW family code; the gate stands
        alone even over a zero-curation world); the default
        None form is byte-for-byte the R1974 contract and only
        an explicit window adds the envelope window key.
        AC-CJM1..CJM7 (R1996)."""
        if window is not None:
            window = self._assert_window(window)
        board = self.hot_board(window)
        hot_rows = [row for row in board["hot_board"]
                    if row["displayed_total"] > 0]
        cold_rows = [row for row in board["hot_board"]
                     if row["displayed_total"] == 0]
        hot_rows.sort(key=lambda r: (-r["displayed_total"],
                                     r["curation_id"]))
        cold_rows.sort(key=lambda r: r["curation_id"])
        hot_out = []
        for rank, row in enumerate(hot_rows, start=1):
            hot_out.append({"rank": rank,
                            "curation_id": row["curation_id"],
                            "title": row["title"],
                            "ai_label": row["ai_label"],
                            "member_count": row["member_count"],
                            "displayed_total": row["displayed_total"]})
        cold_out = []
        for rank, row in enumerate(cold_rows, start=1):
            cold_out.append({"rank": rank,
                             "curation_id": row["curation_id"],
                             "title": row["title"],
                             "ai_label": row["ai_label"],
                             "member_count": row["member_count"],
                             "displayed_total": row["displayed_total"]})
        env = {"hot_board": hot_out,
               "cold_board": cold_out,
               "totals": {"hot_count": len(hot_out),
                          "cold_count": len(cold_out),
                          "total": len(hot_out) + len(cold_out)}}
        if window is not None:
            env["window"] = window
        env["disclaimer"] = self.disclaimer
        return env
