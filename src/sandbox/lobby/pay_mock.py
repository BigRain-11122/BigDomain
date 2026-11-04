"""19.9 entrance payment + month-card MOCK for the lobby sandbox (P-47-4).

Production payment needs the WeChat merchant id, a CEO physical item, so this
module is a simulated channel and says so on every object it returns:

    chargeable = False   (never a real debit, never a real refund)
    mock       = True

The contract is the one the real channel must satisfy once the merchant id
lands: create_order -> pay -> receipt -> entitlement. Swapping the transport
must not change the caller.

Law: an order the mock did not create is refused, and the mock never claims
it settled money it did not settle.
"""

import uuid

E_PAYMOCK_BAD_ACTOR = "E_PAYMOCK_BAD_ACTOR"
E_PAYMOCK_BAD_AMOUNT = "E_PAYMOCK_BAD_AMOUNT"
E_PAYMOCK_UNKNOWN_ORDER = "E_PAYMOCK_UNKNOWN_ORDER"
E_PAYMOCK_STUB_ONLY = "E_PAYMOCK_STUB_ONLY"

CURRENCY = "CNY"
PRODUCT_ENTRANCE = "entrance_19_9"
PRODUCT_MONTH_CARD = "month_card_19_9"
PRICE_CENTS = 1990  # 19.90 CNY, the price canon of the C0 entrance

NON_CHARGEABLE_NOTE = (
    "SANDBOX MOCK: no money moves. Real 19.9 debit waits for the WeChat "
    "merchant id (CEO physical item)."
)


class PayMockError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(code + (": " + detail if detail else ""))
        self.code = code
        self.detail = detail


class PayMock:
    """In-memory mock channel: orders, receipts and month-card entitlements."""

    def __init__(self, price_cents=PRICE_CENTS, currency=CURRENCY):
        self.price_cents = int(price_cents)
        self.currency = currency
        self.orders = {}
        self.receipts = {}
        self.entitlements = {}

    # -- write face -------------------------------------------------

    def create_order(self, actor, product=PRODUCT_ENTRANCE, amount_cents=None):
        actor = str(actor or "").strip()
        if not actor:
            raise PayMockError(E_PAYMOCK_BAD_ACTOR, "actor required")
        amount = self.price_cents if amount_cents is None else int(amount_cents)
        if amount != self.price_cents:
            raise PayMockError(
                E_PAYMOCK_BAD_AMOUNT,
                "mock channel is pinned to the 19.9 canon: %d" % self.price_cents,
            )
        order_id = "sbx-order-" + uuid.uuid4().hex
        order = {
            "order_id": order_id,
            "actor": actor,
            "product": product,
            "amount_cents": amount,
            "currency": self.currency,
            "state": "created",
            "chargeable": False,
            "mock": True,
            "channel": "mock",
            "pay_url": "mock://sandbox/pay/" + order_id,
            "note": NON_CHARGEABLE_NOTE,
        }
        self.orders[order_id] = order
        return dict(order)

    def pay(self, order_id):
        order = self.orders.get(str(order_id or ""))
        if order is None:
            raise PayMockError(E_PAYMOCK_UNKNOWN_ORDER, str(order_id))
        if order["state"] == "paid":
            receipt = dict(self.receipts[order_id])
            receipt["replay"] = True
            return receipt
        order["state"] = "paid"
        receipt = {
            "receipt_no": "sbx-receipt-" + uuid.uuid4().hex,
            "order_id": order_id,
            "actor": order["actor"],
            "product": order["product"],
            "amount_cents": order["amount_cents"],
            "currency": order["currency"],
            "paid": True,
            "chargeable": False,
            "mock": True,
            "replay": False,
            "note": NON_CHARGEABLE_NOTE,
        }
        self.receipts[order_id] = receipt
        return dict(receipt)

    def grant_month_card(self, actor, days=30):
        actor = str(actor or "").strip()
        if not actor:
            raise PayMockError(E_PAYMOCK_BAD_ACTOR, "actor required")
        entitlement = {
            "entitlement_id": "sbx-card-" + uuid.uuid4().hex,
            "actor": actor,
            "plan": PRODUCT_MONTH_CARD,
            "days": int(days),
            "active": True,
            "chargeable": False,
            "mock": True,
            "note": NON_CHARGEABLE_NOTE,
        }
        self.entitlements[actor] = entitlement
        return dict(entitlement)

    # -- read face --------------------------------------------------

    def entitlement_of(self, actor):
        ent = self.entitlements.get(str(actor or "").strip())
        return dict(ent) if ent else None


def refuse_real_charge(*_args, **_kwargs):
    """Any caller that tries to move real money through this module is refused."""
    raise PayMockError(E_PAYMOCK_STUB_ONLY, NON_CHARGEABLE_NOTE)


def contract():
    return {
        "product_entrance": PRODUCT_ENTRANCE,
        "product_month_card": PRODUCT_MONTH_CARD,
        "amount_cents": PRICE_CENTS,
        "currency": CURRENCY,
        "flow": ["create_order", "pay", "receipt", "grant_month_card"],
        "always": {"mock": True, "chargeable": False},
        "refusal_codes": [
            E_PAYMOCK_BAD_ACTOR,
            E_PAYMOCK_BAD_AMOUNT,
            E_PAYMOCK_UNKNOWN_ORDER,
            E_PAYMOCK_STUB_ONLY,
        ],
        "blocked_on": "CEO physical item: WeChat merchant id",
    }


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="19.9 sandbox payment mock (never chargeable)")
    parser.add_argument("--actor", default="sandbox-visitor-1")
    parser.add_argument("--month-card", action="store_true", help="also grant a mock month card")
    parser.add_argument("--contract", action="store_true")
    args = parser.parse_args()

    if args.contract:
        print(json.dumps(contract(), ensure_ascii=False, indent=2))
        return 0
    mock = PayMock()
    order = mock.create_order(args.actor)
    receipt = mock.pay(order["order_id"])
    out = {"order": order, "receipt": receipt}
    if args.month_card:
        out["entitlement"] = mock.grant_month_card(args.actor)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())