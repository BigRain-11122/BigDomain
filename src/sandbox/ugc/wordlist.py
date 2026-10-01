"""Local L1 pre-filter for the UGC pipeline (BigDomain P-47-3 wiring round).

Adoption wiring for the pooled OSS candidate OH-20261002 (window 3
slice, R837; registry row in docs/oss-harvest/README.md): houbb/
sensitive-word contributes its wordlist DATA face only - the Java
library itself is not adopted (zero stack pollution). The matcher is
self-written on stdlib (no fail links - a per-position greedy trie
walk, not full Aho-Corasick; content is capped at max_content_len so
this is ample).

Production order model (docs/spec/ugc-pipeline-spec.md):
  L1  this module: local trie scan over the real wordlist - free, and
      every local catch is a platform call saved (msgSecCheck quota)
  L2  platform msgSecCheck three-state - sandbox stand-in stays the
      config wordlist mock (SecGate), real wiring blocked on CEO
      physical items (AC-UP1; account domain is never self-served)
  then gray-review tier (pipeline.gray_words).

allow_words (config gate.pre_filter.allow_words, houbb's own
sensitive_word_allow.txt design): dict words our business context
handles downstream - gray-tier words (review desk, not rejection) and
product vocabulary the dict flags (e.g. routing keywords). An allowed
hit falls through to the next layer; it is a demotion, not a pass -
the content still runs the SecGate mock and the gray review.

check() returns the first non-allowed hit word, or None; it never
raises. The pipeline converts a hit to the lobby gate's
ContentRejectedError(1) family and counts it as a locally saved
platform call. Configured-but-unwired (missing/empty file) refuses
startup with GateOfflineError - no gate, no door.

Encoding discipline: this module stays ASCII; the wordlist itself is
a data file (wordlist_data/sensitive_words_dict.txt, verbatim from
the source repo; NOTICE + LICENSE live beside it).
"""

import os

from sec_gate import GateOfflineError  # lobby gate product (referenced)

BASE = os.path.dirname(os.path.abspath(__file__))


class PreFilter:
    """Trie matcher over the adopted wordlist. Built from config only."""

    def __init__(self, words, allow_words, source):
        self.source = str(source)
        self.allow_words = set(str(w) for w in allow_words if str(w))
        root = {}
        count = 0
        for word in words:
            node = root
            for ch in word:
                node = node.setdefault(ch, {})
            node[""] = word  # terminal marker -> full word
            count += 1
        self._root = root
        self.word_count = count

    @classmethod
    def from_config(cls, cfg):
        """Build from config dict; None when gate.pre_filter is absent
        (backward compatible), GateOfflineError when configured but the
        wordlist is unwired (file missing/unreadable/no words)."""
        if not isinstance(cfg, dict):
            raise GateOfflineError("config not loaded")
        gate_cfg = cfg.get("gate")
        if not isinstance(gate_cfg, dict):
            raise GateOfflineError("gate section missing from config")
        pf_cfg = gate_cfg.get("pre_filter")
        if pf_cfg is None:
            return None  # not wired in this config: legacy behavior
        if not isinstance(pf_cfg, dict):
            raise GateOfflineError("gate.pre_filter must be an object")
        raw = str(pf_cfg.get("file", ""))
        if not raw:
            raise GateOfflineError("gate.pre_filter.file missing")
        path = raw if os.path.isabs(raw) else os.path.join(BASE, raw)
        try:
            with open(path, encoding="utf-8") as handle:
                lines = handle.read().splitlines()
        except OSError as exc:
            raise GateOfflineError("pre-filter wordlist unreadable: %s" % exc)
        # observed source format: plain one word per line, no blanks, no
        # annotations (format scan 2026-10-01); 2 duplicate lines deduped
        words = []
        seen = set()
        for line in lines:
            word = line.strip()
            if word and word not in seen:
                seen.add(word)
                words.append(word)
        if not words:
            raise GateOfflineError("pre-filter wordlist empty: " + raw)
        allow = pf_cfg.get("allow_words", [])
        if not isinstance(allow, list):
            raise GateOfflineError("gate.pre_filter.allow_words must be a list")
        return cls(words, allow, pf_cfg.get("source", ""))

    def check(self, text):
        """First non-allowed dict word inside text, or None.

        Greedy trie walk from each position; an allowed terminal hit
        keeps the scan running (both deeper on the same position and
        onward) so an allowed word never masks a later real hit.
        """
        root = self._root
        allow = self.allow_words
        for start in range(len(text)):
            node = root
            for pos in range(start, len(text)):
                node = node.get(text[pos])
                if node is None:
                    break
                word = node.get("")
                if word is not None and word not in allow:
                    return word
        return None
