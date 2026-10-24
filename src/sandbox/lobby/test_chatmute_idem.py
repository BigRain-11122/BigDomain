"""Acceptance suite: lobby chat mute / idempotency boundary family
(BigDomain R2070, explore-queue FIFO head claim; seed = R2042
idem_expired_rebilling_cases in test_client.py).

Pins AC-CMI1..AC-CMI8 (pre-registered in state/queue/explore.md
before this suite existed).

Finding under pin (read from src/sandbox/lobby/server.py, then
proved through the real product path): in handle_chat the identity,
room, empty-text and content gates run first, then the idempotency
gate, then the rate/mute gate. Consequences this suite nails:

  (a) inside a mute window an in-TTL (client_msg_id, text) replay
      still answers chat.duplicate and never E_RATE_LIMIT - the
      replay is immune, costs no window budget and no violation;
  (b) an EXPIRED replay falls through the idem gate into the mute
      gate and is refused, i.e. mute + expired rebill compose into
      the refusal path (the mute counter is only advanced by the
      rate gate, never by idem hits);
  (c) the idem cache is lobby-scoped, not connection-scoped: a
      second connection can seed a key that a muted connection
      replays to a duplicate answer.

Clock discipline: server.time is replaced by a deterministic fake
clock (that module binding only, restored on exit), so the rate
window, the mute window and the idem TTL all move without sleeps
or real-clock reads. The shipped config is read from disk, deep
copied in memory, and only the idem TTL is compressed to 5s (data
only) so an expired replay can be produced inside one saturated
10s rate window. Zero product code is touched.

Usage: python test_chatmute_idem.py
"""

import asyncio
import hashlib
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import sec_gate as G                                   # noqa: E402
import server as SRV                                   # noqa: E402
import store as S                                      # noqa: E402

DEFAULT_TTL = 5.0
PRODUCT_FILES = ("server.py", "store.py", "sec_gate.py", "config.json")


class FakeTime(object):
    """Deterministic monotonic + wall clock pair."""

    def __init__(self):
        self.mono = 0.0
        self.wall = 1700000000.0

    def monotonic(self):
        return self.mono

    def time(self):
        return self.wall

    def advance(self, dt):
        self.mono += dt
        self.wall += dt


class FakeWS(object):
    """Frame sink standing in for a websocket connection."""

    def __init__(self):
        self.frames = []

    async def send(self, data):
        self.frames.append(json.loads(data))


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def load_cfg():
    path = os.path.join(BASE, "config.json")
    with open(path, encoding="utf-8") as handle:
        cfg = json.load(handle)
    cfg = json.loads(json.dumps(cfg))          # deep copy, memory only
    cfg["idempotency"]["ttl_seconds"] = DEFAULT_TTL
    return cfg


def build(db_path):
    cfg = load_cfg()
    gate = G.SecGate.from_config(cfg)
    st = S.EventStore(db_path, disclaimer=str(cfg["risk_warning"]["text"]))
    lobby = SRV.Lobby(cfg, gate, st)
    return cfg, gate, st, lobby


def new_client(lobby, cfg):
    ws = FakeWS()
    client = SRV.Client(ws, cfg["rooms"])
    lobby.clients.add(client)        # same registration as handle_connection
    client.make_resident()
    return ws, client


async def chat(lobby, client, text, cid=None, room="lobby"):
    msg = {"type": "chat.send", "room": room, "payload": {"text": text}}
    if cid is not None:
        msg["client_msg_id"] = cid
    await lobby.handle_chat(client, msg)
    return client.ws.frames[-1]


def payload_of(frame):
    return frame.get("payload") or {}


