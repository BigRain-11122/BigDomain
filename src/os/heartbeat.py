"""The one birth site for the repo-root heartbeat row (criterion AC-HB1).

WHY THIS MODULE EXISTS (measured at R3110, not assumed):
43 shipped .py files under src/ name `heartbeat.txt`, 41 of them perform
write-shaped calls, and 39 carry no tick guard at all - the file's format was
only ever agreed on by its single reader. Sending history agrees: of the last
60 shipped versions of `heartbeat.txt`, 20 were a clean `tick <n>` line, 19
were a bare number and 21 were something else, and the only reader's rule
(`scan_five_still.ps1`: `tick (\\d+)` on the last non-blank of the last five
lines) would FLAG 40 of those 60. The recurring [HB] FLAG is not bad luck; it
is what an unguarded write face produces.

WHAT THIS MODULE OWNS:
  read_tick(root)          the reader rule, transcribed once from the shipped
                           PS1 face (last non-blank of the last TAIL_LINES
                           lines must match `tick (\\d+)`, else None).
  write_tick(root, tick)   refuses a non-int, a bool, a float and a negative
                           BEFORE touching the file (E_HB_TICK), then lands
                           exactly one `tick <n>\\n` line in UTF-8/LF through a
                           same-directory temp file plus os.replace.
  verify(root, state_tick) derives PASS/FLAG and the lag from the two live
                           readings, so a green line cannot be typed by hand.

This module does NOT rewrite the 43 historical one-off closeout scripts: they
are shipped evidence, not a live writer set. The guard is born here and this
round's own heartbeat write goes through it.
"""
import os
import re
import sys

TICK_RE = re.compile(r"tick (\d+)")
TICK_LINE = "tick %d\n"
TAIL_LINES = 5
E_HB_TICK = "E_HB_TICK"
E_HB_NO_STATE = "E_HB_NO_STATE"

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def path_for(root):
    return os.path.join(root, "heartbeat.txt")


def read_tick(root):
    """The shipped reader rule. None = missing, unreadable or unparsed."""
    target = path_for(root)
    try:
        with open(target, "rb") as handle:
            blob = handle.read()
    except OSError:
        return None
    text = blob.decode("utf-8", "replace").replace("\r\n", "\n")
    lines = [line for line in text.split("\n")[-TAIL_LINES:] if line.strip()]
    if not lines:
        return None
    hit = TICK_RE.search(lines[-1])
    return int(hit.group(1)) if hit else None


def write_tick(root, tick):
    """Land one `tick <n>` line. Refuses bad input before any write."""
    if isinstance(tick, bool) or not isinstance(tick, int) or tick < 0:
        raise ValueError("%s refused tick=%r" % (E_HB_TICK, tick))
    payload = (TICK_LINE % tick).encode("ascii")
    target = path_for(root)
    folder = os.path.dirname(target) or "."
    temp = os.path.join(folder, ".heartbeat.tmp-%d" % os.getpid())
    try:
        with open(temp, "wb") as handle:
            handle.write(payload)
        os.replace(temp, target)
    finally:
        if os.path.exists(temp):
            os.remove(temp)
    return len(payload)


def verify(root, state_tick=None):
    """Derive the verdict from two live readings, never from a typed string."""
    hb = read_tick(root)
    if hb is None:
        return {"status": "FLAG", "tick": None, "state": state_tick,
                "lag": None, "reason": "heartbeat_missing_or_unparsed"}
    if state_tick is None:
        return {"status": "PASS", "tick": hb, "state": None, "lag": None,
                "reason": "state_not_asked"}
    lag = int(state_tick) - hb
    if lag > 0:
        return {"status": "FLAG", "tick": hb, "state": int(state_tick),
                "lag": lag, "reason": "heartbeat_row_debt"}
    return {"status": "PASS", "tick": hb, "state": int(state_tick),
            "lag": lag, "reason": "fresh"}


def _state_tick(root):
    import json
    target = os.path.join(root, "src", "os", "state.json")
    try:
        with open(target, encoding="utf-8") as handle:
            return int(json.load(handle).get("tick"))
    except (OSError, ValueError, TypeError):
        return None


def _line(verdict, root):
    def show(value):
        return "none" if value is None else str(value)
    return ("HEARTBEAT %s tick=%s state=%s lag=%s reason=%s path=%s"
            % (verdict["status"], show(verdict["tick"]), show(verdict["state"]),
               show(verdict["lag"]), verdict["reason"],
               os.path.relpath(path_for(root), root).replace("\\", "/")))


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    root = ROOT
    if "--root" in args:
        at = args.index("--root")
        root = args[at + 1]
        del args[at:at + 2]
    if args and args[0] == "--write":
        try:
            tick = int(args[1])
        except (IndexError, ValueError):
            print("%s refused tick=%r" % (E_HB_TICK, args[1:]))
            return 2
        try:
            size = write_tick(root, tick)
        except ValueError as exc:
            print(str(exc))
            return 2
        print("HEARTBEAT-WRITE tick=%d bytes=%d path=%s"
              % (tick, size,
                 os.path.relpath(path_for(root), root).replace("\\", "/")))
        return 0
    state = _state_tick(root)
    verdict = verify(root, state if state is not None else None)
    print(_line(verdict, root))
    return 0 if verdict["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
