"""Suite for the msgSecCheck parameter face (AC-MSF1..AC-MSF6).

Criteria were pinned in src/os/backlog.md at R2908 BEFORE msgsec_face.py existed.
Every arm is measured: a lawful input must pass AND a doctored one must be
refused, so a criterion cannot pass as a constant that happens to match today.

Run: python src/sandbox/ugc/test_msgsec_face.py
"""

import copy
import hashlib
import io
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import msgsec_face as MF  # noqa: E402

RESULTS = []
CRITERIA = []


def check(criterion, name, cond, detail=""):
    if criterion not in CRITERIA:
        CRITERIA.append(criterion)
    RESULTS.append((criterion, name, bool(cond), detail))


LAWFUL_REQUEST = {
    "openid": "OPENID",
    "scene": 1,
    "version": 2,
    "content": "hello world!",
}
LAWFUL_RESPONSE = {
    "errcode": 0,
    "errmsg": "ok",
    "result": {"suggest": "pass", "label": 100},
    "trace_id": "60ae120f-371d5872-7941a05b",
}


def resp(suggest, label, **extra):
    out = {"errcode": 0, "errmsg": "ok",
           "result": {"suggest": suggest, "label": label}}
    out.update(extra)
    return out


# --- AC-MSF1: the documented face is the law, and a doctored face reddens ---
face = MF.FACE
check("AC-MSF1", "method is POST", face["call"]["method"] == "POST")
check("AC-MSF1", "path is /wxa/msg_sec_check",
      face["call"]["path"] == "/wxa/msg_sec_check")
check("AC-MSF1", "cloud method is security.msgSecCheck",
      face["call"]["cloud_method"] == "security.msgSecCheck")
check("AC-MSF1", "third-party permission set id 18",
      face["call"]["third_party_permission_set_id"] == 18)
check("AC-MSF1", "version fixed at 2",
      face["request"]["fields"]["version"]["fixed"] == 2)
check("AC-MSF1", "four scenes 1..4",
      sorted(int(k) for k in face["request"]["fields"]["scene"]["enum"]) ==
      [1, 2, 3, 4])
check("AC-MSF1", "three suggests",
      sorted(face["suggest"]) == ["pass", "review", "risky"])
check("AC-MSF1", "ten labels including 100 normal",
      len(face["labels"]) == 10 and face["labels"]["100"] == "normal")
check("AC-MSF1", "content limit 2500 characters",
      face["limits"]["content_max_chars"] == 2500)
check("AC-MSF1", "rate 4000/min and 2000000/day and 100 unpublished/day",
      (face["limits"]["per_minute"], face["limits"]["per_day"],
       face["limits"]["unpublished_per_day"]) == (4000, 2000000, 100))
check("AC-MSF1", "required body fields are content/version/scene/openid",
      set(face["request"]["required"]) ==
      {"content", "version", "scene", "openid"})
check("AC-MSF1", "source is marked verbatim and named",
      face["source"]["verbatim"] is True and
      "msgseccheck" in face["source"]["url"].lower())
# Negative control: the same checker must redden a doctored face.
bad = copy.deepcopy(face)
bad["call"]["path"] = "/wxa/msg_sec_check_v1_guess"
bad["labels"].pop("20013")
bad["limits"]["content_max_chars"] = 5000
check("AC-MSF1", "doctored face reddens (path, label, limit)",
      len(MF.check(bad)) >= 3,
      ",".join(MF.check(bad)))
check("AC-MSF1", "lawful face grades clean", MF.check(face) == [],
      ",".join(MF.check(face)))

# --- AC-MSF2: the request gate, measured at both sides of every boundary ---
check("AC-MSF2", "lawful request accepted",
      MF.validate_request(LAWFUL_REQUEST) == [],
      ",".join(MF.validate_request(LAWFUL_REQUEST)))
check("AC-MSF2", "content at exactly 2500 characters accepted",
      MF.validate_request(dict(LAWFUL_REQUEST, content="x" * 2500)) == [])
check("AC-MSF2", "content at 2501 characters refused",
      MF.validate_request(dict(LAWFUL_REQUEST, content="x" * 2501)) ==
      ["E_MSF_REQ_CONTENT_TOO_LONG"])
check("AC-MSF2", "2500 CJK characters accepted (character count, not bytes)",
      MF.validate_request(dict(LAWFUL_REQUEST, content="\u6d4b" * 2500)) == [])
