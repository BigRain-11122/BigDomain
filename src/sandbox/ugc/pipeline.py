"""UGC + msgSecCheck pipeline sandbox (BigDomain P-47-3b).

Implements the pre-registered criteria AC-U1..AC-U12 from
docs/spec/ugc-pipeline-spec.md section 1 (criteria were registered
before this code; honesty law). Stdlib only, zero external wiring:
msgSecCheck is the one real production touchpoint and it stays blocked
on CEO physical items (platform credentials; account domain is never
self-served), so the sandbox gate is a wordlist mock imported from the
lobby gate product (src/sandbox/lobby/sec_gate.py - referenced, not
copied).

Pipeline order is constitutional (spec section 2):
  intake -> gate 1 (pass|review|risky) -> gate 2 (non-advisory)
  -> routing (six lines + unsorted, config-driven) -> noise triage
  -> pooled -> drafted (rule template; no LLM on any server face)
  -> final_review (small ideas: L0 self-decide; landfall scale:
  needs_ceo_review, CEO approval only - P1 never self-served)
  -> adopted | rejected -> chronicled.
Gate receipts open only at adoption (AC-U10); every terminal state
lands in the city chronicle (AC-U12).

Startup self-checks refuse construction (E_GATE_OFFLINE family; main()
exits 2) when the gate config is missing/unwired or the export dir
escapes this repo (AC-U2/AC-U11). Encoding discipline: this script
stays ASCII; Chinese copy lives in config.json.

Run (readiness self-check = sandbox serve mode):
    python pipeline.py
    python pipeline.py --config config.json --db data/ugc.db
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
_LOBBY = os.path.normpath(os.path.join(BASE, "..", "lobby"))
for _p in (_LOBBY, BASE):
    # deterministic order: BASE stays ahead of the lobby dir so "import
    # store" resolves to this package's store, while sec_gate still comes
    # from the lobby product (referenced, not copied)
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

from sec_gate import (ContentRejectedError, GateOfflineError,  # lobby gate product
                      SecGate)
import store as UGC
from review import ReviewDesk
from wordlist import PreFilter  # L1 local pre-filter (OH-20261002 wiring)
from sec_batch import SecBatchFace, ST_DRAINED_PASS  # batch + degraded queue (R1681)

REPO_ROOT = os.path.realpath(os.path.join(BASE, "..", "..", ".."))
SOURCES = ("direct", "lobby_idea", "avatar_intake", "live_danmaku")


def compute_evt_id(source, actor, content):
    """Content-addressed intake id over (source, actor, content): same
    source + actor + content replays onto one id (AC-U6 UNIQUE), cross
    sources land as separate rows with a duplicate_of marker."""
    canonical = "|".join((source, actor, content))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


class UGCPipeline:
    def __init__(self, config, db_path):
        self._startup_checks(config)
        self.config = config
        self.db_path = db_path
        self.store = UGC.UGCStore(db_path)
        self.desk = ReviewDesk(self.store)
        self._rate = defaultdict(deque)
        # batch face wraps the SAME gate instance (referenced, not
        # copied); the degraded queue rides next to ugc.db so every
        # instance shares one recovery namespace (AC-PW1). Built last:
        # refused constructions never open the queue file.
        queue_db = os.path.join(
            os.path.dirname(os.path.abspath(db_path)), "sec_degraded.db")
        try:
            self.batch = SecBatchFace(self.gate, queue_db, config=config)
        except ValueError as exc:
            self.store.close()
            raise GateOfflineError("sec_batch config invalid: %s" % exc)

    # ---- startup self-checks (serve refusal family) -----------------------

    def _startup_checks(self, config):
        if not isinstance(config, dict):
            raise GateOfflineError("config not loaded")
        self.config = config
        self.gate = SecGate.from_config(config)  # AC-U2 (raises GateOfflineError)
        gate_cfg = config.get("gate") or {}
        gray = gate_cfg.get("gray_words")
        if not isinstance(gray, list) or not [w for w in gray if str(w)]:
            raise GateOfflineError("gate.gray_words missing or empty (AC-U2/AC-U3)")
        self.gray_words = [str(w) for w in gray if str(w)]
        self.prefilter = PreFilter.from_config(config)  # L1; None = unwired
        self.local_hit_count = 0  # platform calls saved by the local trie
        noise_cfg = config.get("noise") or {}
        try:
            self.emoji_re = re.compile(str(noise_cfg.get("emoji_pattern", "")))
        except re.error as exc:
            raise GateOfflineError("noise.emoji_pattern invalid: %s" % exc)
        self.min_len = int(noise_cfg.get("min_content_len", 4))
        self.flood_window = float(noise_cfg.get("flood_window_seconds", 60))
        self.flood_max = int(noise_cfg.get("flood_max_submissions", 5))
        comp = config.get("compliance") or {}
        self.disclaimer = str(comp.get("disclaimer", ""))
        if not self.disclaimer:
            raise GateOfflineError("compliance.disclaimer missing (AC-U8 resident face)")
        self.disclaimer_persistent = bool(comp.get("disclaimer_persistent", True))
        self.ai_label = str(comp.get("ai_label_text", ""))
        self.draft_risk_note = str(comp.get("draft_risk_note", ""))
        self.chronicle_note = str(comp.get("chronicle_note", ""))
        self.max_len = int(config.get("max_content_len", 2000))
        src_cfg = config.get("sources") or {}
        self.enabled = set(str(s) for s in src_cfg.get("enabled", SOURCES[:3]))
        self.entrance_required = set(
            str(s) for s in src_cfg.get("entrance_required", ("direct",)))
        self.entrance_cfg = config.get("entrance") or {}
        rate = config.get("rate_limit") or {}
        self.rate_max = int(rate.get("max_submissions", 5))
        self.rate_window = float(rate.get("window_seconds", 10))
        approval = config.get("approval") or {}
        self.threshold_len = int(approval.get("threshold_len", 30))
        self.landfall_keywords = [
            str(k) for k in approval.get("landfall_keywords", []) if str(k)]
        hot = config.get("hot") or {}
        self.hot_min = int(hot.get("min_score", 0))
        self.hot_factor = int(hot.get("score_len_factor", 1))
        self.export_dir = self._resolve_export_dir(config.get("export") or {})

    def _resolve_export_dir(self, export_cfg):
        raw = str(export_cfg.get("dir", "export"))
        candidate = raw if os.path.isabs(raw) else os.path.join(BASE, raw)
        real = os.path.realpath(candidate)
        try:
            inside = os.path.commonpath([REPO_ROOT, real]) == REPO_ROOT
        except ValueError:
            inside = False
        if not inside:
            # cross-repo writes are forbidden; exports are the only outflow
            # face and they stay inside this repo (AC-U11)
            raise GateOfflineError("export dir escapes this repo (AC-U11): " + raw)
        return real

    def close(self):
        self.batch.close()
        self.store.close()

    @classmethod
    def startup_check(cls, config, db_path):
        """Sandbox readiness probe: constructs the pipeline (all startup
        self-checks run in the constructor), then closes it."""
        pipe = cls(config, db_path)
        pipe.close()
        return True

    # ---- intake faces ------------------------------------------------------

    def grant_entrance_sandbox(self, actor, ttl_seconds=None):
        """Mock entrance credential (production = P-47-4 payment receipt;
        account domain = CEO physical items, never self-served)."""
        ttl = int(ttl_seconds if ttl_seconds is not None
                  else self.entrance_cfg.get("ttl_seconds", 3600))
        self.store.entrance_grant(actor, ttl)
        return {"actor": actor, "mock": True, "ttl_seconds": ttl}

    def _validate_source(self, source):
        if source not in SOURCES:
            raise UGC.PipelineError(UGC.E_BAD_SOURCE, str(source))
        if source not in self.enabled:
            raise UGC.PipelineError(
                UGC.E_SOURCE_BLOCKED, "%s reserved (AC-UP3 stream bridge)" % source)

    def _check_rate(self, actor):
        now = datetime.now(timezone.utc)
        times = self._rate[actor]
        cutoff = now - timedelta(seconds=self.rate_window)
        while times and times[0] < cutoff:
            times.popleft()
        if len(times) >= self.rate_max:
            raise UGC.PipelineError(
                UGC.E_RATE_LIMIT, "%d per %gs" % (self.rate_max, self.rate_window))
        times.append(now)

    def submit(self, source, actor, content, **client_hints):
        """Direct intake face. client_hints (producer/ai_generated) are
        deliberately ignored: the server alone stamps provenance (AC-U7)."""
        client_hints.pop("producer", None)
        client_hints.pop("ai_generated", None)
        self._validate_source(source)
        if source in self.entrance_required and not self.store.entrance_valid(actor):
            raise UGC.PipelineError(UGC.E_ENTRANCE_REQUIRED, str(actor))
        if source == "direct":
            self._check_rate(actor)
        return self._process(source, actor, content)

    def submit_batch(self, source, actor, texts):
        """Batch intake face (AC-PW4): per-text prefilter and rate faces,
        then ONE real batch gate call per max_batch chunk. The budget
        face degrades the ungated suffix into the persistent queue
        (fail-closed: never passed, never lost). One bad text never
        aborts the batch - every text gets its own receipt."""
        self._validate_source(source)
        if source in self.entrance_required and not self.store.entrance_valid(actor):
            raise UGC.PipelineError(UGC.E_ENTRANCE_REQUIRED, str(actor))
        cleaned = [str(t or "").strip()[: self.max_len] for t in texts]
        receipts = [None] * len(cleaned)
        gate_idx = []
        for i, text in enumerate(cleaned):
            if not text:
                receipts[i] = {"received": False, "queued": False,
                               "code": UGC.E_BAD_FRAME, "text_index": i}
                continue
            hit = None
            if self.prefilter is not None:
                hit = self.prefilter.check(text)
                if hit is not None:
                    self.local_hit_count += 1
            if hit is not None:
                receipts[i] = {"received": False, "queued": False,
                               "code": UGC.E_CONTENT_REJECTED, "text_index": i}
            else:
                gate_idx.append(i)
        if source == "direct":
            for i in list(gate_idx):
                try:
                    self._check_rate(actor)
                except UGC.PipelineError as exc:
                    receipts[i] = {"received": False, "queued": False,
                                   "code": exc.code, "text_index": i}
                    gate_idx.remove(i)
        for start in range(0, len(gate_idx), self.batch.max_batch):
            piece = gate_idx[start:start + self.batch.max_batch]
            out = self.batch.check_batch(
                [cleaned[i] for i in piece], source=source, actor=actor)
            verdicts, degraded = out["verdicts"], out["degraded"]
            # in-chunk mapping law: verdicts cover the piece prefix in
            # order, the degraded qids cover the suffix in order
            for j, (kind, gate_no, _word, _text) in enumerate(verdicts):
                i = piece[j]
                if kind == "rejected":
                    receipts[i] = {"received": False, "queued": False,
                                   "code": UGC.E_CONTENT_REJECTED,
                                   "text_index": i}
                    continue
                try:
                    rec = self._after_gate(source, actor, cleaned[i])
                except UGC.PipelineError as exc:
                    rec = {"received": False, "queued": False,
                           "code": exc.code, "text_index": i}
                rec["text_index"] = i
                receipts[i] = rec
            for k, (qid, _landed) in enumerate(degraded):
                i = piece[len(verdicts) + k]
                receipts[i] = {"received": False, "queued": True,
                               "qid": qid, "text_index": i}
        return receipts

    def degraded_banner(self):
        """Degraded in-app banner face: the persistent queue read side
        (rows ARE the queue), disclaimer resident (AC-PW3/AC-PW6)."""
        keys = ("qid", "source", "actor", "content", "reason",
                "status", "ts_utc")
        return self._disclaimer({"queued": [
            dict(zip(keys, row)) for row in self.batch.banner_queue()]})

    def drain_recover(self):
        """End-to-end recovery (AC-PW5): re-gate the degraded queue
        (face.drain), then re-enter the post-gate flow for every clean
        row. Rows from other namespaces stay face-owned (source not in
        SOURCES); rows whose event already exists are skipped - the
        recovery is idempotent across restarts."""
        stats = self.batch.drain()
        recovered, skipped, failed = [], 0, 0
        for row in self.batch.rows_by_status(ST_DRAINED_PASS):
            q_source, q_actor, q_content = row[1], row[2], row[3]
            if q_source not in SOURCES:
                continue  # another namespace owns its own republish
            evt_id = compute_evt_id(q_source, q_actor, q_content)
            if self.store.event_row(evt_id) is not None:
                skipped += 1
                continue
            try:
                self._after_gate(q_source, q_actor, q_content)
                recovered.append(evt_id)
            except UGC.PipelineError:
                failed += 1  # honest count; the queue row keeps its
                # terminal drained_pass verdict either way
        return self._disclaimer({
            "drained": stats["drained"], "passed": stats["passed"],
            "rejected": stats["rejected"],
            "still_queued": stats["still_queued"],
            "recovered": recovered, "skipped_existing": skipped,
            "failed_publish": failed})

    def ingest_lobby(self):
        """Diverting reader: the real consumer of the lobby idea.submit
        (AC-S10) and avatar.intake (AC-S12) streams. One DB, tables
        split. The lobby already enforced entrance + gates upstream; this
        face re-runs its own gates anyway (defense in depth).

        Batched gate window (AC-IL1..IL6): rows are parsed in window
        order, the local L1 pre-filter runs per row BEFORE any gate
        call (paid-call saving), then the surviving rows reach the
        gate as ONE check_batch call per (source, actor) group chunk
        instead of one call per row. The face takes a single
        source/actor pair per call, so rows are grouped by that pair -
        mixing groups would mislabel degraded queue rows with the
        wrong metadata. Post-gate flow still replays in window order
        (AC-IL3): gray/noise/flood/duplicate state stays identical to
        the old per-row semantics."""
        rows = self.store.lobby_intake_rows()
        # phase 1: parse + local classification (window order kept)
        parsed = []  # [origin, source, actor, text, kind, qid]
        for origin, evt_type, actor, payload_json in rows:
            try:
                payload = json.loads(payload_json) if payload_json else {}
            except json.JSONDecodeError:
                payload = {}
            if evt_type == "idea.submit":
                source, text = "lobby_idea", str(payload.get("text", ""))
            else:  # avatar.intake (household registration itself = BigLife T-04)
                name, intro = str(payload.get("name", "")), str(payload.get("intro", ""))
                source, text = "avatar_intake", ((name + " - " + intro) if intro else name)
            text = text.strip()[: self.max_len]
            if not text:
                kind = "bad"
            elif (self.prefilter is not None
                  and self.prefilter.check(text) is not None):
                self.local_hit_count += 1  # local catch, zero gate calls
                kind = "l1"
            else:
                kind = "gate"
            parsed.append([origin, source, actor, text, kind, None])
        # phase 2: batched gate - one call per (source, actor) chunk
        groups = {}
        for i, row in enumerate(parsed):
            if row[4] == "gate":
                groups.setdefault((row[1], row[2]), []).append(i)
        for (source, actor), idxs in groups.items():
            for start in range(0, len(idxs), self.batch.max_batch):
                piece = idxs[start:start + self.batch.max_batch]
                out = self.batch.check_batch(
                    [parsed[i][3] for i in piece], source=source, actor=actor)
                verdicts, degraded = out["verdicts"], out["degraded"]
                # in-chunk mapping law: verdicts cover the piece prefix
                # in order, the degraded qids cover the suffix in order
                for j, (kind, _gate_no, _word, _text) in enumerate(verdicts):
                    parsed[piece[j]][4] = "rejected" if kind == "rejected" else "pass"
                for k, (qid, _landed) in enumerate(degraded):
                    target = parsed[piece[len(verdicts) + k]]
                    target[4], target[5] = "degraded", qid
        # phase 3: window-order replay (old per-row loop semantics)
        receipts = []
        for origin, source, actor, text, kind, qid in parsed:
            if kind == "degraded":
                # consumed by the reader, content persisted in the
                # degraded queue; single recovery path = drain_recover,
                # no silent loss (AC-PW3/AC-IL5)
                out = {"received": False, "queued": True, "qid": qid,
                       "gate": None, "origin_evt_id": origin}
                status = "queued"
            elif kind in ("l1", "rejected"):
                out = {"received": False, "code": UGC.E_CONTENT_REJECTED,
                       "origin_evt_id": origin}
                status = "rejected"
            elif kind == "bad":
                out = {"received": False, "code": UGC.E_BAD_FRAME,
                       "origin_evt_id": origin}
                status = UGC.E_BAD_FRAME
            else:  # pass: full post-gate flow, window order preserved
                try:
                    out = self._after_gate(source, actor, text,
                                           origin_evt_id=origin)
                    status = ("noise" if out.get("noise")
                              else ("review" if out.get("suspended")
                                    else "accepted"))
                except UGC.PipelineError as exc:
                    out = {"received": False, "code": exc.code,
                           "origin_evt_id": origin}
                    status = ("rejected" if exc.code == UGC.E_CONTENT_REJECTED
                              else exc.code)
            self.store.mark_ingest(origin, status, UGC.utc_now_iso())
            receipts.append(out)
        return receipts

    # ---- core pipeline -----------------------------------------------------

    def _process(self, source, actor, content, origin_evt_id=None):
        text = str(content or "").strip()[: self.max_len]
        if not text:
            raise UGC.PipelineError(UGC.E_BAD_FRAME, "content empty")
        try:
            if self.prefilter is not None:
                hit = self.prefilter.check(text)  # production L1: local
                if hit is not None:                # catch before the paid
                    self.local_hit_count += 1     # platform call (quota)
                    raise ContentRejectedError(1, hit)
        except ContentRejectedError as exc:
            # gate hits never land and never receipt (lobby AC-S4 same origin)
            raise UGC.PipelineError(
                UGC.E_CONTENT_REJECTED, "gate %d wordlist hit" % exc.gate) from None
        # gate 1 risky + gate 2 non-advisory ride the batch face (R1681
        # wiring, AC-PW2): a runtime gate failure degrades the text into
        # the persistent queue instead of losing it (AC-PW3)
        out = self.batch.check_batch([text], source=source, actor=actor)
        if out["degraded"]:
            qid = out["degraded"][0][0]
            return {"received": False, "queued": True, "qid": qid,
                    "gate": None, "origin_evt_id": origin_evt_id}
        kind, gate_no, _word, _text = out["verdicts"][0]
        if kind == "rejected":
            raise UGC.PipelineError(
                UGC.E_CONTENT_REJECTED, "gate %d wordlist hit" % gate_no)
        return self._after_gate(source, actor, text, origin_evt_id)

    def _after_gate(self, source, actor, text, origin_evt_id=None):
        """Post-gate flow (gray zone -> accept). Shared by submit,
        submit_batch and drain_recover; the recovery resume point is
        the gate: entrance and rate already passed on the original
        submit (AC-PW5)."""
        evt_id = compute_evt_id(source, actor, text)
        ts = UGC.utc_now_iso()
        gray_hit = next((w for w in self.gray_words if w and w in text), None)
        if gray_hit is not None:
            payload = {"content": text, "gate": "review", "gray_word": gray_hit}
            if origin_evt_id:
                payload["origin_evt_id"] = origin_evt_id
            self.store.insert_event(evt_id, ts, actor, source, text, payload)
            self.desk.open(evt_id, ts)  # no verdict = suspended forever (AC-U3)
            return {"received": True, "evt_id": evt_id, "gate": "review",
                    "suspended": True, "pooled": False, "noise": False, "line": None}
        return self._accept_clean(evt_id, ts, source, actor, text, origin_evt_id)

    def _accept_clean(self, evt_id, ts, source, actor, text,
                      origin_evt_id=None, event_exists=False):
        line, hits = self._route(text)
        noise_reason = self._noise_reason(actor, text)
        duplicate_of = self.store.content_seen(text, evt_id)
        if not event_exists:
            payload = {"content": text, "gate": "pass", "route": line,
                       "noise": bool(noise_reason), "route_keywords": hits}
            if noise_reason:
                payload["noise_reason"] = noise_reason
            if duplicate_of:
                payload["duplicate_of"] = duplicate_of
            if origin_evt_id:
                payload["origin_evt_id"] = origin_evt_id
            self.store.insert_event(evt_id, ts, actor, source, text, payload)
        if noise_reason:
            # honest triage: row kept, never pooled, never drafted (AC-U5)
            return {"received": True, "evt_id": evt_id, "gate": "pass",
                    "suspended": False, "pooled": False, "noise": True,
                    "line": line, "noise_reason": noise_reason}
        self.store.insert_item(evt_id, line, duplicate_of, ts)
        return {"received": True, "evt_id": evt_id, "gate": "pass",
                "suspended": False, "pooled": True, "noise": False,
                "line": line, "duplicate_of": duplicate_of}

    def _route(self, text):
        routing = self.config.get("routing") or {}
        for rule in routing.get("rules", []):
            line = str(rule.get("line", ""))
            hits = [str(k) for k in rule.get("keywords", [])
                    if str(k) and str(k) in text]
            if line and hits:
                return line, hits
        return str(routing.get("default_line", "unsorted")), []

    def _noise_reason(self, actor, text):
        stripped = self.emoji_re.sub("", text).strip()
        if not stripped:
            return "emoji_only"
        if len(stripped) < self.min_len:
            return "too_short"
        cutoff = _iso(datetime.now(timezone.utc)
                      - timedelta(seconds=self.flood_window))
        if self.store.count_recent(actor, cutoff) >= self.flood_max:
            return "flooding"
        return None

    # ---- review verdict (AC-U3) --------------------------------------------

    def review_verdict(self, evt_id, verdict, reviewer="sandbox-reviewer"):
        """pass -> the case re-enters the flow from routing; risky ->
        E_CONTENT_REJECTED (trace kept in the queue)."""
        self.desk.decide(evt_id, verdict, reviewer)
        row = self.store.event_row(evt_id)
        if row is None:
            raise UGC.PipelineError(UGC.E_NOT_FOUND, evt_id)
        return self._accept_clean(evt_id, UGC.utc_now_iso(), row["zone"],
                                  row["actor"], row["summary"], event_exists=True)

    # ---- draft + final review (AC-U7/AC-U9) --------------------------------

    def _item_or_404(self, item_id):
        row = self.store.item_row(item_id)
        if row is None:
            raise UGC.PipelineError(UGC.E_NOT_FOUND, str(item_id))
        return row

    def draft(self, item_id):
        """Rule-template organized first draft: producer is
        server-authoritative and ai_generated is true only for
        local_llm (never in this sandbox - zero LLM on server faces)."""
        row = self._item_or_404(item_id)
        if row["state"] != "pooled":
            raise UGC.PipelineError(
                UGC.E_BAD_STATE, "draft needs pooled, got " + row["state"])
        evt = self.store.event_row(item_id)
        content = str(evt["summary"])
        _, hits = self._route(content)
        tpl = self.config.get("draft_template") or {}
        labels = tpl.get("labels") or {}
        title_max = int(tpl.get("title_max_len", 24))
        draft = {
            "title": content[:title_max],
            str(labels.get("restated", "restated")): content,
            str(labels.get("suggested_line", "suggested_line")): row["line"],
            str(labels.get("matched_keywords", "matched_keywords")): hits,
            str(labels.get("risk_note", "risk_note")): self.draft_risk_note,
            "producer": "rule_template",   # server authority (AC-U7)
            "ai_generated": False,         # iff local_llm; rule template = never
            "ai_label": self.ai_label,
        }
        self.store.save_draft(item_id, draft)
        self.store.set_state(item_id, "drafted")
        return draft

    def final_review(self, item_id):
        """Threshold check: landfall-scale items auto-mark
        needs_ceo_review (CEO approval only, never auto-adopted); small
        ideas stay on the L0 self-decide path."""
        row = self._item_or_404(item_id)
        if row["state"] != "drafted":
            raise UGC.PipelineError(
                UGC.E_BAD_STATE, "final_review needs drafted, got " + row["state"])
        evt = self.store.event_row(item_id)
        content = str(evt["summary"])
        landfall = (len(content) >= self.threshold_len
                    or any(k in content for k in self.landfall_keywords))
        if landfall:
            self.store.to_needs_ceo(item_id)
            return {"item_id": item_id, "state": "needs_ceo_review", "needs_ceo": True}
        self.store.set_state(item_id, "final_review")
        return {"item_id": item_id, "state": "final_review", "needs_ceo": False}

    def record_ceo_decision(self, item_id, decision):
        """Sandbox stub for the CEO approval face: records the approval
        trace the DB trigger demands before adoption. The pipeline never
        fabricates this; production = the CEO's one-word reply lands here
        (P1: approval only, never self-served)."""
        if decision not in ("approved", "rejected"):
            raise UGC.PipelineError(UGC.E_BAD_DECISION, str(decision))
        self._item_or_404(item_id)
        self.store.ceo_receipt_upsert(item_id, decision)
        return {"item_id": item_id, "decision": decision}

    def final_decide(self, item_id, decision):
        if decision not in ("adopt", "reject"):
            raise UGC.PipelineError(UGC.E_BAD_DECISION, str(decision))
        row = self._item_or_404(item_id)
        if row["state"] not in ("final_review", "needs_ceo_review"):
            raise UGC.PipelineError(
                UGC.E_BAD_STATE,
                "decide needs final_review/needs_ceo_review, got " + row["state"])
        if row["state"] == "needs_ceo_review":
            want = "approved" if decision == "adopt" else "rejected"
            receipt = self.store.ceo_receipt(item_id)
            if not receipt or receipt["decision"] != want:
                raise UGC.PipelineError(UGC.E_CEO_RECEIPT_REQUIRED, str(item_id))
        if decision == "adopt":
            self.store.adopt_with_receipt(item_id)  # AC-U10: receipt at adoption
            return {"item_id": item_id, "state": "adopted"}
        self.store.set_state(item_id, "rejected", decision="rejected")
        return {"item_id": item_id, "state": "rejected"}

    # ---- read faces (AC-U4/AC-U8) -------------------------------------------

    def _disclaimer(self, out):
        out["disclaimer"] = self.disclaimer
        out["persistent"] = self.disclaimer_persistent
        return out

    def pool_query(self, line=None, states=("pooled", "drafted")):
        items = []
        for row in self.store.items_in_states(list(states), line=line):
            item = dict(row)
            item["evt_id"] = row["item_id"]  # 1:1 with the intake event
            item["draft"] = self.store.draft_row(row["item_id"])
            items.append(item)
        return self._disclaimer({"items": items})

    def _chronicle_row(self, row):
        return {
            "evt_id": row["item_id"],
            "summary": row["content"],
            "decision": row["decision"],
            "state": row["state"],
            "signature_slot": row["author"],
            "signature_eligible": row["state"] == "adopted",
            "credit": "named" if row["state"] == "adopted" else "record-only",
            "ts_utc": row["ts_utc"],
            "disclaimer": self.disclaimer,
        }

    def chronicle_query(self):
        items = [self._chronicle_row(r)
                 for r in self.store.items_in_states(["adopted", "chronicled"])]
        out = self._disclaimer({"items": items})
        out["note"] = self.chronicle_note
        return out

    def re_route(self, item_id):
        """Config-driven routing proof (AC-U4): re-runs the routing rules
        from the current config on a pooled item; code untouched."""
        row = self._item_or_404(item_id)
        if row["state"] != "pooled":
            raise UGC.PipelineError(
                UGC.E_BAD_STATE, "re_route needs pooled, got " + row["state"])
        evt = self.store.event_row(item_id)
        line, _ = self._route(str(evt["summary"]))
        if line != row["line"]:
            self.store.write("UPDATE ugc_items SET line = ? WHERE item_id = ?",
                             (line, item_id))
        return {"item_id": item_id, "line": line, "was": row["line"]}

    # ---- export faces (AC-U11/AC-U12) ---------------------------------------

    def export(self):
        """Three export faces inside this repo only. The chronicle step
        (rejected -> chronicled) runs first: every terminal state lands
        in the city chronicle."""
        self.store.write(
            "UPDATE ugc_items SET state = 'chronicled' WHERE state = 'rejected'")
        files = {}

        feed_dir = os.path.join(self.export_dir, "proposal_feed")
        os.makedirs(feed_dir, exist_ok=True)
        by_line = {}
        for row in self.store.items_in_states(["pooled", "drafted"]):
            by_line.setdefault(row["line"], []).append({
                "evt_id": row["item_id"], "line": row["line"], "state": row["state"],
                "producer": row["producer"], "ai_generated": bool(row["ai_generated"]),
                "duplicate_of": row["duplicate_of"], "content": row["content"],
                "ts_utc": row["ts_utc"], "disclaimer": self.disclaimer,
            })
        for line, rows in sorted(by_line.items()):
            path = os.path.join(feed_dir, line + ".jsonl")
            self._write_jsonl(path, rows)
            files["proposal_feed/" + line + ".jsonl"] = len(rows)

        chron = [self._chronicle_row(r)
                 for r in self.store.items_in_states(["adopted", "chronicled"])]
        self._write_jsonl(os.path.join(self.export_dir, "chronicle.jsonl"), chron)
        files["chronicle.jsonl"] = len(chron)

        hot_rows = []
        for row in self.store.items_in_states(["pooled", "drafted", "adopted"]):
            score = len(row["content"]) * self.hot_factor  # [needs-CEO] placeholder
            if score >= self.hot_min:
                hot_rows.append({
                    "evt_id": row["item_id"], "score": score, "line": row["line"],
                    "state": row["state"], "summary": row["content"],
                    "ts_utc": row["ts_utc"], "disclaimer": self.disclaimer,
                })
        hot_rows.sort(key=lambda r: r["score"], reverse=True)
        self._write_jsonl(os.path.join(self.export_dir, "hot_index.jsonl"), hot_rows)
        files["hot_index.jsonl"] = len(hot_rows)
        return {"export_dir": self.export_dir, "files": files}

    @staticmethod
    def _write_jsonl(path, rows):
        with open(path, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="BigDomain sandbox UGC pipeline (P-47-3b) readiness self-check")
    parser.add_argument("--config", default=os.path.join(BASE, "config.json"))
    parser.add_argument("--db", default=os.path.join(BASE, "data", "ugc.db"))
    args = parser.parse_args()
    try:
        with open(args.config, encoding="utf-8") as handle:
            cfg = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print("E_GATE_OFFLINE: config unreadable: %s" % exc, file=sys.stderr)
        return 2
    try:
        pipe = UGCPipeline(cfg, args.db)
    except GateOfflineError as exc:
        print(str(exc), file=sys.stderr)  # serve refusal, same family as lobby/ledger
        return 2
    pf = pipe.prefilter
    print("ugc pipeline ready: gate=ok pre_filter=%s gray_words=%d export=%s db=%s sources=%s sec_queue=%s"
          % ("%d words" % pf.word_count if pf is not None else "off",
             len(pipe.gray_words), pipe.export_dir, args.db,
             ",".join(sorted(pipe.enabled)), pipe.batch.db_path), flush=True)
    pipe.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
