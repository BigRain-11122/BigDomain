# repair_R3183_fold_summary.py - one live line, repaired into the shipped shape
# Criteria AC-SUM1..5 were pre-registered in src/os/backlog.md (R3183 PIN)
# BEFORE this file existed - honesty law.
#
# Why: fold 608 left a prose summary that names no archive file, so the
# sequence reader (which reads a fold summary as "head 'R<n> fold' AND the
# item names the archive file") refused it and counted it as a ROUND. The
# live sequence then read BACKWARDS (R3170 after R3181) and REPEAT R3181
# count=2 while fold_summaries read 0. The reader is right - loosening it
# would let any narrative that starts with "R<n> fold" leave the sequence
# silently - so this repairs the line and state_fold_run refuses such a
# summary before writing it again.
#
# Read-only unless --execute. Writes through state_io.write_document, the
# canonical closeout door. Stdlib only, ASCII source, zero network.

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402
import state_seq as SQ  # noqa: E402

PROSE_HEAD = "2026-11-21 R3181 fold 608:"
TOKEN_HEAD = "Tokens they alone carried:"
SHIPPED_HEAD = ("R3181 fold 608 of log lines 1..6 into"
                " logs/state-log-archive-2026-11.md")
ALREADY_HEAD = "R3181 fold 608 of log lines 1..6 into"


def state_path(root):
    return os.path.join(root, "src", "os", "state.json")


def carried_tokens(text):
    """The tokens the prose line names, read from its own labelled tail.

    The prose line states its tokens after "Tokens they alone carried:" as a
    comma-separated run; reading that tail keeps this repair from inventing a
    second token law for a single line.
    """
    if TOKEN_HEAD not in text:
        return []
    tail = text.split(TOKEN_HEAD, 1)[1].replace("\n", " ")
    out = []
    for piece in tail.split(","):
        token = piece.strip().rstrip(".")
        if token:
            out.append(token)
    return out


def repair_line(old):
    """Old prose line -> shipped shape carrying the same tokens verbatim."""
    markers = sorted(set(carried_tokens(old)))
    return (SHIPPED_HEAD
            + "; the six oldest live items left the carrier verbatim"
              " (window 1:6); payload unchanged"
            + "; tokens carried: " + " ".join(markers))


def plan(root):
    path = state_path(root)
    raw = SIO.read_raw(path)
    state = SIO.parse(SIO.decode(raw))
    log = state["log"]
    hits = [i for i, item in enumerate(log) if item.startswith(PROSE_HEAD)]
    if len(hits) > 1:
        return {"code": 3, "msg": "E_R3183FS_MULTI hits=%s" % (hits,)}
    if not hits:
        done = [i for i, item in enumerate(log)
                if item.startswith(ALREADY_HEAD)]
        if done:
            return {"code": 0, "mode": "ALREADY", "index": done[0],
                    "msg": "ALREADY-REPAIRED line=%d wrote=0"
                           % (done[0] + 1)}
        return {"code": 3, "msg": "E_R3183FS_NOT_FOUND"}
    index = hits[0]
    old = log[index]
    new = repair_line(old)
    if not SQ.is_fold_summary(new):
        return {"code": 5, "msg": "E_R3183FS_SHAPE new line not recognised"}
    markers = carried_tokens(old)
    if not markers:
        return {"code": 5, "msg": "E_R3183FS_TOKENS old line names none"}
    words = set(new.split())
    lost = [token for token in markers if token not in words]
    if lost:
        return {"code": 5, "msg": "E_R3183FS_TOKENS lost=%s" % lost}
    if len(new.encode("utf-8")) > len(old.encode("utf-8")):
        return {"code": 5, "msg": "E_R3183FS_LONGER new line is longer"}
    candidate = dict(state)
    candidate["log"] = list(log)
    candidate["log"][index] = new
    text = SIO.dump_canon(candidate)
    before = len(raw)
    after = len(text.encode("utf-8"))
    return {"code": 0, "mode": "REPAIR", "index": index,
            "before": before, "after": after, "state": candidate,
            "msg": "REPAIR line=%d bytes %d -> %d delta=%+d tokens=%d"
                   % (index + 1, before, after, after - before, len(markers))}


def main(argv):
    root = os.path.dirname(os.path.dirname(BASE))
    execute = "--execute" in argv
    report = plan(root)
    sys.stdout.write(report["msg"] + "\n")
    if report["code"] != 0:
        return report["code"]
    if report["mode"] == "ALREADY" or not execute:
        return 0
    path = state_path(root)
    written = SIO.write_document(path, report["state"])
    back = SIO.parse(io.open(path, encoding="utf-8").read())
    reading = SQ.audit(root)
    ok = (SQ.is_fold_summary(back["log"][report["index"]])
          and reading["fold_summaries"] == 1
          and not reading["repeats"]
          and not reading["backwards"])
    sys.stdout.write("READBACK wrote=%d fold_summaries=%d repeats=%d"
                     " backwards=%d verdict=%s ok=%s\n"
                     % (written["written"], reading["fold_summaries"],
                        len(reading["repeats"]), len(reading["backwards"]),
                        reading["verdict"], ok))
    return 0 if ok else 5


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
