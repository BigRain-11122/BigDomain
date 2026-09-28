"""WeChat Pay V3 callback face for the pay sandbox (BigDomain P-47-4b
follow-up: benchmarks collection 4012791902 / 4012075249 / 4012365342
wired into the sandbox verifier).

Collected official rules wired here (docs/global-benchmarks.md sec 1,
A-grade direct crawl 2026-09-27/28):
  - 4012791902 (payment-success callback notice): verification needs
    the four headers Wechatpay-Serial / Wechatpay-Signature /
    Wechatpay-Timestamp / Wechatpay-Nonce; the serial is the public-key
    id in fixed PUB_KEY_ID_<digits> format, otherwise the platform
    certificate serial; ack within 5s, success = 200/204 without a body,
    failure = 4XX/5XX with {"code":"FAIL","message":...}; upstream
    retries up to 15 times on the documented gradient, so duplicate
    callbacks must re-enter idempotently.
  - 4012365342 (APIv3 signing overview): the verification input string
    is exactly "<timestamp>\n<nonce>\n<body>\n".
  - 4012075249 (callback+query best practice): payment success
    criterion = signature verified AND trade_state == SUCCESS; amounts
    are in fen (cents).

Sandbox honesty (stand-in primitives, explicit, wiring-day swap faces):
  - Production verifies RSA-SHA256 with the WeChat Pay platform public
    key / platform certificate. The Python stdlib has no RSA and real
    keys are CEO account-domain physical items (keys only in .env,
    never in git), so the stand-in is HMAC-SHA256 over the REAL V3
    verification string. The input-string rule itself is
    production-faithful; only the signature primitive is a stand-in.
  - Production decrypts resource with AES-256-GCM under the APIv3 key
    (algorithm AEAD_AES_256_GCM). The stdlib has no AEAD and the sandbox
    must not fake one, so the stand-in is a reversible base64 envelope
    carrying the same field contract (algorithm / ciphertext /
    associated_data / nonce); wiring day swaps the primitive behind the
    same field contract.
  - The timestamp window is parameterized (benchmarks note: the
    official page does not state the window; parameterized-M stands).
  - No real payment API is called anywhere; no new external touchpoint.

The order domain still sees ONE uniform callback contract
(payment-integration-spec sec 2): the V3 translation nests the signed
envelope under payload["v3"], derives the six uniform fields FROM the
signed body (never the other way round, translation-injection guard),
and orders.handle_callback keeps its constitutional order unchanged.

Encoding discipline: this script stays ASCII; Chinese copy lives in
config/data files only.
"""

import base64
import datetime
import hashlib
import hmac
import json
import re

import adapters

_HEADERS = ("Wechatpay-Serial", "Wechatpay-Signature",
            "Wechatpay-Timestamp", "Wechatpay-Nonce")
_SERIAL_PUBKEY_RE = re.compile(r"^PUB_KEY_ID_[0-9]+$")
STANDIN_ALGORITHM = "AEAD_AES_256_GCM_SANDBOX_STANDIN"
PAYMENT_SUCCESS = "SUCCESS"  # 4012075249 criterion, literal state value
# 4012791902: upstream retry semantics (15 attempts max) live upstream;
# the sandbox side owes idempotent re-entry, handled by orders.py.
# The 5s ack budget is a production-latency note, not sandbox-testable.


def ack_ok():
    """Success ack per 4012791902: 200/204 family, no body."""
    return {"http_status": 200, "body": None}


def ack_fail(check, status=400):
    """Failure ack per 4012791902: 4XX/5XX with FAIL body."""
    return {"http_status": int(status),
            "body": {"code": "FAIL", "message": str(check)}}


