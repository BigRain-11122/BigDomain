"""R2119 preview artifacts: a deterministic world with buyers, sellers
and pre-purchase questions, rendered to preview HTML + versioned JSON.
Pure ASCII, stdlib, temp db outside the repo tree."""

import hashlib
import io
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
BASE = os.path.join(ROOT, "src", "sandbox", "ledger")
LOBBY = os.path.join(ROOT, "src", "sandbox", "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402
import metered as M                   # noqa: E402
import apidev as D                    # noqa: E402
import apimarket as A                 # noqa: E402
import apimarket_report as R          # noqa: E402
from sec_gate import SecGate          # noqa: E402

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")
PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}


def main():
    tmp = tempfile.mkdtemp(prefix="amqbq-preview-")
    db_path = os.path.join(tmp, "preview.db")
    with open(os.path.join(BASE, "config.json"), "rb") as fh:
        cfg = json.loads(fh.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as fh:
        lobby_cfg = json.loads(fh.read().decode("utf-8"))
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    gate = SecGate.from_config(lobby_cfg)
    am = A.APIMarketFace(led, dk, gate, DISCLAIMER)

    stamps = iter(
        ["2026-10-25T08:00:00Z", "2026-10-25T08:10:00Z",
         "2026-10-25T08:20:00Z", "2026-10-25T09:00:00Z",
         "2026-10-25T09:10:00Z", "2026-10-25T09:20:00Z",
         "2026-10-25T09:30:00Z", "2026-10-25T09:40:00Z",
         "2026-10-25T10:00:00Z"] * 8)
    origin = A._now_utc

    def stamp():
        try:
            return next(stamps)
        except StopIteration:
            return "2026-10-25T11:00:00Z"

    A._now_utc = stamp
    try:
        led.mint_to_pool("pool:reserve", 20000, "PREV-A", "settlement")
        led.mint_to_pool("pool:share", 20000, "PREV-S", "settlement")
        for who in ("bob", "carol"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
            led.adjust([("pool:reserve", "debit", 600),
                        ("usr:" + who, "credit", 600)],
                       "manual:fund-" + who, "preview funding " + who)
        dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
        ids = {}
        for key, title, price in (("alpha", "Service Alpha", 10),
                                  ("beta", "Service Beta", 8),
                                  ("gamma", "Service Gamma", 6)):
            ids[key] = am.publish_api("usr:dana", key, title,
                                      "service payload " + key, PAYLOAD,
                                      price, False)["listing_id"]
        am.purchase_api("usr:bob", ids["alpha"], "preview-sale-1")
        q1 = am.ask_question("usr:bob", ids["alpha"],
                             "does this support batch calls?")
        am.ask_question("usr:carol", ids["alpha"],
                        "is there a sample response?")
        am.ask_question("usr:bob", ids["beta"],
                        "what is the rate limit?")
        am.answer_question("usr:dana", q1["question_id"],
                           "yes, up to 500 calls per batch")
        am.ask_question("usr:carol", ids["gamma"],
                        "does this include history?")
        am.delist_api("usr:dana", ids["gamma"])
        report = R.collect(am)
        html = R.render_html(report)
        html_path = os.path.join(ROOT, "preview",
                                 "apimarket-report-buyerquestions.html")
        json_path = os.path.join(ROOT, "preview",
                                 "apimarket-report-buyerquestions.json")
        with io.open(html_path, "w", encoding="utf-8",
                     newline="\n") as fh:
            fh.write(html)
        R.write_report_json(json_path, report)
        for path in (html_path, json_path):
            with open(path, "rb") as fh:
                blob = fh.read()
            print("%s bytes=%d sha256=%s"
                  % (os.path.basename(path), len(blob),
                     hashlib.sha256(blob).hexdigest()[:16]))
        bob = report["buyers"].get("usr:bob")
        print("schema=%d buyer_questions=%r my_questions_in_html=%r"
              % (R.REPORT_SCHEMA,
                 bob["questions"]["question_count"] if bob else None,
                 "my questions" in html))
    finally:
        A._now_utc = origin
        am.close()
        dk.close()
        metered.close()
        led.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())