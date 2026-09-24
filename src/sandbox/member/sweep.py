"""Period expiry sweep CLI (BigDomain P-47-5b, AC-M12).

Drives MemberStore.sweep_expired over the full sandbox wiring (lobby
events + ledger + pay docks). Idempotent: safe to re-run. One
conclusion line first; exit 0 on success, 2 on refusal (unwired gate /
unreadable config - the same serve-refusal family as every piece).

Usage:
    python sweep.py [--config config.json] [--db data/member.db]
                    [--now 2030-01-01T00:00:00Z]
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
_LOBBY = os.path.normpath(os.path.join(BASE, "..", "lobby"))
_PAY = os.path.normpath(os.path.join(BASE, "..", "pay"))
_LEDGER = os.path.normpath(os.path.join(BASE, "..", "ledger"))
for _p in (_LOBBY, _PAY, _LEDGER, BASE):
    # deterministic order: BASE first, then ledger/pay/lobby - same
    # module-resolution contract as member.py
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

from sec_gate import GateOfflineError  # noqa: E402 (lobby product)
import store as lobby_store             # noqa: E402 (lobby product)
from ledger import Ledger               # noqa: E402 (ledger product)
import orders as pay_orders             # noqa: E402 (pay product)
import member                           # noqa: E402 (this package)


def main():
    parser = argparse.ArgumentParser(
        description="BigDomain member period expiry sweep (AC-M12)")
    parser.add_argument("--config", default=os.path.join(BASE, "config.json"))
    parser.add_argument("--db", default=os.path.join(BASE, "data", "member.db"))
    parser.add_argument("--pay-config",
                        default=os.path.join(_PAY, "config.json"))
    parser.add_argument("--pay-db", default=os.path.join(_PAY, "data", "pay.db"))
    parser.add_argument("--events-db",
                        default=os.path.join(_PAY, "data", "events.db"))
    parser.add_argument("--ledger-db",
                        default=os.path.join(_LEDGER, "data", "ledger.db"))
    parser.add_argument("--ledger-config",
                        default=os.path.join(_LEDGER, "config.json"))
    parser.add_argument("--now", default=None,
                        help="override the sweep clock (ISO 8601 Z)")
    args = parser.parse_args()
    store = None
    pay = None
    led = None
    events = None
    try:
        with open(args.config, encoding="utf-8") as handle:
            cfg = json.load(handle)
        with open(args.pay_config, encoding="utf-8") as handle:
            pay_cfg = json.load(handle)
        with open(args.ledger_config, encoding="utf-8") as handle:
            led_cfg = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print("E_GATE_OFFLINE: config unreadable: %s" % exc, file=sys.stderr)
        return 2
    try:
        events = lobby_store.EventStore(args.events_db)
        led = Ledger(args.ledger_db, led_cfg)
        pay = pay_orders.PayOrders(pay_cfg, args.pay_db, events, led)
        store = member.MemberStore(cfg, args.db, pay)
        expired = store.sweep_expired(now=args.now)
        print("sweep done: periods_expired=%d now=%s"
              % (expired, args.now or "wallclock"), flush=True)
        return 0
    except GateOfflineError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        if store is not None:
            store.close()
        if pay is not None:
            pay.close()
        if led is not None:
            led.close()
        if events is not None:
            events.close()


if __name__ == "__main__":
    sys.exit(main())
