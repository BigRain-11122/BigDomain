r"""Water journal x store live-levels consistency probe (R1806, seed:
water_journal.py R1805 cell_totals).

The five completed-window water wiring (R1794..R1800) archives one
delta row per completed window in the append-only journal, and every
delta derives from the single store face (two live pool_water_levels
snapshots around the window). From a shared empty start (journal and
store both born empty, zero preexisting rows) the telescoping sum of
the archived per-cell deltas is structurally equal to the store's
current pool levels - this probe is the end-to-end invariant check
the family never had.

Measurement face only (R1727 qa_mtime_probe precedent): not in the
SUITES registry, zero product-file writes - the probe builds its own
shared-birth world in a system temp dir, drives real flows through
all five window kinds, then cross-checks journal cell_totals against
the store's live levels cell by cell (four families: noise.total,
noise.by_reason.*, review.suspended, review.verdicted.*). A drift
injection (direct fake journal row, the R1776/R1801 tamper posture)
must be detected and named - detection is the probe's positive path,
never a silent green.

Encoding discipline: this source stays pure ASCII (the emoji probe
text rides \U escapes); the output stays deterministic (no
timestamps, no temp paths) so double runs compare byte-identical.

Usage: python water_consistency_probe.py
Exit 0 = consistent world + drift detected; 2 = any unexpected
mismatch (fail-closed).
"""

import hashlib
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile

OS_BASE = os.path.dirname(os.path.abspath(__file__))
UGCDIR = os.path.normpath(os.path.join(OS_BASE, "..", "sandbox", "ugc"))
sys.path.insert(0, UGCDIR)

import pipeline as P  # noqa: E402  (product: referenced, not copied)
import water_journal as WJ  # noqa: E402

FROZEN = ("pipeline.py", "store.py", "water_journal.py", "config.json")
EMOJI_A = "\U0001F389"  # pure-emoji probe texts (emoji_only cell)
EMOJI_B = "\U0001F38A"
EMOJI_C = "\U0001F389\U0001F38A"
SHORT = "ab!"  # emoji-stripped len 3 < min 4 (too_short cell)


