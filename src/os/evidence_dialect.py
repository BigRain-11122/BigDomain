"""The evidence-file dialect law, in ONE place (R2926, AC-EVB1..AC-EVB5).

Why this module exists: until R2926 the dialect rule lived inside
src/os/qa_writer_census.py, which imports reconcile_all (the shipped SUITES
registry) at module level. That is a fine dependency for a census probe and a
bad one for a commit hook: the hook must answer "is this staged evidence file
in the healthy dialect" without loading the whole registry.

So the rule moved here, verbatim, and the census now DELEGATES to it. There is
still exactly one classification law (the R2901/R2905/R2906 lesson: a rule
typed in two places drifts in one of them).

The rule itself is unchanged and pre-registered at R1836 (AC-SL3):

  * BOM utf-16le/utf-16be            -> ps-utf16     (PS 5.1 `>` family)
  * no BOM + any NUL byte present    -> nul-bytes    (BOM-less UTF-16; this
                                                      branch runs BEFORE the
                                                      EOL branches - R2808)
  * no BOM + crlf==0 + strict utf-8  -> tee          (healthy dialect)
  * no BOM + crlf-dominant + utf-8 FAILS -> cmd-raw  (raw cp936 family)
  * no BOM + crlf-dominant + utf-8 OK    -> pwsh-capture
  * anything else                    -> other        (honest catch-all)

`tee` is the only healthy class. Everything else is a named debt class.

The label column is NOT part of the rule (R2926 measurement): SHELL_CAPTURE_LABEL
marks one writer family, not a dialect - on the shipped tree 410 labeled files
classify tee and 579 of the 590 baselined debt files carry no label. label_absent
is a census column; the refusal is the class.

Stdlib only, ASCII source, zero network, zero shell, writes nothing.
"""

import os

HEALTHY = "tee"
CLASSES = ("tee", "cmd-raw", "pwsh-capture", "ps-utf16", "nul-bytes",
           "other")
BASELINE_CLASSES = ("cmd-raw", "pwsh-capture", "ps-utf16", "nul-bytes",
                    "other")

BOM_UTF8 = b"\xef\xbb\xbf"
BOM_16LE = b"\xff\xfe"
BOM_16BE = b"\xfe\xff"


def bom_of(raw):
    """Name the BOM, if any (AC-QD family). This module is a LEAF: no
    import of the sandbox registry, so the commit gate can ask it before
    anything else in the tree is loadable.

    R2926: `qa_decode_probe._bom_of` was the single source of this
    answer; it now imports THIS function, so the count of the rule is
    still one and the dependency points at the leaf rather than away
    from it.
    """
    if raw.startswith(BOM_16LE):
        return "utf-16le"
    if raw.startswith(BOM_16BE):
        return "utf-16be"
    if raw.startswith(BOM_UTF8):
        return "utf-8-sig"
    return "utf-8"  # presumed (no BOM on disk) - the R1836 census column


def classify_bytes(raw, label=None):
    """Classify one evidence blob. `label` is the ASCII label bytes to look
    for on the first physical line (None = do not read the label column).

    Returns a row dict; every number is measured, never fabricated.
    """
    row = {"bytes": len(raw), "bom": bom_of(raw), "crlf": 0,
           "bare_lf": 0, "utf8": False, "label": False, "class": "other"}
    row["crlf"] = raw.count(b"\r\n")
    row["bare_lf"] = raw.count(b"\n") - row["crlf"]
    try:
        raw.decode("utf-8", "strict")
        row["utf8"] = True
    except UnicodeDecodeError:
        row["utf8"] = False
    if label is not None:
        first = raw.split(b"\n", 1)[0]
        if first.endswith(b"\r"):
            first = first[:-1]
        row["label"] = (first == label)
    if row["bom"] in ("utf-16le", "utf-16be"):
        row["class"] = "ps-utf16"
    elif row["bom"] == "utf-8-sig":
        row["class"] = "other"
    elif b"\x00" in raw:
        row["class"] = "nul-bytes"
    elif row["crlf"] == 0:
        row["class"] = "tee" if row["utf8"] else "other"
    elif row["crlf"] > row["bare_lf"]:
        row["class"] = "pwsh-capture" if row["utf8"] else "cmd-raw"
    else:
        row["class"] = "other"
    return row


def label_coverage(rows):
    """Split classified rows by the label column.

    Returns {"labeled": n, "unlabeled": n, "labeled_names": [...]}. The
    shipped census publishes this for the baselined debt so a reader can see
    whether the self-announcing writer covers it - measured at R2926: 11 of
    590, which is why label absence cannot be a refusal.
    """
    labeled = []
    unlabeled = 0
    for name, row in rows:
        if row["label"]:
            labeled.append(name)
        else:
            unlabeled += 1
    return {"labeled": len(labeled), "unlabeled": unlabeled,
            "labeled_names": sorted(labeled)}
