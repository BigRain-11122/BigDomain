"""Token double-entry ledger console for the sandbox (BigDomain P-47-2b).

The ledger already ships two business modules - ledger.py (AC-L1..AC-L11:
accounts, mint, reward, share, spend, adjust, balance, bill) and
reconcile.py (eight honesty checks over the database) - but until this
module nothing human could operate them: every proof was a command line
run. This module serves one self-contained page plus five same-origin JSON
routes:

    GET  /ledger, /ledger/          the page on disk, served byte for byte
    GET  /ledger/api/state          accounts + balances + reconcile verdict
    GET  /ledger/api/bill?account=  the shipped Ledger.bill for one account
    POST /ledger/api/mint           mint_to_pool   (authorized issue)
    POST /ledger/api/reward         grant_reward   (pool -> usr payout)
    POST /ledger/api/spend          spend          (usr -> reserve)

Laws carried from the shipped faces, never re-implemented here:

  - every write goes through ledger.Ledger itself, so the double-entry
    balance, the sign law, the daily cap, the content-gate reference and
    the schema triggers all still have exactly one owner;
  - the reconcile readout is reconcile.check_lines asked at call time, so
    this face cannot disagree with the script the house runs;
  - the AI markers stay server-side: grant_reward decides source_ai from
    the config (AC-L9), and this module never reads a client source_ai key;
  - zero network egress: the page is read from disk, every fetch target in
    it is a same-origin /ledger/... path, and the server makes no outbound
    call. No fiat field exists anywhere (BLUEPRINT 5.4).

Pre-registered criteria AC-LC1..AC-LC6 live in the R2469 backlog row and
were written before this code existed (honesty law).

Stdlib only. Source is pure ASCII; the page is the only non-ASCII file.
"""

import argparse
import io
import json
import os
import sqlite3
import sys
import threading
import urllib.parse
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import reconcile as reconcile_script  # noqa: E402  (shipped check law)
from ledger import Ledger, LedgerError  # noqa: E402  (shipped book law)

PAGE_NAME = "ledger.html"
DEFAULT_DB = os.path.join(HERE, "ledger.db")
DEFAULT_CONFIG = os.path.join(HERE, "config.json")
MAX_BODY_BYTES = 8192

E_BAD_BODY = "E_LC_BAD_BODY"
E_NO_DB = "E_LC_NO_DB"

POST_ROUTES = ("/ledger/api/mint", "/ledger/api/reward", "/ledger/api/spend")

# HTTP status per shipped refusal code, so a caller can be written once.
LEDGER_STATUS = {
    "E_BAD_ACCOUNT": 400,
    "E_BAD_AMOUNT": 400,
    "E_BAD_TYPE": 400,
    "E_BAD_ACTION": 400,
    "E_ADJUST_MEMO": 400,
    "E_NO_BINDING": 400,
    "E_GATE_REF": 403,
    "E_UNKNOWN_ACCOUNT": 404,
    "E_NEGATIVE_BALANCE": 409,
    "E_TX_IMBALANCE": 409,
    "E_TX_MIN_ENTRIES": 409,
    "E_TX_CLOSED": 409,
    "E_TX_IMMUTABLE": 409,
    "E_TX_DUPLICATE": 409,
    "E_REF_DUPLICATE": 409,
    "E_TOKEN_CAP": 409,
}


class ConsoleError(Exception):
    """A refusal this face owns, carrying its own HTTP status."""

    def __init__(self, code, status, detail=""):
        super().__init__(code + (": " + detail if detail else ""))
        self.code = code
        self.status = int(status)
        self.detail = detail


class LedgerConsole:
    """The whole book face, over the shipped ledger and the shipped checks."""

    def __init__(self, db_path, config_path=DEFAULT_CONFIG):
        self.db_path = db_path
        with open(config_path, "r", encoding="utf-8") as handle:
            self.config = json.load(handle)
        self.ledger = Ledger(db_path, self.config)
        for account_id in ("equity:auth", "pool:reserve", "pool:reward", "pool:share"):
            self.ledger.ensure_account(account_id)
        self.ledger.ensure_account("usr:demo", census_avatar_id="demo")

    def close(self):
        self.ledger.close()

    # -- read faces -------------------------------------------------

    def account_ids(self):
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute(
                "SELECT account_id FROM ledger_accounts ORDER BY account_id").fetchall()
        finally:
            conn.close()
        return [row[0] for row in rows]

    def accounts(self):
        """Every balance is the shipped Ledger.balance answer, asked now."""
        out = []
        for account_id in self.account_ids():
            payload = self.ledger.balance(account_id)
            out.append({"account_id": payload["account_id"],
                        "balance": int(payload["balance"])})
        return out

    def reconcile(self):
        """The eight-check verdict, computed by the shipped script itself."""
        conn = sqlite3.connect(self.db_path)
        buffer = io.StringIO()
        try:
            with redirect_stdout(buffer):
                failed = reconcile_script.check_lines(conn, self.config)
        finally:
            conn.close()
        lines = [line.strip() for line in buffer.getvalue().splitlines() if line.strip()]
        return {"verdict": "PASS" if failed == 0 else "FAIL",
                "failed": int(failed),
                "checks": lines}

    def state(self):
        return {"accounts": self.accounts(),
                "reconcile": self.reconcile(),
                "disclaimer": self.ledger.disclaimer_payload(),
                "channel": "sandbox-mock",
                "chargeable": False}

    def bill(self, account_id):
        account_id = str(account_id or "").strip()
        if not account_id:
            raise ConsoleError(E_BAD_BODY, 400, "account required")
        return self.ledger.bill(account_id)

    # -- write faces ------------------------------------------------

    def mint(self, pool_id, amount, ref):
        tx_id = self.ledger.mint_to_pool(str(pool_id or ""), amount, str(ref or ""))
        return {"tx_id": tx_id, "reconcile": self.reconcile()}

    def reward(self, account_id, action, ref):
        """A client-supplied source_ai is never read: the config decides."""
        tx_id = self.ledger.grant_reward(str(account_id or ""), str(action or ""),
                                         str(ref or ""))
        return {"tx_id": tx_id, "reconcile": self.reconcile()}

    def spend(self, account_id, amount, ref):
        tx_id = self.ledger.spend(str(account_id or ""), amount, str(ref or ""))
        return {"tx_id": tx_id, "reconcile": self.reconcile()}