async def timeline(db_path):
    """Drive the whole battery on the real product path and record it."""
    cfg, gate, st, lobby = build(db_path)
    ev = {"cfg": cfg, "gate": gate, "store": st, "lobby": lobby}

    def rows():
        return st.count("WHERE type = ?", ("chat.broadcast",))

    # --- t=0: five accepted sends saturate the 5/10s window ---
    ws1, c1 = new_client(lobby, cfg)
    first = []
    for i in range(5):
        frame = await chat(lobby, c1, "harbor note %d" % i, "cid-%d" % i)
        first.append(frame)
    ev["c1"] = c1
    ev["ws1"] = ws1
    ev["first_frames"] = first
    ev["rows_after_fill"] = rows()
    ev["budget_after_fill"] = len(c1.send_times)

    # --- AC-CMI1: in-TTL replay on the saturated window ---
    SRV.time.advance(1.0)
    before = (rows(), len(c1.send_times), c1.violations, len(lobby.idem_seen))
    replay = await chat(lobby, c1, "harbor note 0", "cid-0")
    ev["replay_frame"] = replay
    ev["replay_original_evt"] = first[0].get("evt_id")
    ev["replay_after"] = (rows(), len(c1.send_times), c1.violations,
                          len(lobby.idem_seen))
    ev["replay_before"] = before

    # --- AC-CMI2: three expired rebills on the same saturated window ---
    SRV.time.advance(DEFAULT_TTL)              # t=6: TTL gone, window held
    r1 = await chat(lobby, c1, "harbor note 0", "cid-0")
    v1 = c1.violations
    r2 = await chat(lobby, c1, "harbor note 1", "cid-1")
    v2 = c1.violations
    r3 = await chat(lobby, c1, "harbor note 2", "cid-2")
    ev["rebill_frames"] = (r1, r2, r3)
    ev["rebill_violations"] = (v1, v2, c1.violations)
    ev["muted_until"] = c1.muted_until
    ev["muted_until_wall"] = c1.muted_until_wall
    ev["mute_seconds"] = lobby.mute_s
    ev["rows_after_mute"] = rows()

    # --- AC-CMI3: a fresh send inside the mute window ---
    SRV.time.advance(1.0)                      # t=7
    idem_before = len(lobby.idem_seen)
    fresh = await chat(lobby, c1, "fresh line", "cid-9")
    ev["fresh_frame"] = fresh
    ev["fresh_violations"] = c1.violations
    ev["fresh_rows"] = rows()
    ev["fresh_idem_delta"] = len(lobby.idem_seen) - idem_before
    ev["fresh_budget"] = len(c1.send_times)

    # --- AC-CMI4: in-TTL replay inside the mute window, key seeded by a
    # second connection (the cache is lobby-scoped, not per connection) ---
    ws2, c2 = new_client(lobby, cfg)
    seed = await chat(lobby, c2, "second voice", "sid-1")
    ev["seed_frame"] = seed
    ev["rows_after_seed"] = rows()
    muted_before = c1.muted_until
    idem_before = len(lobby.idem_seen)
    SRV.time.advance(0.5)                      # t=7.5, still muted
    crossed = await chat(lobby, c1, "second voice", "sid-1")
    ev["cross_frame"] = crossed
    ev["cross_muted_stable"] = (c1.muted_until == muted_before)
    ev["cross_violations"] = c1.violations
    ev["cross_rows"] = rows()
    ev["cross_idem_delta"] = len(lobby.idem_seen) - idem_before
    ev["cross_budget"] = len(c1.send_times)

    # --- AC-CMI5: mute expiry resumes the connection ---
    SRV.time.advance(lobby.mute_s)             # t=67 > 66
    back = await chat(lobby, c1, "back online", "cid-10")
    ev["resume_frame"] = back
    ev["resume_rows"] = rows()
    ev["resume_violations"] = c1.violations
    ev["resume_budget"] = len(c1.send_times)

    # --- AC-CMI6: the whole ledger of accepted sends ---
    ev["total_rows"] = st.count()
    ev["chat_rows"] = rows()
    ev["evt_ids"] = [f.get("evt_id") for f in
                     (first + [seed, back])]
    return ev