check("AC-MSF2", "empty content refused",
      MF.validate_request(dict(LAWFUL_REQUEST, content="")) ==
      ["E_MSF_REQ_CONTENT_EMPTY"])
check("AC-MSF2", "content of a non-string type refused",
      MF.validate_request(dict(LAWFUL_REQUEST, content=42)) ==
      ["E_MSF_REQ_CONTENT_NOT_STRING"])
check("AC-MSF2", "version 1 refused",
      MF.validate_request(dict(LAWFUL_REQUEST, version=1)) ==
      ["E_MSF_REQ_VERSION_NOT_2"])
check("AC-MSF2", "scene 5 refused",
      MF.validate_request(dict(LAWFUL_REQUEST, scene=5)) ==
      ["E_MSF_REQ_SCENE_UNKNOWN"])
check("AC-MSF2", "scene 4 (social log) accepted",
      MF.validate_request(dict(LAWFUL_REQUEST, scene=4)) == [])
check("AC-MSF2", "blank openid refused",
      MF.validate_request(dict(LAWFUL_REQUEST, openid="  ")) ==
      ["E_MSF_REQ_OPENID_EMPTY"])
check("AC-MSF2", "all four required fields missing are each named",
      sorted(MF.validate_request({"title": "t"})) ==
      ["E_MSF_REQ_MISSING_CONTENT", "E_MSF_REQ_MISSING_OPENID",
       "E_MSF_REQ_MISSING_SCENE", "E_MSF_REQ_MISSING_VERSION"])
check("AC-MSF2", "signature in the comment scene refused",
      MF.validate_request(dict(LAWFUL_REQUEST, scene=2, signature="sig")) ==
      ["E_MSF_REQ_SIGNATURE_OUT_OF_SCENE"])
check("AC-MSF2", "signature in the profile scene accepted",
      MF.validate_request(dict(LAWFUL_REQUEST, scene=1, signature="sig")) == [])
check("AC-MSF2", "non-object payload refused",
      MF.validate_request(["content"]) == ["E_MSF_REQ_NOT_OBJECT"])

# --- AC-MSF3: the response gate is fail-closed in every direction ---
decision, problems = MF.parse_response(LAWFUL_RESPONSE)
check("AC-MSF3", "lawful pass response allows",
      decision == MF.ALLOW and problems == [], "%s %s" % (decision, problems))
decision, problems = MF.parse_response({"errcode": 40003, "errmsg": "invalid openid"})
check("AC-MSF3", "non-zero errcode blocks even with no result",
      decision == MF.BLOCK and "E_MSF_RES_ERRCODE_40003" in problems,
      ",".join(problems))
decision, problems = MF.parse_response({"errcode": 0, "errmsg": "ok"})
check("AC-MSF3", "errcode 0 with no result blocks",
      decision == MF.BLOCK and "E_MSF_RES_RESULT_MISSING" in problems)
decision, problems = MF.parse_response({"errmsg": "ok"})
check("AC-MSF3", "missing errcode blocks",
      decision == MF.BLOCK and "E_MSF_RES_ERRCODE_MISSING" in problems)
decision, problems = MF.parse_response(resp("maybe", 100))
check("AC-MSF3", "unknown suggest blocks",
      decision == MF.BLOCK and "E_MSF_RES_SUGGEST_UNKNOWN" in problems)
decision, problems = MF.parse_response(resp("risky", 99999))
check("AC-MSF3", "unknown label blocks",
      decision == MF.BLOCK and "E_MSF_RES_LABEL_UNKNOWN" in problems)
decision, problems = MF.parse_response(resp("pass", 20002))
check("AC-MSF3", "pass carrying a non-normal label blocks",
      decision == MF.BLOCK and
      "E_MSF_RES_PASS_LABEL_INCONSISTENT" in problems, ",".join(problems))
decision, problems = MF.parse_response("ok")
check("AC-MSF3", "non-object response blocks",
      decision == MF.BLOCK and "E_MSF_RES_NOT_OBJECT" in problems)
decision, problems = MF.parse_response(resp("pass", True))
check("AC-MSF3", "boolean label is not an integer label",
      decision == MF.BLOCK and "E_MSF_RES_LABEL_NOT_NUMBER" in problems)

# --- AC-MSF4: the three documented verdicts map to three distinct decisions ---
check("AC-MSF4", "pass allows", MF.parse_response(resp("pass", 100))[0] == MF.ALLOW)
check("AC-MSF4", "review queues rather than allows",
      MF.parse_response(resp("review", 21000))[0] == MF.QUEUE)