class LedgerHandler(BaseHTTPRequestHandler):
    """Six routes, all same-origin; everything else 404 or 405."""

    console = None  # wired at startup
    page_path = os.path.join(HERE, PAGE_NAME)

    # -- plumbing ---------------------------------------------------

    def _send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_page(self):
        try:
            with open(self.page_path, "rb") as handle:
                body = handle.read()
        except OSError:
            self._send_json(503, {"error": "ledger page missing on disk"})
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = self.headers.get("Content-Length")
        if not length:
            return {}
        try:
            size = int(length)
        except (TypeError, ValueError):
            raise ConsoleError(E_BAD_BODY, 400, "bad content-length")
        if size < 0 or size > MAX_BODY_BYTES:
            raise ConsoleError(E_BAD_BODY, 400, "body too large")
        raw = self.rfile.read(size)
        if not raw:
            return {}
        try:
            obj = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ConsoleError(E_BAD_BODY, 400, "body must be json")
        if not isinstance(obj, dict):
            raise ConsoleError(E_BAD_BODY, 400, "body must be a json object")
        return obj

    def _dispatch(self, route):
        try:
            payload = self._read_body()
            if route == "/ledger/api/mint":
                out = self.console.mint(payload.get("pool_id"), payload.get("amount"),
                                        payload.get("ref"))
                self._send_json(201, out)
                return
            if route == "/ledger/api/reward":
                out = self.console.reward(payload.get("account_id"),
                                          payload.get("action"), payload.get("ref"))
                self._send_json(201, out)
                return
            if route == "/ledger/api/spend":
                out = self.console.spend(payload.get("account_id"),
                                         payload.get("amount"), payload.get("ref"))
                self._send_json(201, out)
                return
        except ConsoleError as exc:
            self._send_json(exc.status, {"error": exc.code, "detail": exc.detail})
            return
        except LedgerError as exc:
            self._send_json(LEDGER_STATUS.get(exc.code, 400),
                            {"error": exc.code, "detail": str(exc.detail)})
            return
        self._send_json(404, {"error": "not found: " + route})

    # -- verbs ------------------------------------------------------

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path in ("/ledger", "/ledger/"):
            self._send_page()
            return
        if path in POST_ROUTES:
            self._send_json(405, {"error": "method not allowed: use POST " + path})
            return
        if path == "/ledger/api/state":
            self._send_json(200, self.console.state())
            return
        if path == "/ledger/api/bill":
            query = urllib.parse.parse_qs(parsed.query or "")
            account = (query.get("account") or [""])[0]
            try:
                self._send_json(200, self.console.bill(account))
            except ConsoleError as exc:
                self._send_json(exc.status, {"error": exc.code, "detail": exc.detail})
            except LedgerError as exc:
                self._send_json(LEDGER_STATUS.get(exc.code, 400),
                                {"error": exc.code, "detail": str(exc.detail)})
            return
        self._send_json(404, {"error": "not found: " + path})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path in POST_ROUTES:
            self._dispatch(path)
            return
        if path in ("/ledger", "/ledger/", "/ledger/api/state", "/ledger/api/bill"):
            self._send_json(405, {"error": "method not allowed on " + path})
            return
        self._send_json(404, {"error": "not found: " + path})

    def _method_reject(self):
        self._send_json(405, {"error": "method not allowed on the ledger face"})

    def do_PUT(self):
        self._method_reject()

    def do_DELETE(self):
        self._method_reject()

    def do_PATCH(self):
        self._method_reject()

    def log_message(self, fmt, *args):
        pass


def start_server(host, port, console):
    """Start the console on its own thread; returns the server object.

    The real bound port is at server.server_address[1], so a caller can pass
    port 0 and read back what the OS assigned.
    """
    handler = type("BoundLedgerHandler", (LedgerHandler,), {"console": console})
    httpd = ThreadingHTTPServer((host, port), handler)
    threading.Thread(target=httpd.serve_forever, name="ledger-console",
                     daemon=True).start()
    return httpd


def build_console(db_path=DEFAULT_DB, config_path=DEFAULT_CONFIG):
    return LedgerConsole(db_path, config_path)


def main():
    parser = argparse.ArgumentParser(
        description="token double-entry ledger console (sandbox, no fiat, no real charge)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8097)
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    args = parser.parse_args()

    console = build_console(args.db, args.config)
    httpd = start_server(args.host, args.port, console)
    port = httpd.server_address[1]
    print("LEDGER CONSOLE on http://%s:%d/ledger/" % (args.host, port))
    print("channel=sandbox-mock chargeable=false reconcile=%s"
          % console.reconcile()["verdict"])
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())