async def orthogonal_probes(tmp):
    """AC-CMI7: the non-rate gates never touch the mute counters."""
    db_path = os.path.join(tmp, "ortho.db")
    cfg, gate, st, lobby = build(db_path)
    ws, resident = new_client(lobby, cfg)
    ws_s, spectator = new_client(lobby, cfg)
    spectator.resident = False
    out = {}
    out["not_resident"] = await chat(lobby, spectator, "hello", "x-1")
    out["bad_room"] = await chat(lobby, resident, "hello", "x-2",
                                 room="penthouse")
    out["empty"] = await chat(lobby, resident, "   ", "x-3")
    forbidden = str(gate.forbidden_words[0])
    advisory = str(gate.advisory_ban_words[0])
    out["gate1"] = await chat(lobby, resident, "word " + forbidden, "x-4")
    out["gate2"] = await chat(lobby, resident, "word " + advisory, "x-5")
    out["resident_violations"] = resident.violations
    out["resident_budget"] = len(resident.send_times)
    out["spectator_violations"] = spectator.violations
    out["spectator_budget"] = len(spectator.send_times)
    out["rows"] = st.count()
    out["idem"] = len(lobby.idem_seen)
    return out


def ac_cmi1(ev):
    assert ev["rows_after_fill"] == 5, "five accepted sends must land"
    assert ev["budget_after_fill"] == 5, "window must be saturated"
    frame = ev["replay_frame"]
    assert frame.get("type") == "chat.duplicate", frame.get("type")
    assert payload_of(frame).get("evt_id") == ev["replay_original_evt"], \
        "replay must re-ack the original evt_id"
    assert ev["replay_after"] == ev["replay_before"], \
        "replay must not move rows/budget/violations/idem: %r vs %r" % (
            ev["replay_after"], ev["replay_before"])


def ac_cmi2(ev):
    r1, r2, r3 = ev["rebill_frames"]
    assert r1.get("type") == "err.rate_limit", r1.get("type")
    assert r2.get("type") == "err.rate_limit", r2.get("type")
    assert r3.get("type") == "sec.reject", r3.get("type")
    assert payload_of(r3).get("code") == "E_RATE_LIMIT", payload_of(r3)
    assert "muted for" in str(payload_of(r3).get("reason")), payload_of(r3)
    v1, v2, v3 = ev["rebill_violations"]
    assert (v1, v2) == (1, 2), (v1, v2)
    assert v3 == 0, "mute trigger resets the counter: %r" % (v3,)
    assert ev["muted_until"] == (6.0 + ev["mute_seconds"]), ev["muted_until"]
    assert ev["rows_after_mute"] == 5, "refusals must not land rows"


def ac_cmi3(ev):
    frame = ev["fresh_frame"]
    assert frame.get("type") == "sec.reject", frame.get("type")
    payload = payload_of(frame)
    assert payload.get("code") == "E_RATE_LIMIT", payload
    assert "temporarily muted" in str(payload.get("reason")), payload
    assert payload.get("muted_until") == ev["muted_until_wall"], payload
    assert ev["fresh_violations"] == 0, ev["fresh_violations"]
    assert ev["fresh_rows"] == 5, ev["fresh_rows"]
    assert ev["fresh_idem_delta"] == 0, ev["fresh_idem_delta"]
    assert ev["fresh_budget"] == 5, ev["fresh_budget"]


def ac_cmi4(ev):
    seed = ev["seed_frame"]
    assert seed.get("type") == "chat.broadcast", seed.get("type")
    assert seed.get("evt_id"), "a seeded key needs its evt_id"
    crossed = ev["cross_frame"]
    assert crossed.get("type") == "chat.duplicate", crossed.get("type")
    assert payload_of(crossed).get("evt_id") == seed.get("evt_id"), \
        "the muted replay must re-ack the seeded evt_id"
    assert ev["cross_muted_stable"] is True
    assert ev["cross_violations"] == 0, ev["cross_violations"]
    assert ev["cross_rows"] == 6, ev["cross_rows"]
    assert ev["cross_idem_delta"] == 0, ev["cross_idem_delta"]
    assert ev["cross_budget"] == 5, ev["cross_budget"]


def ac_cmi5(ev):
    frame = ev["resume_frame"]
    assert frame.get("type") == "chat.broadcast", frame.get("type")
    assert ev["resume_rows"] == 7, ev["resume_rows"]
    assert ev["resume_violations"] == 0, ev["resume_violations"]
    assert ev["resume_budget"] == 1, ev["resume_budget"]


