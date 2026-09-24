"""Gray-zone human review desk (AC-U3, BigDomain P-47-3b).

Production gray source = msgSecCheck suggest=review (AC-UP1, blocked on
CEO physical items); sandbox source = the config gray wordlist. A case
without a verdict stays suspended forever by default: never pooled,
never drafted, zero receipts (default = not allowed through). Verdicts
are recorded with reviewer + timestamp (trace kept), and a decided case
never decides twice. The risky verdict rejects with E_CONTENT_REJECTED
while the queue row keeps the trace.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import store as UGC  # shared error family lives there (no import cycle)


class ReviewDesk:
    def __init__(self, store):
        self.store = store

    def open(self, evt_id, ts):
        """Land a gray item in the queue: verdict NULL = suspended."""
        self.store.review_open(evt_id, ts)

    def row(self, evt_id):
        return self.store.review_row(evt_id)

    def is_suspended(self, evt_id):
        row = self.store.review_row(evt_id)
        return bool(row) and row["verdict"] is None

    def decide(self, evt_id, verdict, reviewer, ts=None):
        if verdict not in ("pass", "risky"):
            raise UGC.PipelineError(UGC.E_BAD_VERDICT, str(verdict))
        row = self.store.review_row(evt_id)
        if row is None:
            raise UGC.PipelineError(UGC.E_NOT_FOUND, evt_id)
        if row["verdict"] is not None:
            raise UGC.PipelineError(UGC.E_REVIEW_DONE, evt_id)
        self.store.review_set_verdict(evt_id, verdict, reviewer, ts or UGC.utc_now_iso())
        if verdict == "risky":
            # rejected after review; the queue row keeps reviewer + verdict
            raise UGC.PipelineError(UGC.E_CONTENT_REJECTED, "review verdict risky: " + evt_id)
        return True
