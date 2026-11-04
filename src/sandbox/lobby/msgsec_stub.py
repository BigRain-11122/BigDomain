"""msgSecCheck contract + local stub for the lobby sandbox (P-47-3).

The production content-safety gate is WeChat msgSecCheck v2:

    POST https://api.weixin.qq.com/wxa/msg_sec_check?access_token=...
    {"content": "<text>", "version": 2, "scene": 2, "openid": "<openid>"}
    -> {"errcode": 0, "errmsg": "ok", "trace_id": "...",
        "result": {"suggest": "pass|review|risky", "label": <int>}}

Wiring the real endpoint needs the mini-program appid/secret, which is a CEO
physical item (account domain is never self-served). Until it lands the
sandbox answers the same shape from the local wordlists in config.json, so
the caller code is written once and only the transport is swapped.

Fail-closed law: a stub built without wordlists raises GateOfflineError,
because a content gate that cannot answer must never read as "pass".
"""

import hashlib

from sec_gate import GateOfflineError, SecGate

PROVIDER_STUB = "stub"
PROVIDER_WECHAT = "msgSecCheck-v2"

# WeChat v2 suggest vocabulary. "review" means human queue, never a pass.
SUGGEST_PASS = "pass"
SUGGEST_REVIEW = "review"
SUGGEST_RISKY = "risky"

E_MSSC_UNWIRED = "E_MSSC_UNWIRED"


class MsgSecStub:
    """Local msgSecCheck responder with the production response shape."""

    def __init__(self, forbidden_words, advisory_ban_words):
        if not forbidden_words or not advisory_ban_words:
            raise GateOfflineError("msgSecCheck stub built without wordlists")
        self.gate = SecGate(forbidden_words, advisory_ban_words)

    @classmethod
    def from_config(cls, cfg):
        gate_cfg = cfg.get("gate") if isinstance(cfg, dict) else None
        if not isinstance(gate_cfg, dict):
            raise GateOfflineError("gate section missing from config")
        return cls(gate_cfg.get("forbidden_words"), gate_cfg.get("advisory_ban_words"))

    def check(self, content, openid="sandbox-local"):
        """Answer with the WeChat v2 response shape (mock, non-billable)."""
        text = "" if content is None else str(content)
        if not text.strip():
            # Empty content is not reviewed by the real endpoint either.
            return self._resp(SUGGEST_PASS, 100, text, openid)

        for word in self.gate.forbidden_words:
            if word and word in text:
                return self._resp(SUGGEST_RISKY, 20001, text, openid)
        for word in self.gate.advisory_ban_words:
            if word and word in text:
                return self._resp(SUGGEST_REVIEW, 20002, text, openid)
        return self._resp(SUGGEST_PASS, 100, text, openid)

    def _resp(self, suggest, label, text, openid):
        trace = hashlib.sha256((str(openid) + "|" + text).encode("utf-8")).hexdigest()[:32]
        return {
            "errcode": 0,
            "errmsg": "ok",
            "trace_id": trace,
            "result": {"suggest": suggest, "label": label},
            "provider": PROVIDER_STUB,
            "mock": True,
            "billable": False,
        }

    @staticmethod
    def is_risky(resp):
        return resp.get("result", {}).get("suggest") == SUGGEST_RISKY

    @staticmethod
    def needs_review(resp):
        return resp.get("result", {}).get("suggest") == SUGGEST_REVIEW


def contract():
    """Machine-readable contract the real endpoint must satisfy."""
    return {
        "provider_prod": PROVIDER_WECHAT,
        "endpoint": "https://api.weixin.qq.com/wxa/msg_sec_check",
        "transport": "POST",
        "query": ["access_token"],
        "request_keys": ["content", "version", "scene", "openid"],
        "response_keys": ["errcode", "errmsg", "trace_id", "result"],
        "result_keys": ["suggest", "label"],
        "suggest_values": [SUGGEST_PASS, SUGGEST_REVIEW, SUGGEST_RISKY],
        "fail_closed": "unwired or error -> refuse serve (E_GATE_OFFLINE / " + E_MSSC_UNWIRED + ")",
        "blocked_on": "CEO physical item: mini-program appid/secret",
    }


def main():
    import argparse
    import json
    import os

    parser = argparse.ArgumentParser(description="msgSecCheck local stub (sandbox only)")
    parser.add_argument("--config", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"))
    parser.add_argument("--check", default=None, help="content to check")
    parser.add_argument("--contract", action="store_true", help="print the endpoint contract")
    parser.add_argument("--parity", action="store_true", help="prove the stub agrees with the shipped gate")
    args = parser.parse_args()

    if args.contract:
        print(json.dumps(contract(), ensure_ascii=False, indent=2))
        return 0
    with open(args.config, "r", encoding="utf-8") as fh:
        cfg = json.load(fh)
    stub = MsgSecStub.from_config(cfg)
    if args.parity:
        # The stub replaces gate 1 only if it answers exactly like the
        # shipped wordlist gate; prove that here instead of asserting it.
        gate_cfg = cfg["gate"]
        gate = SecGate(gate_cfg["forbidden_words"], gate_cfg["advisory_ban_words"])
        cases = (
            [(w, SUGGEST_RISKY, 1) for w in gate_cfg["forbidden_words"]]
            + [(w, SUGGEST_REVIEW, 2) for w in gate_cfg["advisory_ban_words"]]
            + [("plain research note", SUGGEST_PASS, 0)]
        )
        bad = []
        for text, want, want_gate in cases:
            got = stub.check(text)["result"]["suggest"]
            if got != want:
                bad.append((text, want, got))
        refused = 0
        for text, want, want_gate in cases:
            try:
                gate.check_text(text)
                raised = 0
            except Exception as exc:  # ContentRejectedError
                raised = getattr(exc, "gate", 0)
            if raised == want_gate:
                refused += 1
        verdict = "PARITY-OK" if not bad and refused == len(cases) else "PARITY-DIFFERS"
        print("MSGSEC PARITY cases=%d stub_mismatch=%d gate_agree=%d verdict=%s"
              % (len(cases), len(bad), refused, verdict))
        for row in bad:
            print("  MISMATCH %r want=%s got=%s" % row)
        return 0 if verdict == "PARITY-OK" else 2
    if args.check is None:
        print("usage: python msgsec_stub.py --check TEXT | --contract")
        return 5
    resp = stub.check(args.check)
    print(json.dumps(resp, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())