def ac_cmi6(ev):
    assert ev["chat_rows"] == 7, ev["chat_rows"]
    assert ev["total_rows"] == 7, "rejected paths must leave zero rows"
    assert len(set(ev["evt_ids"])) == 7, "evt_ids must be distinct"


def ac_cmi7(out):
    pairs = [
        ("not_resident", "E_ENTRANCE_REQUIRED"),
        ("bad_room", "E_ROOM_UNKNOWN"),
        ("empty", "E_BAD_FRAME"),
        ("gate1", "E_CONTENT_REJECTED"),
        ("gate2", "E_CONTENT_REJECTED"),
    ]
    for key, code in pairs:
        frame = out[key]
        assert frame.get("type") == "sec.reject", (key, frame.get("type"))
        assert payload_of(frame).get("code") == code, (key, payload_of(frame))
    assert out["resident_violations"] == 0, out["resident_violations"]
    assert out["resident_budget"] == 0, out["resident_budget"]
    assert out["spectator_violations"] == 0, out["spectator_violations"]
    assert out["spectator_budget"] == 0, out["spectator_budget"]
    assert out["rows"] == 0, out["rows"]
    assert out["idem"] == 0, out["idem"]


def main():
    tmp = tempfile.mkdtemp(prefix="lobby-chatmute-idem-")
    product_before = dict((n, digest(os.path.join(BASE, n)))
                          for n in PRODUCT_FILES)
    fake = FakeTime()
    real_time = SRV.time
    SRV.time = fake
    failed = 0
    try:
        db_path = os.path.join(tmp, "chatmute.db")
        loop = asyncio.new_event_loop()
        try:
            ev = loop.run_until_complete(timeline(db_path))
            ortho = loop.run_until_complete(orthogonal_probes(tmp))
        finally:
            loop.close()
        cases = [
            ("AC-CMI1 idem-before-rate ordering", ac_cmi1, ev),
            ("AC-CMI2 expired rebill triple mutes", ac_cmi2, ev),
            ("AC-CMI3 fresh send inside mute", ac_cmi3, ev),
            ("AC-CMI4 in-TTL replay immunity while muted", ac_cmi4, ev),
            ("AC-CMI5 mute expiry resumes", ac_cmi5, ev),
            ("AC-CMI6 refusals leave no ledger rows", ac_cmi6, ev),
            ("AC-CMI7 orthogonal gates keep counters", ac_cmi7, ortho),
        ]
        for name, fn, arg in cases:
            try:
                fn(arg)
                print("PASS %s" % name)
            except AssertionError as exc:
                failed += 1
                print("FAIL %s :: %s" % (name, exc))
        # AC-CMI8 hygiene
        try:
            with open(os.path.abspath(__file__), "rb") as handle:
                raw = handle.read()
            assert max(raw) < 128, "suite source must stay ASCII"
            text = raw.decode("ascii")
            # Import-line scan, not a substring scan: the detector's own
            # literals must not self-match (R1678 lesson).
            banned_mods = ("socket", "urllib", "requests", "http",
                           "ssl", "asyncio.streams")
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("import "):
                    mod = stripped[len("import "):].split()[0].split(".")[0]
                    assert mod not in banned_mods, "network import: " + mod
                elif stripped.startswith("from "):
                    mod = stripped[len("from "):].split()[0].split(".")[0]
                    assert mod not in banned_mods, "network import: " + mod
            product_after = dict((n, digest(os.path.join(BASE, n)))
                                 for n in PRODUCT_FILES)
            assert product_after == product_before, \
                "shipped product files changed during the run"
            assert os.path.abspath(tmp).startswith(
                os.path.abspath(tempfile.gettempdir())), "fixture outside temp"
            print("PASS AC-CMI8 hygiene")
        except AssertionError as exc:
            failed += 1
            print("FAIL AC-CMI8 :: %s" % exc)
    finally:
        SRV.time = real_time
        shutil.rmtree(tmp, ignore_errors=True)
    total = 8
    print("SUITE %s %d/%d" % ("PASS" if not failed else "FAIL",
                              total - failed, total))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())