def _unix_to_iso(ts_unix):
    return datetime.datetime.fromtimestamp(
        int(ts_unix), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _encode_resource(resource):
    raw = json.dumps(resource, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def _decode_resource(ciphertext):
    raw = base64.b64decode(str(ciphertext), validate=True)
    out = json.loads(raw.decode("utf-8"))
    if not isinstance(out, dict):
        raise ValueError("resource not an object")
    return out


class V3Channel(adapters.MockChannel):
    """MockChannel with the V3 callback contract: the same signer/key/
    window config, plus accepted Wechatpay-Serial values. Config key
    "callback_style": "v3" on a channel section routes here
    (adapters.from_config); absent key keeps the flat legacy contract,
    so the shipped config and the AC-Y baseline stay untouched."""

    def __init__(self, channel, signer, key, ts_window_seconds=300,
                 serials=None):
        super().__init__(channel, signer, key, ts_window_seconds)
        self.serials = tuple(str(s) for s in (serials or []))

    @classmethod
    def from_spec(cls, name, spec):
        signer = str(spec.get("signer", "")).strip()
        key = str(spec.get("mock_key", "")).strip()
        if not signer or not key:
            raise adapters.AdapterError(
                "channels.%s signer/mock_key missing" % name)
        raw = spec.get("v3_serials")
        serials = [str(s) for s in raw] if isinstance(raw, list) else []
        return cls(name, signer, key,
                   int(spec.get("ts_window_seconds", 300)), serials)

    # ---- builder (sandbox stand-in for the real gateway pushing a
    # notification; tests construct good and bad cases with it) --------

    def make_v3_callback(self, order_id, amount_cent, nonce,
                         ts_unix=None, serial=None, trade_state=None,
                         event_type="TRANSACTION.SUCCESS", key=None,
                         mchid="sandbox-mchid", appid="sandbox-appid"):
        ts = int(ts_unix) if ts_unix is not None else int(
            datetime.datetime.now(datetime.timezone.utc).timestamp())
        sg_serial = str(serial or (self.serials[0] if self.serials
                                   else "PUB_KEY_ID_0000000000"))
        resource = {
            "mchid": str(mchid), "appid": str(appid),
            "out_trade_no": str(order_id),
            "transaction_id": "sandbox-txn-%s" % hashlib.sha256(
                ("%s|%s" % (order_id, nonce)).encode("utf-8")).hexdigest()[:12],
            "trade_state": str(trade_state or PAYMENT_SUCCESS),
            "amount": {"total": int(amount_cent), "currency": "CNY"},
        }
        body = json.dumps({
            "id": "evt-%s" % hashlib.sha256(
                ("%s|%s|%s" % (order_id, nonce, ts)).encode("utf-8")
            ).hexdigest()[:16],
            "event_type": str(event_type),
            "summary": "payment notification (sandbox stand-in)",
            "resource": {"algorithm": STANDIN_ALGORITHM,
                         "ciphertext": _encode_resource(resource),
                         "associated_data": "transaction",
                         "nonce": "%s-res" % nonce},
        }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        sig = hmac.new(str(key or self.key).encode("utf-8"),
                       ("%d\n%s\n%s\n" % (ts, nonce, body))
                       .encode("utf-8"), hashlib.sha256).hexdigest()
        headers = {"Wechatpay-Serial": sg_serial,
                   "Wechatpay-Signature": sig,
                   "Wechatpay-Timestamp": str(ts),
                   "Wechatpay-Nonce": str(nonce)}
        # six uniform fields are DERIVED from the signed body above
        return {"order_id": resource["out_trade_no"],
                "amount_cent": resource["amount"]["total"],
                "nonce": str(nonce), "ts_utc": _unix_to_iso(ts),
                "signer": sg_serial, "sig": sig,
                "v3": {"headers": headers, "body": body}}

    # ---- verifier (adapter face called by orders.handle_callback) ----

    def verify(self, payload):
        env = payload.get("v3") if isinstance(payload, dict) else None
        if not isinstance(env, dict):
            raise adapters.AdapterError("malformed v3 envelope")
        headers = env.get("headers")
        body = env.get("body")
        if not isinstance(headers, dict) or not isinstance(body, str):
            raise adapters.AdapterError("malformed v3 envelope")
        for name in _HEADERS:  # AC-V31: four-header contract
            if not str(headers.get(name, "")).strip():
                raise adapters.AdapterError("missing header: %s" % name)
        serial = str(headers["Wechatpay-Serial"]).strip()
        if serial not in self.serials and not _SERIAL_PUBKEY_RE.match(serial):
            raise adapters.AdapterError("unknown serial: %s" % serial)
        try:
            ts = int(str(headers["Wechatpay-Timestamp"]).strip())
        except ValueError:
            raise adapters.AdapterError(
                "bad Wechatpay-Timestamp: %s"
                % headers["Wechatpay-Timestamp"]) from None
        delta = abs(datetime.datetime.now(datetime.timezone.utc).timestamp()
                    - ts)
        if delta > self.ts_window:  # AC-V33: parameterized window
            raise adapters.AdapterError(
                "ts outside +-%ds window (delta=%.0fs)"
                % (self.ts_window, delta))
        nonce = str(headers["Wechatpay-Nonce"]).strip()
        expect = hmac.new(self.key.encode("utf-8"),
                          ("%d\n%s\n%s\n" % (ts, nonce, body))
                          .encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expect, str(headers["Wechatpay-Signature"])):
            raise adapters.AdapterError("signature mismatch")
        try:  # AC-V35: envelope decode + field contract
            msg = json.loads(body)
            if not isinstance(msg, dict):
                raise ValueError("body not an object")
            res = _decode_resource(msg.get("resource", {}).get("ciphertext", ""))
            out_trade_no = str(res["out_trade_no"])
            trade_state = str(res["trade_state"])
            total_cent = int(res["amount"]["total"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise adapters.AdapterError("malformed resource: %s" % exc) from None
        # translation-injection guard: the visible uniform fields must
        # match the SIGNED body, never override it
        if (out_trade_no != str(payload.get("order_id"))
                or total_cent != int(payload.get("amount_cent", -1))
                or nonce != str(payload.get("nonce"))):
            raise adapters.AdapterError("uniform/body mismatch")
        if trade_state != PAYMENT_SUCCESS:  # AC-V36: 4012075249 criterion
            raise adapters.AdapterError(
                "trade_state=%s not %s (4012075249 criterion)"
                % (trade_state, PAYMENT_SUCCESS))
        return None
