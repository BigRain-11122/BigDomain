"""Mock dual-channel payment adapters (BigDomain P-47-4b sandbox).

Channel differences live ONLY here (docs/spec/payment-integration-spec.md
section 0): 'virtual' = C-side in-app virtual goods (mini-program virtual
payment track, D2 ruling), 'standard' = B-side real services (standard
merchant API). The order domain sees one uniform callback contract.

Sandbox honesty: these are local mock gateways with explicitly fake test
keys (real credentials = CEO account-domain physical items, keys only in
.env, never in git). Real channel API endpoints are deliberately NOT
pre-written here - they align with the official docs on wiring day
(AC-YP1, blocked on physical items). Stdlib only, no external API call
is ever made by this file.

Callback contract (mock): {order_id, amount_cent, nonce, ts_utc, signer,
sig} where sig = HMAC-SHA256(key, canonical(order_id|amount_cent|nonce|
ts_utc|signer)). The four bad cases of AC-Y4 (bad signature / unknown
signer / stale timestamp / nonce replay) are all constructible against
this contract; nonce freshness itself is enforced by orders.py against
the receipts table.
"""

import datetime
import hashlib
import hmac


class AdapterError(Exception):
    """Callback verification failure. detail names the failed check."""

    def __init__(self, check):
        super().__init__("E_CALLBACK_REJECTED: " + str(check))
        self.check = str(check)


def utc_now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_ts(ts_utc):
    return datetime.datetime.strptime(str(ts_utc), "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc)


def _canonical(order_id, amount_cent, nonce, ts_utc, signer):
    return "|".join((str(order_id), str(int(amount_cent)), str(nonce),
                     str(ts_utc), str(signer)))


def _sign(key, order_id, amount_cent, nonce, ts_utc, signer):
    mac = hmac.new(str(key).encode("utf-8"),
                   _canonical(order_id, amount_cent, nonce, ts_utc, signer)
                   .encode("utf-8"), hashlib.sha256)
    return mac.hexdigest()


class MockChannel:
    """One mock gateway per channel: signer id + local test key + ts
    window. place() returns a mock prepay credential; make_callback()
    builds a signed callback payload (the sandbox stand-in for the real
    gateway pushing a payment notification)."""

    def __init__(self, channel, signer, key, ts_window_seconds=300):
        self.channel = str(channel)
        self.signer = str(signer)
        self.key = str(key)
        self.ts_window = int(ts_window_seconds)

    def place(self, order_id, amount_cent):
        """Mock prepay credential (production = channel prepay API)."""
        prepay_id = "mock-prepay-" + hashlib.sha256(
            ("%s|%s|%s" % (self.channel, order_id, amount_cent))
            .encode("utf-8")).hexdigest()[:12]
        return {"prepay_id": prepay_id, "channel_signer": self.signer,
                "channel": self.channel, "mock": True}

    def make_callback(self, order_id, amount_cent, nonce, ts_utc=None,
                      signer=None, key=None):
        """Build a signed callback for tests / sandbox flows."""
        ts = str(ts_utc or utc_now_iso())
        sg = str(signer or self.signer)
        k = str(key or self.key)
        sig = _sign(k, order_id, amount_cent, nonce, ts, sg)
        return {"order_id": str(order_id), "amount_cent": int(amount_cent),
                "nonce": str(nonce), "ts_utc": ts, "signer": sg, "sig": sig}

    def verify(self, payload):
        """Raise AdapterError on any signature-family failure (AC-Y4
        bads 1-3); nonce freshness is checked by orders.py (bad 4)."""
        try:
            order_id = str(payload["order_id"])
            amount_cent = int(payload["amount_cent"])
            nonce = str(payload["nonce"])
            ts_utc = str(payload["ts_utc"])
            signer = str(payload["signer"])
            sig = str(payload["sig"])
        except (KeyError, TypeError, ValueError) as exc:
            raise AdapterError("malformed payload: %s" % exc) from None
        if signer != self.signer:
            raise AdapterError("unknown signer: %s" % signer)
        try:
            ts = parse_ts(ts_utc)
        except ValueError:
            raise AdapterError("bad ts_utc: %s" % ts_utc) from None
        delta = abs((datetime.datetime.now(datetime.timezone.utc) - ts)
                    .total_seconds())
        if delta > self.ts_window:
            raise AdapterError("ts outside +-%ds window (delta=%.0fs)"
                               % (self.ts_window, delta))
        expect = _sign(self.key, order_id, amount_cent, nonce, ts_utc, signer)
        if not hmac.compare_digest(expect, sig):
            raise AdapterError("signature mismatch")
        return None


def from_config(config):
    """Build the two mock adapters from the pay config. Missing channel
    sections / keys are config errors (serve refusal family upstream)."""
    channels = (config or {}).get("channels") or {}
    out = {}
    for name in ("virtual", "standard"):
        spec = channels.get(name)
        if not isinstance(spec, dict):
            raise AdapterError("channels.%s missing" % name)
        signer = str(spec.get("signer", "")).strip()
        key = str(spec.get("mock_key", "")).strip()
        if not signer or not key:
            raise AdapterError("channels.%s signer/mock_key missing" % name)
        out[name] = MockChannel(name, signer, key,
                                int(spec.get("ts_window_seconds", 300)))
    return out