def sha16(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


def load_lobby_store():
    path = os.path.normpath(os.path.join(UGCDIR, "..", "lobby", "store.py"))
    spec = importlib.util.spec_from_file_location("lobby_store_probe", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def flatten_store(levels_env):
    """Flatten the store levels envelope into journal cell-key shape
    (noise.total / noise.by_reason.<r> / review.suspended /
    review.verdicted.<v>) so both sides compare under one key space."""
    lv = levels_env["pool_water_levels"]
    flat = {"noise.total": int(lv["noise"]["total"]),
            "review.suspended": int(lv["review"]["suspended"])}
    for reason, n in lv["noise"]["by_reason"].items():
        flat["noise.by_reason." + str(reason)] = int(n)
    for verdict, n in lv["review"]["verdicted"].items():
        flat["review.verdicted." + str(verdict)] = int(n)
    return flat


def cross(journal_env, levels_env):
    """Per-cell cross: union of journal cell keys and store keys, a
    missing journal cell reads as zero (store by_reason cells stay
    sparse-observed, store dense cells never miss). Returns
    (all_match, per-cell report rows, composition_ok)."""
    jc = journal_env["cell_totals"]
    sf = flatten_store(levels_env)
    rows = []
    all_match = True
    for key in sorted(set(jc) | set(sf)):
        j_val = int(jc.get(key, 0))
        s_val = int(sf.get(key, 0))
        match = j_val == s_val
        all_match = all_match and match
        rows.append("cell %-28s journal=%-3d store=%-3d %s"
                    % (key, j_val, s_val, "OK" if match else "DRIFT"))
    comp_left = int(journal_env["total"])
    comp_right = int(jc.get("noise.total", 0)) + int(jc.get("review.suspended", 0))
    store_total = int(levels_env["total"])
    composition_ok = comp_left == comp_right == store_total
    return all_match, rows, (comp_left, comp_right, store_total), composition_ok


def hand_sum_cells(board_rows):
    """Third path (AC-JC3): per-cell hand sum over the journal_board
    row deltas - must equal the cell_totals face read."""
    cells = {}
    for row in board_rows:
        for key, value in row["delta"].items():
            cells[key] = cells.get(key, 0) + int(value)
    return cells


class OfflineGate(object):
    """Deterministic runtime-failure stub (suite precedent): every
    check raises the gate-offline family so the text degrades into
    the persistent queue - the queued receipt is a completed submit
    window with honest zero water cells."""

    def check_text(self, text):
        raise P.GateOfflineError("consistency probe offline stub")


def main():
    frozen_before = {rel: sha16(os.path.join(UGCDIR, rel))
                     for rel in FROZEN}
    tmp = tempfile.mkdtemp(prefix="wc-probe-")
    with open(os.path.join(UGCDIR, "config.json"), encoding="utf-8") as handle:
        cfg = json.load(handle)
    gw = str(cfg["gate"]["gray_words"][0])
    db = os.path.join(tmp, "ugc.db")
    journal_db = os.path.join(tmp, "water_journal.db")
    lobby = load_lobby_store()
    ls = lobby.EventStore(db)
    pipe = P.UGCPipeline(cfg, db)
    sections = []
    fail = False
    try:
        # ---- AC-JC1: shared-birth zero-start proofs ------------------
        lv0 = pipe.store.pool_water_levels()
        z_levels = (lv0["pool_water_levels"]["noise"]["total"] == 0
                    and lv0["pool_water_levels"]["noise"]["by_reason"] == {}
                    and lv0["pool_water_levels"]["review"]["suspended"] == 0
                    and lv0["pool_water_levels"]["review"]["verdicted"]
                    == {"pass": 0, "risky": 0}
                    and lv0["total"] == 0)
        board0 = pipe.journal.journal_board()
        z_board = board0["total"] == 0 and board0["journal_board"] == []
        tally0 = pipe.journal.kind_tally()
        z_tally = (tally0["kind_tally"]
                   == {"batch": 0, "drain": 0, "ingest": 0,
                       "submit": 0, "verdict": 0}
                   and tally0["total"] == 0)
        sections.append("[1] shared-birth zero-start: levels=%s board=%s "
                       "tally=%s"
                       % (z_levels, z_board, z_tally))
        fail = fail or not (z_levels and z_board and z_tally)

        # ---- AC-JC2: real-flow world across the five window kinds ---
        def idea(actor, text):
            ls.append(lobby.utc_now_iso(), "idea.submit", actor, "cocreate",
                      text, payload={"text": text,
                                     "pool": "proposal-queue-stub"})

        rec_gray = pipe.submit("avatar_intake", "A-jc1",
                               "gray submit probe " + gw)
        rec_emoji = pipe.submit("avatar_intake", "A-jc2", EMOJI_A)
        rec_short = pipe.submit("avatar_intake", "A-jc3", SHORT)
        idea("C-80001", "clean ingest probe idea")
        idea("C-80002", "gray ingest probe idea " + gw)
        idea("C-80003", EMOJI_B)
        pipe.ingest_lobby()
        batch_receipts = pipe.submit_batch(
            "avatar_intake", "A-jc4",
            ["clean batch probe text", "gray batch probe " + gw,
             EMOJI_C])
        real_gate = pipe.batch.gate
        pipe.batch.gate = OfflineGate()
        try:
            rec_queued = pipe.submit("avatar_intake", "A-jc5",
                                     "gray drain probe " + gw)
        finally:
            pipe.batch.gate = real_gate
        drain_receipt = pipe.drain_recover()
        rec_batch_gray = next(r for r in batch_receipts
                             if isinstance(r, dict) and r.get("suspended"))
        pipe.review_verdict(rec_gray["evt_id"], "pass")
        try:
            pipe.review_verdict(rec_batch_gray["evt_id"], "risky")
        except P.UGC.PipelineError as exc:
            if exc.code != P.UGC.E_CONTENT_REJECTED:
                raise
        tally = pipe.journal.kind_tally()
        kinds_ok = all(tally["kind_tally"][k] >= 1
                       for k in ("ingest", "batch", "drain", "submit", "verdict"))
        queued_ok = isinstance(rec_queued, dict) and rec_queued.get("queued") is True
        sections.append("[2] world account: kind_tally=%s five-kinds>=1=%s "
                       "degraded-queued=%s drain=%s"
                       % (json.dumps(tally["kind_tally"], sort_keys=True),
                          kinds_ok, queued_ok,
                          json.dumps({k: drain_receipt[k]
                                      for k in sorted(drain_receipt)
                                      if k in ("drained", "passed", "rejected",
                                               "recovered")},
                                     sort_keys=True)))
        fail = fail or not (kinds_ok and queued_ok)

        # ---- AC-JC3: end-to-end invariant cross (core) ---------------
        journal_env = pipe.journal.cell_totals()
        levels_env = pipe.store.pool_water_levels()
        all_match, rows, comp, composition_ok = cross(journal_env, levels_env)
        hand = hand_sum_cells(pipe.journal.journal_board()["journal_board"])
        hand_ok = all(int(hand.get(k, 0)) == int(v)
                      for k, v in journal_env["cell_totals"].items()) \
            and set(hand) == set(journal_env["cell_totals"])
        sections.append("[3] journal-vs-store cross:")
        sections.extend("    " + r for r in rows)
        sections.append("    composition journal_total=%d noise+susp=%d "
                       "store_total=%d %s"
                       % (comp[0], comp[1], comp[2],
                          "OK" if composition_ok else "DRIFT"))
        sections.append("    third-path hand-sum=%s"
                       % ("OK" if hand_ok else "DRIFT"))
        fail = fail or not (all_match and composition_ok and hand_ok)

        # ---- AC-JC4: drift injection negative path -------------------
        conn = sqlite3.connect(journal_db)
        conn.execute(
            "INSERT INTO water_windows (kind, delta, total_delta, ts_utc) "
            "VALUES ('submit', ?, 5, '2026-10-11T00:00:00.000000Z')",
            (json.dumps({"noise.total": 5}, sort_keys=True),))
        conn.commit()
        conn.close()
        drift_env = pipe.journal.cell_totals()
        drift_match, drift_rows, drift_comp, drift_comp_ok = cross(
            drift_env, levels_env)
        named = [r for r in drift_rows if "DRIFT" in r]
        drift_named = any("noise.total" in r for r in named)
        sections.append("[4] drift injection: rows=%d named=%d "
                       "noise.total-named=%s verdict=DRIFT-DETECTED"
                       % (len(named), len(named), drift_named))
        sections.extend("    " + r for r in named)
        sections.append("    drift composition journal_total=%d "
                       "noise+susp=%d store_total=%d %s"
                       % (drift_comp[0], drift_comp[1], drift_comp[2],
                          "OK" if drift_comp_ok else "DRIFT"))
        fail = fail or not (not drift_match and drift_named)

        # ---- AC-JC5: hygiene -----------------------------------------
        with open(os.path.abspath(__file__), "rb") as handle:
            self_bytes = handle.read()
        ascii_ok = max(self_bytes) < 128
        net_ok = True
        with open(os.path.abspath(__file__), encoding="utf-8") as handle:
            for line in handle:
                s = line.strip()
                if s.startswith("import ") or s.startswith("from "):
                    if any(w in s for w in ("urllib", "requests",
                                            "socket", "http")):
                        net_ok = False
        frozen_after = {rel: sha16(os.path.join(UGCDIR, rel))
                        for rel in FROZEN}
        frozen_ok = frozen_before == frozen_after
        sections.append("[5] hygiene: probe-ascii=%s import-lines-clean=%s "
                       "frozen=%s (%s)"
                       % (ascii_ok, net_ok, frozen_ok,
                          " ".join("%s:%s" % (rel, sha)
                                   for rel, sha in sorted(
                                       frozen_after.items()))))
        fail = fail or not (ascii_ok and net_ok and frozen_ok)
    finally:
        pipe.close()
        ls.close()

    verdict = "CONSISTENT+DETECTING" if not fail else "PROBE-FAIL"
    print("\n".join(sections))
    print("PROBE VERDICT: %s" % verdict)
    return 0 if not fail else 2


if __name__ == "__main__":
    sys.exit(main())
