"""Clickable membership face: the entitlement side of the 19.9 entrance (P-47-5).

The member sandbox has shipped an entitlement engine (member.py), a catalog
(catalog.py), a sweep, a reconcile and a reminder - all reachable only by a
terminal. A person who pays the 19.9 month card at the checkout face has no
page that shows what they now hold: tier, remaining credits, birth-cert
marker, what expires within N days. This module serves that page.

Routes (one self-contained page, same-origin JSON only):

    GET  /member, /member/        the page on disk, byte for byte
    GET  /member/api/state        entitlement for ?avatar=<name>[&days=N]
    GET  /member/api/avatars      the avatars this sandbox holds a grant for
    POST /member/api/join         sandbox month card: order -> pay -> activate

Laws carried, never re-implemented here:

  - the money face is the shipped pay dock; this module books nothing. The
    dock is wired with sandbox-only price rows (mock, never chargeable) and
    every response carries mock=true / chargeable=false;
  - entitlement reads are the shipped MemberStore read faces:
    privileges_for / balance_face / birth_cert_face / expiring_soon;
  - the resident non-advisory disclaimer and the AIGC label text come from
    the member config, never from a literal in this file;
  - zero network egress: the page is read from disk and every fetch target
    in it is a same-origin /member/... path.

The data directory defaults to a temp sandbox instance, so a demo run never
touches the shipped config.json or any live database.

Stdlib only. Source is pure ASCII; the page is the only non-ASCII file.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
_SANDBOX = os.path.normpath(os.path.join(HERE, ".."))
_LOBBY = os.path.join(_SANDBOX, "lobby")
_PAY = os.path.join(_SANDBOX, "pay")
_LEDGER = os.path.join(_SANDBOX, "ledger")
# BASE first, then the sibling faces: member modules win over same-named
# pay modules, exactly as the shipped member suite resolves them.
for _p in (HERE, _LEDGER, _PAY, _LOBBY):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import adapters as AD          # noqa: E402  (pay channel adapters)
import catalog as CAT          # noqa: E402
import ledger as LED           # noqa: E402
import member as M             # noqa: E402
import orders as PAY           # noqa: E402  (pay dock)
import store as LOBBY_STORE    # noqa: E402  (lobby event store)

PAGE_NAME = "member.html"
MEMBER_CFG = os.path.join(HERE, "config.json")
PAY_CFG = os.path.join(_PAY, "config.json")
LEDGER_CFG = os.path.join(_LEDGER, "config.json")

MAX_BODY_BYTES = 8192
SANDBOX_TIER = "experience"          # the 19.9 entrance month card
SANDBOX_PRODUCT = "tier_experience"  # sandbox-only price row, never real

E_BAD_BODY = "E_BAD_BODY"
E_NO_AVATAR = "E_NO_AVATAR"
E_DOCK = "E_DOCK_UNAVAILABLE"


class FaceError(Exception):
    """A refusal this face owns, carrying its own HTTP status."""

    def __init__(self, code, status, detail=""):
        super().__init__(code + (": " + detail if detail else ""))
        self.code = code
        self.status = int(status)
        self.detail = detail


def _load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def build_world(data_dir):
    """Wire the shipped faces into one sandbox instance under data_dir.

    The pay dock is given sandbox-only price rows whose entitlement key is
    the member catalog product key, so a join grants a real member period
    while never recording real money.
    """
    os.makedirs(data_dir, exist_ok=True)
    mcfg = _load(MEMBER_CFG)
    pcfg = _load(PAY_CFG)
    pcfg.setdefault("products", {})
    pcfg["products"][SANDBOX_PRODUCT] = {
        "channel": "virtual",
        "price_cent": 1990,
        "share_tokens": 0,
        "entitlement": "tier:" + SANDBOX_TIER,
        "copy": "sandbox dock product: experience tier (never chargeable)",
    }
    events = LOBBY_STORE.EventStore(os.path.join(data_dir, "events.db"))
    led = LED.Ledger(os.path.join(data_dir, "ledger.db"), _load(LEDGER_CFG))
    led.mint_to_pool("pool:share", 1000000, "SETTLE-MEMBER-FACE-1",
                     "settlement")
    pay = PAY.PayOrders(pcfg, os.path.join(data_dir, "pay.db"), events, led)
    store = M.MemberStore(mcfg, os.path.join(data_dir, "member.db"), pay)
    return {
        "mcfg": mcfg,
        "pcfg": pcfg,
        "events": events,
        "led": led,
        "pay": pay,
        "chans": AD.from_config(pcfg),
        "store": store,
    }


def close_world(world):
    for key in ("store", "pay", "led", "events"):
        try:
            world[key].close()
        except Exception:  # noqa: BLE001 - teardown must not mask a result
            pass


def _catalog_public(cat):
    """The tier rows a person may join, read from the catalog (single
    source), reduced to what the page shows."""
    rows = []
    for key in sorted(cat.tiers.keys()):
        tier = cat.tiers[key]
        rows.append({
            "tier": key,
            "monthly_credits": int(tier.monthly_credits),
            "privileges": sorted(tier.privileges),
        })
    return rows


class MemberFace(object):
    """Read-mostly HTTP face over the shipped member engine."""

    def __init__(self, world, page_path, host):
        self.world = world
        self.page_path = page_path
        self.host = host
        self.mcfg = world["mcfg"]
        self._lock = threading.Lock()

    # ---- reads ----------------------------------------------------
    def state(self, avatar, days=30):
        avatar = str(avatar or "").strip()
        if not avatar:
            raise FaceError(E_NO_AVATAR, 400, "avatar is required")
        store = self.world["store"]
        with self._lock:
            privs = store.privileges_for(avatar)
            balance = store.balance_face(avatar)
            cert = store.birth_cert_face(avatar)
            expiring = store.expiring_soon(int(days), now=None)
        return {
            "avatar": avatar,
            "mock": True,
            "chargeable": False,
            "ai_label": self.world["store"].catalog.ai_label,
            "disclaimer": self.world["store"].catalog.disclaimer,
            "persistent": True,
            "privileges": privs,
            "balance": balance,
            "birth_cert": cert,
            "expiring_soon": expiring,
            "window_days": int(days),
            "catalog": _catalog_public(self.world["store"].catalog),
        }

    def avatars(self):
        store = self.world["store"]
        with self._lock:
            rows = store._conn.execute(
                "SELECT DISTINCT census_avatar_id FROM member_periods "
                "ORDER BY census_avatar_id").fetchall()
        names = sorted({r[0] for r in rows})
        return {
            "avatars": names,
            "count": len(names),
            "mock": True,
            "chargeable": False,
            "disclaimer": store.catalog.disclaimer,
        }

    # ---- the one write this face owns -----------------------------
    def join(self, avatar):
        avatar = str(avatar or "").strip()
        if not avatar:
            raise FaceError(E_NO_AVATAR, 400, "avatar is required")
        pay = self.world["pay"]
        with self._lock:
            resp = pay.create_order(SANDBOX_PRODUCT, avatar)
            order_id = resp["order_id"]
            pay.place_order(order_id)
            amount = pay.order_detail(order_id)["amount_cent"]
            cb = self.world["chans"][resp["channel"]].make_callback(
                order_id, amount, "member-face-" + order_id)
            pay.handle_callback(cb)
            items = pay.grants_for(avatar)["items"]
            grant_id = items[-1]["grant_id"]
            self.world["store"].activate(grant_id, avatar)
        out = self.state(avatar)
        out["joined"] = {"order_id": order_id, "grant_id": grant_id,
                         "amount_cent": amount, "mock": True}
        return out


class Handler(BaseHTTPRequestHandler):
    server_version = "BigDomainMemberFace/1.0"

    # quiet: the suite reads status codes, not stderr chatter
    def log_message(self, fmt, *args):
        pass

    def _send(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False,
                          sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _page(self):
        with open(self.server.face.page_path, "rb") as handle:
            body = handle.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _query(self):
        parsed = urllib.parse.urlparse(self.path)
        return parsed.path, urllib.parse.parse_qs(parsed.query)

    def do_GET(self):
        path, query = self._query()
        face = self.server.face
        try:
            if path in ("/member", "/member/"):
                self._page()
            elif path == "/member/api/state":
                avatar = (query.get("avatar") or [""])[0]
                raw_days = (query.get("days") or ["30"])[0]
                try:
                    days = int(raw_days)
                except ValueError:
                    raise FaceError(E_BAD_BODY, 400, "days must be an integer")
                if days < 0 or days > 3650:
                    raise FaceError(E_BAD_BODY, 400, "days out of range")
                self._send(200, face.state(avatar, days))
            elif path == "/member/api/avatars":
                self._send(200, face.avatars())
            else:
                self._send(404, {"error": "E_NOT_FOUND", "path": path})
        except FaceError as exc:
            self._send(exc.status, {"error": exc.code, "detail": exc.detail})
        except M.MemberError as exc:
            self._send(400, {"error": exc.code, "detail": exc.detail or ""})
        except Exception as exc:  # noqa: BLE001 - one face, one refusal
            self._send(500, {"error": E_DOCK, "detail": type(exc).__name__})

    def do_POST(self):
        path, _query = self._query()
        face = self.server.face
        if path != "/member/api/join":
            self._send(404, {"error": "E_NOT_FOUND", "path": path})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BODY_BYTES:
            self._send(400, {"error": E_BAD_BODY, "detail": "bad length"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._send(400, {"error": E_BAD_BODY, "detail": "not json"})
            return
        if not isinstance(payload, dict):
            self._send(400, {"error": E_BAD_BODY, "detail": "object expected"})
            return
        try:
            self._send(200, face.join(payload.get("avatar")))
        except FaceError as exc:
            self._send(exc.status, {"error": exc.code, "detail": exc.detail})
        except M.MemberError as exc:
            self._send(409, {"error": exc.code, "detail": exc.detail or ""})
        except PAY.PayError as exc:
            self._send(400, {"error": exc.code, "detail": exc.detail or ""})
        except Exception as exc:  # noqa: BLE001
            self._send(500, {"error": E_DOCK, "detail": type(exc).__name__})

    def do_PUT(self):
        self._send(405, {"error": "E_METHOD_NOT_ALLOWED"})

    def do_DELETE(self):
        self._send(405, {"error": "E_METHOD_NOT_ALLOWED"})


class FaceServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_server(host, port, data_dir, page_path=None):
    world = build_world(data_dir)
    page = page_path or os.path.join(HERE, PAGE_NAME)
    httpd = FaceServer((host, int(port)), Handler)
    httpd.face = MemberFace(world, page, host)
    return httpd


def main(argv=None):
    parser = argparse.ArgumentParser(description="BigDomain member face")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8096)
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--keep-data", action="store_true")
    args = parser.parse_args(argv)

    data_dir = args.data_dir
    temp_dir = None
    if not data_dir:
        temp_dir = tempfile.mkdtemp(prefix="bd-member-face-")
        data_dir = temp_dir
    httpd = make_server(args.host, args.port, data_dir)
    host, port = httpd.server_address[0], httpd.server_address[1]
    print("member face on http://%s:%d/member/ (data=%s)"
          % (host, port, data_dir), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        close_world(httpd.face.world)
        if temp_dir and not args.keep_data:
            shutil.rmtree(temp_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())