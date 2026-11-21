"""ONE judgement for the published claims census, shared by both surfaces.

Why this exists (R3233, probe qa/probe-R3233.log): the same `claims` block in
docs/status-export.json was derived twice - once for the static page a reader
opens by path (tools/deliverable_index.py:claims_band) and once for the card
the live hub serves (src/sandbox/frontdoor.py:claims_card). Each carried its own
key tuple, its own validation and its own refusal prose. Measured consequences:

  * ZERO shipped file mentioned both faces, so neither could ever be compared
    to the other;
  * the faces already disagreed on one real shape: a block whose `present` is
    a string is refused by the card and printed as six numbers by the band;
  * a hand-drifted number in the landed page stayed silent (--check rc=0,
    VERDICT PASS 16/16) while a drifted `census_ts` was caught - the disk face
    pins the moment, never the numbers.

So this module owns the ONE judgement: which shape the block is in, and what
the six readings are. Rendering stays per surface - a file page writes prose
for a reader, the hub writes the card the server serves - but neither surface
decides what the block means any more.

No I/O: the caller passes the block it already read. This module never opens a
file, never stats one and never re-censuses.
"""

KEYS = ("claimed", "captured", "contradicted", "uncaptured", "historic", "rows")
STAMP_KEY = "census_ts"

ABSENT = "absent"        # no block at all (None, not a dict, or empty)
EMPTY = "empty"          # present is False: the census had no ledger to read
MALFORMED = "malformed"  # a reading is not a non-negative int, or present is bad
READING = "reading"      # six readings; present True/None; stamp str or None


def _is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def claims_view(block):
    """Return the one reading of a published claims block.

    The returned dict always carries the same five keys, so a renderer never
    has to guess:

        state    one of ABSENT / EMPTY / MALFORMED / READING
        bad      offending field names in KEYS order, then "present"
        counts   the six readings, only when state is READING
        present  True / False / None (absent field), only when READING or EMPTY
        stamp    the census moment or None, only when READING
    """
    empty = {"state": ABSENT, "bad": [], "counts": {}, "present": None,
             "stamp": None}
    if not isinstance(block, dict) or not block:
        return empty

    bad = []
    counts = {}
    for key in KEYS:
        value = block.get(key)
        if _is_count(value):
            counts[key] = value
        else:
            bad.append(key)

    present = block.get("present")
    if present is not None and not isinstance(present, bool):
        bad.append("present")
        present = None

    if bad:
        return {"state": MALFORMED, "bad": bad, "counts": {}, "present": None,
                "stamp": None}
    if present is False:
        return {"state": EMPTY, "bad": [], "counts": {}, "present": False,
                "stamp": None}

    stamp = block.get(STAMP_KEY)
    return {"state": READING, "bad": [], "counts": counts, "present": present,
            "stamp": stamp if isinstance(stamp, str) and stamp else None}