check("AC-MSF4", "risky blocks",
      MF.parse_response(resp("risky", 20002))[0] == MF.BLOCK)
check("AC-MSF4", "the three decisions are distinct",
      len({MF.ALLOW, MF.QUEUE, MF.BLOCK}) == 3)
check("AC-MSF4", "adjudicate refuses a bad request before reading a good response",
      MF.adjudicate({"content": "x" * 2501}, LAWFUL_RESPONSE)[0] == MF.BLOCK)
check("AC-MSF4", "adjudicate passes a lawful pair through",
      MF.adjudicate(LAWFUL_REQUEST, LAWFUL_RESPONSE)[0] == MF.ALLOW)

# --- AC-MSF5: detail rows are graded and an inactive row never decides ---
rows = [{"strategy": "content_model", "errcode": 0, "suggest": "risky",
         "label": 20006, "prob": 90},
        {"strategy": "keyword", "errcode": 0, "suggest": "pass",
         "label": 20006, "level": 20, "keyword": "k1"}]
decision, problems = MF.parse_response(resp("risky", 20001, detail=rows))
check("AC-MSF5", "documented detail array accepted",
      decision == MF.BLOCK and problems == [], ",".join(problems))
decision, problems = MF.parse_response(
    resp("risky", 20001, detail=[{"errcode": 0, "suggest": "unclear",
                                  "label": 20006}]))
check("AC-MSF5", "unknown detail suggest is named",
      "E_MSF_RES_DETAIL_SUGGEST_UNKNOWN" in problems, ",".join(problems))
decision, problems = MF.parse_response(
    resp("risky", 20001, detail=[{"errcode": 0, "suggest": "risky",
                                  "label": 20006, "prob": 101}]))
check("AC-MSF5", "detail prob above 100 is named",
      "E_MSF_RES_DETAIL_PROB_OUT_OF_RANGE" in problems)
decision, problems = MF.parse_response(
    resp("risky", 20001, detail=[{"errcode": 40001, "suggest": "pass",
                                  "label": 100}]))
check("AC-MSF5", "an inactive detail row does not override the top verdict",
      decision == MF.BLOCK, decision)
decision, problems = MF.parse_response(
    resp("pass", 100, detail="not-a-list"))
check("AC-MSF5", "a non-array detail block is named",
      "E_MSF_RES_DETAIL_NOT_ARRAY" in problems)

# --- AC-MSF6: purity, determinism, read-only --check ---
src = open(os.path.join(BASE, "msgsec_face.py"), "r", encoding="utf-8").read()
check("AC-MSF6", "source is pure ASCII", all(ord(c) < 128 for c in src))
banned = ("urllib", "requests", "http.client", "socket", "aiohttp")
check("AC-MSF6", "no network import",
      not any(("import " + b) in src for b in banned))
check("AC-MSF6", "declares no credential handling",
      "appid" not in src.lower() or "no key" in src.lower())

dl = [os.path.join(BASE, "msgsec_face.py"), os.path.join(BASE, "msgsec_face.json")]


def digest(paths):
    h = hashlib.sha256()
    for p in paths:
        with open(p, "rb") as fh:
            h.update(fh.read())
    return h.hexdigest()


before = digest(dl)
run1 = subprocess.run([sys.executable, os.path.join(BASE, "msgsec_face.py"),
                       "--check"], capture_output=True, text=True)
after = digest(dl)
check("AC-MSF6", "--check exits 0", run1.returncode == 0, run1.stdout.strip())
check("AC-MSF6", "--check prints VERDICT PASS", "VERDICT PASS" in run1.stdout)
check("AC-MSF6", "--check writes nothing (digest unchanged)", before == after)
run2 = subprocess.run([sys.executable, os.path.join(BASE, "msgsec_face.py"),
                       "--check"], capture_output=True, text=True)
check("AC-MSF6", "double run is byte-identical",
      run1.stdout == run2.stdout and run1.returncode == run2.returncode)

# --- report ---
passed = sum(1 for r in RESULTS if r[2])
failed = [r for r in RESULTS if not r[2]]
buf = io.StringIO()
for criterion, name, ok, detail in RESULTS:
    if not ok:
        buf.write("FAIL %s %s %s\n" % (criterion, name, detail))
buf.write("SUITE %s %d/%d criteria=%d\n"
          % ("PASS" if not failed else "FAIL", passed, len(RESULTS),
             len(CRITERIA)))
out = buf.getvalue()
sys.stdout.write(out)
sys.exit(0 if not failed else 1)
