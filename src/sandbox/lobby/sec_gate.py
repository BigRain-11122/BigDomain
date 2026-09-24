"""Sandbox security gates for the lobby WebSocket server (P-47-1b).

Gate pipeline order is constitutional (docs/spec/lobby-websocket-spec.md):
  gate 1  content safety: sandbox = wordlist mock (production = msgSecCheck,
          blocked on CEO physical items; an unwired gate refuses startup)
  gate 2  non-advisory: ban profit-promise / guaranteed-return wording
  gate 3  rate limit: lives in server.py (per-connection sliding window)

Wordlists and labels are data (config.json), not code literals, per the
encoding discipline (scripts stay ASCII; Chinese lives in data files).
"""

E_GATE_OFFLINE = "E_GATE_OFFLINE"
E_CONTENT_REJECTED = "E_CONTENT_REJECTED"


class GateOfflineError(Exception):
    """Content gate missing/unwired: serve mode must refuse to start."""

    def __init__(self, detail):
        super().__init__(E_GATE_OFFLINE + ": " + str(detail))
        self.code = E_GATE_OFFLINE


class ContentRejectedError(Exception):
    def __init__(self, gate, word):
        super().__init__(E_CONTENT_REJECTED)
        self.code = E_CONTENT_REJECTED
        self.gate = gate  # 1 = content safety, 2 = non-advisory
        self.word = word


class SecGate:
    """Two serial wordlist gates. Built from config only; a config without
    both non-empty wordlists raises GateOfflineError (no content safety =
    no door)."""

    def __init__(self, forbidden_words, advisory_ban_words):
        self.forbidden_words = [str(w) for w in forbidden_words if str(w)]
        self.advisory_ban_words = [str(w) for w in advisory_ban_words if str(w)]

    @classmethod
    def from_config(cls, cfg):
        if not isinstance(cfg, dict):
            raise GateOfflineError("config not loaded")
        gate_cfg = cfg.get("gate")
        if not isinstance(gate_cfg, dict):
            raise GateOfflineError("gate section missing from config")
        forbidden = gate_cfg.get("forbidden_words")
        advisory = gate_cfg.get("advisory_ban_words")
        if not isinstance(forbidden, list) or not [w for w in forbidden if str(w)]:
            raise GateOfflineError("gate.forbidden_words missing or empty")
        if not isinstance(advisory, list) or not [w for w in advisory if str(w)]:
            raise GateOfflineError("gate.advisory_ban_words missing or empty")
        return cls(forbidden, advisory)

    def check_text(self, text):
        """Raise ContentRejectedError on a gate hit; return None when clean."""
        for word in self.forbidden_words:
            if word and word in text:
                raise ContentRejectedError(1, word)
        for word in self.advisory_ban_words:
            if word and word in text:
                raise ContentRejectedError(2, word)
        return None
