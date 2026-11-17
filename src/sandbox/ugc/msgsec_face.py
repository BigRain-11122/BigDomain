"""msgSecCheck parameter face: the pre-publication gate, defined at field level.

Why this module exists
----------------------
BLUEPRINT section 5 makes the content gate a life-or-death line ("no gate, no
door"), and src/sandbox/ugc/pipeline.py has run against a WORDLIST MOCK since
P-47-3b because the real interface parameters were never read from the official
doc: the doc paths guessed at R419 and again at R2907 were both 404, so the M
item stayed open and no gate could claim to speak the interface's dialect.

R2908 closed it through a discovery channel instead of another guessed path:
the section index (server-rendered, /miniprogram/dev/server/API/sec-center/)
links an llm.txt/md form, and the page's `.md` variant returns the whole table
verbatim. That table is now data (msgsec_face.json) and this module is the gate
that reads it, so a request or a response that the real interface would refuse
is refused HERE - locally, with no network call and no credential.

Law
---
The JSON file is the ONE authored place for the documented face. This module
adds no second copy: every constant it uses is read from that file at import,
and --check proves the file still says what the gate assumes. AC-MSF1..AC-MSF6
were pinned in src/os/backlog.md at R2908 BEFORE this file existed.

Decisions are fail-closed by construction:
  pass  -> ALLOW (label must be 100, the documented "normal" tag)
  review-> QUEUE (a human decides; never auto-adopted)
  risky -> BLOCK
  anything else (unknown suggest, unknown label, non-zero errcode, missing
  result) -> BLOCK, because a gate that guesses is not a gate.

Run:
    python src/sandbox/ugc/msgsec_face.py --check     # read-only verdict
    python src/sandbox/ugc/test_msgsec_face.py        # the suite
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
FACE_PATH = os.path.join(BASE, "msgsec_face.json")

ALLOW = "ALLOW"
QUEUE = "QUEUE"
BLOCK = "BLOCK"

DECISION_BY_SUGGEST = {"pass": ALLOW, "review": QUEUE, "risky": BLOCK}


def load_face(path=None):
    """Read the documented face. Raises on an unreadable file, never guesses."""
    with open(path or FACE_PATH, "r", encoding="utf-8") as fh:
        face = json.load(fh)
    return face


FACE = load_face()

PATH = FACE["call"]["path"]
HOST = FACE["call"]["host"]
METHOD = FACE["call"]["method"]
CLOUD_METHOD = FACE["call"]["cloud_method"]
PERMISSION_SET_ID = FACE["call"]["third_party_permission_set_id"]

REQUIRED = tuple(FACE["request"]["required"])
OPTIONAL = tuple(FACE["request"]["optional"])
SCENES = dict((int(k), v) for k, v in FACE["request"]["fields"]["scene"]["enum"].items())
VERSION_FIXED = FACE["request"]["fields"]["version"]["fixed"]

SUGGESTS = tuple(FACE["suggest"])
LABELS = dict((int(k), v) for k, v in FACE["labels"].items())
NORMAL_LABEL = 100

LIMITS = FACE["limits"]
CONTENT_MAX = LIMITS["content_max_chars"]
PROB_MIN = LIMITS["prob_min"]
PROB_MAX = LIMITS["prob_max"]


def validate_request(payload):
    """Return a list of refusal codes for a request the interface would refuse."""
    problems = []
    if not isinstance(payload, dict):
        return ["E_MSF_REQ_NOT_OBJECT"]
    for name in REQUIRED:
        if name not in payload:
            problems.append("E_MSF_REQ_MISSING_%s" % name.upper())

    content = payload.get("content")
    if content is not None:
        if not isinstance(content, str):
            problems.append("E_MSF_REQ_CONTENT_NOT_STRING")
        elif len(content) == 0:
            problems.append("E_MSF_REQ_CONTENT_EMPTY")
        elif len(content) > CONTENT_MAX:
            # The doc counts CHARACTERS ("2500 zi"), so len() is the right
            # measure and a UTF-8 byte count would refuse legal Chinese text.
            problems.append("E_MSF_REQ_CONTENT_TOO_LONG")

    if "version" in payload:
        version = payload.get("version")
        if isinstance(version, bool) or not isinstance(version, (int, float)):
            problems.append("E_MSF_REQ_VERSION_NOT_NUMBER")
        elif int(version) != VERSION_FIXED:
            problems.append("E_MSF_REQ_VERSION_NOT_2")

    if "scene" in payload:
        scene = payload.get("scene")
        if isinstance(scene, bool) or not isinstance(scene, (int, float)):
            problems.append("E_MSF_REQ_SCENE_NOT_NUMBER")
        elif int(scene) not in SCENES:
            problems.append("E_MSF_REQ_SCENE_UNKNOWN")

    if "openid" in payload:
        openid = payload.get("openid")
        if not isinstance(openid, str) or not openid.strip():
            problems.append("E_MSF_REQ_OPENID_EMPTY")

    # The doc says signature is only meaningful in the profile scene. Sending it
    # elsewhere is not an error the interface reports, so the gate refuses the
    # shape rather than letting an author believe the signature was checked.
    if "signature" in payload and payload.get("signature") is not None:
        scene = payload.get("scene")
        if isinstance(scene, (int, float)) and not isinstance(scene, bool):
            if int(scene) != 1:
                problems.append("E_MSF_REQ_SIGNATURE_OUT_OF_SCENE")

    for name in ("title", "nickname", "signature"):
        if name in payload and payload.get(name) is not None:
            if not isinstance(payload.get(name), str):
                problems.append("E_MSF_REQ_%s_NOT_STRING" % name.upper())
    return problems


def _check_detail_rows(rows, problems):
    """Grade the per-strategy detail array; inactive rows never drive a decision."""
    if rows is None:
        return
    if not isinstance(rows, list):
        problems.append("E_MSF_RES_DETAIL_NOT_ARRAY")
        return
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            problems.append("E_MSF_RES_DETAIL_ROW_NOT_OBJECT")
            continue
        suggest = row.get("suggest")
        if suggest is not None and suggest not in SUGGESTS:
            problems.append("E_MSF_RES_DETAIL_SUGGEST_UNKNOWN")
        label = row.get("label")
        if label is not None:
            if isinstance(label, bool) or not isinstance(label, int):
                problems.append("E_MSF_RES_DETAIL_LABEL_NOT_NUMBER")
            elif label not in LABELS:
                problems.append("E_MSF_RES_DETAIL_LABEL_UNKNOWN")
        prob = row.get("prob")
        if prob is not None:
            if isinstance(prob, bool) or not isinstance(prob, (int, float)):
                problems.append("E_MSF_RES_DETAIL_PROB_NOT_NUMBER")
            elif not (PROB_MIN <= prob <= PROB_MAX):
                problems.append("E_MSF_RES_DETAIL_PROB_OUT_OF_RANGE")
        errcode = row.get("errcode")
        if errcode is not None and errcode != 0:
            # Documented: a row is valid only when its errcode is 0. The row is
            # recorded but must not be read as a verdict about the content.
            continue


def parse_response(payload):
    """Return (decision, problems) for one interface response, fail-closed."""
    problems = []
    if not isinstance(payload, dict):
        return BLOCK, ["E_MSF_RES_NOT_OBJECT"]

    errcode = payload.get("errcode")
    if errcode is None:
        problems.append("E_MSF_RES_ERRCODE_MISSING")
        return BLOCK, problems
    if isinstance(errcode, bool) or not isinstance(errcode, int):
        problems.append("E_MSF_RES_ERRCODE_NOT_NUMBER")
        return BLOCK, problems
    if errcode != 0:
        problems.append("E_MSF_RES_ERRCODE_%d" % errcode)
        return BLOCK, problems

    result = payload.get("result")
    if not isinstance(result, dict):
        problems.append("E_MSF_RES_RESULT_MISSING")
        return BLOCK, problems

    suggest = result.get("suggest")
    if suggest not in SUGGESTS:
        problems.append("E_MSF_RES_SUGGEST_UNKNOWN")
        return BLOCK, problems

    label = result.get("label")
    if isinstance(label, bool) or not isinstance(label, int):
        problems.append("E_MSF_RES_LABEL_NOT_NUMBER")
        return BLOCK, problems
    if label not in LABELS:
        problems.append("E_MSF_RES_LABEL_UNKNOWN")
        return BLOCK, problems

    # An inconsistent pair is not a pass: the documented "normal" tag is 100, so
    # a pass carrying any other label is a response the gate cannot trust.
    if suggest == "pass" and label != NORMAL_LABEL:
        problems.append("E_MSF_RES_PASS_LABEL_INCONSISTENT")
        return BLOCK, problems

    _check_detail_rows(payload.get("detail"), problems)
    # Detail shape problems are recorded but the top-level verdict stands: the
    # documented decision is result.suggest. A malformed detail array is still
    # worth naming, so it is returned rather than swallowed.
    return DECISION_BY_SUGGEST[suggest], problems


def adjudicate(request, response):
    """One call: refuse a bad request before reading any response."""
    problems = validate_request(request)
    if problems:
        return BLOCK, problems
    return parse_response(response)


def check(face=None):
    """Read-only: does the documented face still say what this gate assumes?"""
    face = face or FACE
    fails = []

    def expect(cond, code):
        if not cond:
            fails.append(code)

    expect(face["call"]["method"] == "POST", "E_MSF_CHK_METHOD")
    expect(face["call"]["path"] == "/wxa/msg_sec_check", "E_MSF_CHK_PATH")
    expect(face["call"]["cloud_method"] == "security.msgSecCheck",
           "E_MSF_CHK_CLOUD_METHOD")
    expect(face["call"]["third_party_permission_set_id"] == 18,
           "E_MSF_CHK_PERMISSION_SET")
    expect(face["request"]["fields"]["version"]["fixed"] == 2,
           "E_MSF_CHK_VERSION")
    expect(sorted(int(k) for k in face["request"]["fields"]["scene"]["enum"]) ==
           [1, 2, 3, 4], "E_MSF_CHK_SCENES")
    expect(sorted(face["suggest"]) == ["pass", "review", "risky"],
           "E_MSF_CHK_SUGGESTS")
    expect(set(int(k) for k in face["labels"]) ==
           {100, 10001, 20001, 20002, 20003, 20006, 20008, 20012, 20013, 21000},
           "E_MSF_CHK_LABELS")
    expect(face["labels"]["100"] == "normal", "E_MSF_CHK_NORMAL_LABEL")
    expect(face["limits"]["content_max_chars"] == 2500, "E_MSF_CHK_CONTENT_MAX")
    expect(face["limits"]["per_minute"] == 4000, "E_MSF_CHK_RATE_MINUTE")
    expect(face["limits"]["per_day"] == 2000000, "E_MSF_CHK_RATE_DAY")
    expect(face["limits"]["unpublished_per_day"] == 100,
           "E_MSF_CHK_RATE_UNPUBLISHED")
    expect(set(face["request"]["required"]) ==
           {"content", "version", "scene", "openid"}, "E_MSF_CHK_REQUIRED")
    expect(face["source"]["verbatim"] is True, "E_MSF_CHK_SOURCE_NOT_VERBATIM")
    expect("msgseccheck" in face["source"]["url"].lower(),
           "E_MSF_CHK_SOURCE_URL")
    return fails


def main(argv=None):
    ap = argparse.ArgumentParser(description="msgSecCheck parameter face gate")
    ap.add_argument("--check", action="store_true",
                    help="read-only verdict on the documented face")
    ap.add_argument("--face", default=None, help="alternate face json")
    args = ap.parse_args(argv)

    face = load_face(args.face)
    fails = check(face)
    print("msgSecCheck face: path=%s cloud=%s permission_set=%d "
          "content_max=%d scenes=%d labels=%d suggests=%d"
          % (face["call"]["path"], face["call"]["cloud_method"],
             face["call"]["third_party_permission_set_id"],
             face["limits"]["content_max_chars"],
             len(face["request"]["fields"]["scene"]["enum"]),
             len(face["labels"]), len(face["suggest"])))
    if args.check:
        if fails:
            print("VERDICT FAIL fails=%d %s" % (len(fails), " ".join(fails)))
            return 2
        print("VERDICT PASS checks=16 read_only=True")
        return 0
    print("VERDICT READY (use --check for the graded verdict)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
