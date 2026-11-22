"""Render preview/start-here.html - the one page a first visitor opens to see what
this machine can actually be operated for today.

Every number on the page is derived from preview/*.html on the same run; the
--check arm re-scans the disk and re-reads the page, so a stale page or a hand
edit reddens instead of passing. Chinese strings live in
state/start-here-faces.json and state/merchant-onboard-items.json; this source
stays ASCII (encoding law).
"""

import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(ROOT, "preview")
DATA = os.path.join(ROOT, "state", "start-here-faces.json")
OUT_HTML = os.path.join(PREVIEW, "start-here.html")
OUT_JSON = os.path.join(PREVIEW, "start-here.json")

EXCLUDE = {"index.html", "start-here.html"}
OPS = ("input", "button", "select", "textarea")
EXT = re.compile(r'(?:src|href)\s*=\s*["\']https?://', re.I)
HREF = re.compile(r'<a\s[^>]*href="([^"]+)"')

# What a control actually changes is read off the face itself, never authored:
# a page whose script touches browser storage keeps its state across a reload
# (persists); a page whose script rewrites the DOM keeps it only while open
# (screen); a script with listeners but no derived output is wires; a control
# with no script behind it is inert (only the browser's own check state moves).
SCRIPT = re.compile(r"<script\b", re.I)
STORAGE = re.compile(r"\b(localStorage|sessionStorage|indexedDB)\b")
HANDLER = re.compile(r"\b(addEventListener|onclick|oninput|onchange|onkeyup)\b", re.I)
DOMWRITE = re.compile(r"\.(textContent|innerHTML|value)\s*=")
KINDS = ("persists", "screen", "wires", "inert")

# Pairing says WHICH symbols a key rests on; it cannot say WHERE the variable part of
# the key comes from. A face that reads NS+':'+kk and writes NS+':'+this.getAttribute(..)
# is an orphan by symbols yet takes both sides from the same DOM attribute. The source
# tier is read one hop deep from the face's own bytes: a name bound to a literal is
# const, a loop-bound name is loop, a name bound to anything else is runtime, and a name
# or expression that reads a DOM/external value is dom. Nothing is executed.
TIERS = ("literal", "const", "loop", "runtime", "dom")
TIER_ORDER = {name: i for i, name in enumerate(TIERS)}
DOMVALUE = re.compile(r"\b(getAttribute|dataset|innerHTML|innerText|textContent|checked|"
                      r"selectedIndex|getItem|prompt|confirm|Math\.random)\b")
ASSIGN = re.compile(r"(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*([^;]{0,240})")
LOOPVAR = re.compile(r"for\s*\(\s*(?:var|let|const)?\s*([A-Za-z_$][\w$]*)\s*(?:in|of)\b")

# A persists face keeps state in browser storage, but WHICH key is only half of it:
# a page that reads a key it never writes is reading nothing. The live faces key by
# SYMBOL (NS, KEY, k), not by literal, so pairing is read on two levels - the key
# expression, and the declared symbols that expression rests on.
CALL = re.compile(r"\.(setItem|getItem|removeItem)\s*\(")
DECL = re.compile(r"\b(?:var|let|const)\s+([A-Za-z_$][\w$]*)")
IDENT = re.compile(r"[A-Za-z_$][\w$]*")
STR = re.compile(r"'[^']*'|\"[^\"]*\"")
MEMBER = re.compile(r"\.\s*[A-Za-z_$][\w$]*")
KEYWORDS = {"this", "window", "document", "true", "false", "null", "undefined",
            "function", "return", "typeof", "new", "JSON", "String", "Number",
            "localStorage", "sessionStorage", "indexedDB"}


def sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def classify(text):
    """Which kind of change a click can make, derived from the face's own bytes."""
    storage = len(STORAGE.findall(text))
    script = len(SCRIPT.findall(text))
    handler = len(HANDLER.findall(text))
    domwrite = len(DOMWRITE.findall(text))
    if storage:
        kind = "persists"
    elif script and handler and domwrite:
        kind = "screen"
    elif script and handler:
        kind = "wires"
    else:
        kind = "inert"
    return {"storage": storage, "script": script, "handler": handler,
            "domwrite": domwrite, "kind": kind}


def _first_arg(text, open_paren):
    depth = 0
    for i in range(open_paren, min(len(text), open_paren + 600)):
        ch = text[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                return text[open_paren + 1:i]
        elif ch == "," and depth == 1:
            return text[open_paren + 1:i]
    return ""


def _key_symbols(expr):
    """The declared-looking identifiers a key expression rests on. String literals and
    member tails are stripped first, so 'data-ck' and this.getAttribute are not
    mistaken for symbols (the first probe run made exactly that mistake)."""
    bare = MEMBER.sub("", STR.sub('""', expr))
    return sorted({tok for tok in IDENT.findall(bare) if tok not in KEYWORDS})


def key_reading(text):
    """How a face keys its storage: which expressions it writes and reads, and the
    symbols those expressions rest on. Text only - no JS is ever executed."""
    bare = STR.sub('""', text)
    declared = set(DECL.findall(bare))
    buckets = {"setItem": set(), "getItem": set(), "removeItem": set()}
    for match in CALL.finditer(bare):
        expr = re.sub(r"\s+", "", _first_arg(bare, match.end() - 1))
        if expr:
            buckets[match.group(1)].add(expr)
    writes, reads, removes = buckets["setItem"], buckets["getItem"], buckets["removeItem"]
    symbols = {expr: _key_symbols(expr) for expr in writes | reads | removes}
    base_write = sorted({tok for expr in writes for tok in symbols[expr]})
    base_read = sorted({tok for expr in reads for tok in symbols[expr]})
    unresolved = sorted({tok for expr in symbols for tok in symbols[expr]
                         if tok not in declared})
    return {
        "write": sorted(writes), "read": sorted(reads), "remove": sorted(removes),
        "base_write": base_write, "base_read": base_read,
        "expr_paired": bool(reads) and reads <= writes,
        "base_paired": set(base_read) <= set(base_write),
        "unresolved": unresolved,
    }


def _cut_rhs(rhs):
    """A declaration can carry several names (`var A='x', B=...`); stopping at the
    first top-level comma keeps each name bound to its own value. Reading the whole
    tail made a literal binding look like a runtime one on the first probe run."""
    depth = 0
    for i, ch in enumerate(rhs):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            return rhs[:i]
    return rhs


def _bindings(text):
    """One-hop resolution: every declared name and the tier of what it was bound to."""
    bare = STR.sub('""', text)
    bound = {}
    for match in ASSIGN.finditer(bare):
        name, rhs = match.group(1), _cut_rhs(match.group(2))
        if DOMVALUE.search(rhs):
            tier = "dom"
        else:
            names = [tok for tok in IDENT.findall(MEMBER.sub("", STR.sub("", rhs)))
                     if tok not in KEYWORDS]
            tier = "const" if not names else "runtime"
        if TIER_ORDER[tier] > TIER_ORDER.get(bound.get(name, "literal"), 0):
            bound[name] = tier
    for match in LOOPVAR.finditer(bare):
        name = match.group(1)
        if TIER_ORDER.get(bound.get(name, "literal"), 0) < TIER_ORDER["loop"]:
            bound[name] = "loop"
    return bound


def _expr_tier(expr, bound):
    tier = "dom" if DOMVALUE.search(expr) else "literal"
    for tok in _key_symbols(expr):
        got = bound.get(tok, "runtime")
        if TIER_ORDER[got] > TIER_ORDER[tier]:
            tier = got
    return tier


def tier_reading(text, keys=None):
    """Where the VARIABLE part of each key expression comes from, one hop deep. This is
    a second reading of the same bytes as key_reading, not a correction of it: symbols
    answer 'does the read rest on what the write declares', tiers answer 'do the two
    sides draw their variable part from the same kind of place'."""
    keys = keys or key_reading(text)
    bound = _bindings(text)
    writes = [(expr, _expr_tier(expr, bound)) for expr in keys["write"]]
    reads = [(expr, _expr_tier(expr, bound)) for expr in keys["read"]]
    write_tier = max((t for _, t in writes), key=lambda t: TIER_ORDER[t]) if writes else None
    read_tier = max((t for _, t in reads), key=lambda t: TIER_ORDER[t]) if reads else None
    if read_tier is None:
        same = "noread"
    elif read_tier == write_tier:
        same = "same"
    else:
        same = "cross"
    return {"writes": writes, "reads": reads, "bound": bound,
            "write_tier": write_tier, "read_tier": read_tier, "same": same}


def scan_faces():
    """Per preview face: how many controls it carries, what a click can change, and
    whether it leaves the machine."""
    rows = {}
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".html"):
            continue
        with open(os.path.join(PREVIEW, name), "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8", "replace")
        counts = {key: len(re.findall(r"<%s\b" % key, text, re.I)) for key in OPS}
        row = {
            "bytes": len(raw),
            "counts": counts,
            "ops": sum(counts.values()),
            "external": len(EXT.findall(text)),
        }
        row.update(classify(text))
        if row["storage"]:
            row["keys"] = key_reading(text)
            row["tiers"] = tier_reading(text, row["keys"])
        rows[name] = row
    return rows


def operable_set(rows):
    return [name for name, row in rows.items() if row["ops"] > 0 and name not in EXCLUDE]


def missing_ceo_items():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import merchant_onboard as mo

    return [row for row in mo.project_items() if row.get("owner") == "ceo" and not row.get("proven")]


def projection():
    rows = scan_faces()
    doc = load_json(DATA)
    operable = operable_set(rows)
    gaps = []
    hand_written = []
    for name in operable:
        entry = (doc.get("faces") or {}).get(name) or {}
        for key in ("label", "can", "cannot"):
            if not (entry.get(key) or "").strip():
                gaps.append("%s missing %s" % (name, key))
        # A hand-authored kind would turn the stratification back into a list that
        # only tracks drift; the kind must come from the bytes.
        if "kind" in entry:
            hand_written.append(name)
    kinds = {kind: [] for kind in KINDS}
    for name in operable:
        kinds[rows[name]["kind"]].append(name)
    key_faces = [name for name in operable if "keys" in rows[name]]
    key_outside = [name for name in rows
                   if "keys" in rows[name] and name not in operable
                   and name != "start-here.html"]
    key_counts = {
        "persists": len(key_faces),
        "expr_paired": len([n for n in key_faces if rows[n]["keys"]["expr_paired"]]),
        "base_paired": len([n for n in key_faces if rows[n]["keys"]["base_paired"]]),
        "orphan": len([n for n in key_faces if not rows[n]["keys"]["base_paired"]]),
        "unresolved": len([n for n in key_faces if rows[n]["keys"]["unresolved"]]),
        "outside": len(key_outside),
    }
    tier_counts = {tier: 0 for tier in TIERS}
    for name in key_faces:
        got = rows[name]["tiers"]["write_tier"]
        if got:
            tier_counts[got] += 1
    tier_cross = [n for n in key_faces if rows[n]["tiers"]["same"] == "cross"]
    tier_noread = [n for n in key_faces if rows[n]["tiers"]["same"] == "noread"]
    return {
        "rows": rows,
        "doc": doc,
        "operable": operable,
        "faces_total": len([name for name in rows if name != "start-here.html"]),
        "gaps": gaps,
        "hand_written": hand_written,
        "kinds": kinds,
        "kind_counts": {kind: len(kinds[kind]) for kind in KINDS},
        "key_faces": key_faces,
        "key_outside": key_outside,
        "key_counts": key_counts,
        "key_orphans": [n for n in key_faces if not rows[n]["keys"]["base_paired"]],
        "key_unresolved": [n for n in key_faces if rows[n]["keys"]["unresolved"]],
        "tier_counts": tier_counts,
        "tier_cross": tier_cross,
        "tier_noread": tier_noread,
        "missing": missing_ceo_items(),
        "data16": sha16(DATA),
    }


def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def kind_tag(doc, kind):
    return ((doc.get("kind_tags") or {}).get(kind) or kind)


def kind_note(doc, kind):
    return ((doc.get("kind_notes") or {}).get(kind) or "")


def key_phrase(doc, keys):
    """One face's key pairing in words, read off that face's own bytes."""
    paired = (doc.get("keys_paired_word") if keys["base_paired"]
              else doc.get("keys_orphan_word")) or ""
    return (doc.get("keys_fmt") or "").format(
        write=len(keys["write"]), read=len(keys["read"]), paired=paired,
        unresolved=len(keys["unresolved"]))


def tier_tag(doc, tier):
    return ((doc.get("tier_tags") or {}).get(tier) or (tier or ""))


def tier_phrase(doc, tiers):
    """One face's key source in words. Says what the tier does NOT prove."""
    same = tiers["same"]
    word = ((doc.get("tiers_same_word") if same == "same" else
             doc.get("tiers_cross_word") if same == "cross" else
             doc.get("tiers_noread_word")) or "")
    read = tier_tag(doc, tiers["read_tier"]) if tiers["read_tier"] else (
        doc.get("tiers_noread") or "")
    return (doc.get("tiers_fmt") or "").format(
        write=tier_tag(doc, tiers["write_tier"]), read=read, same=word)


def render(proj):
    doc = proj["doc"]
    faces = doc.get("faces") or {}
    sub = doc["sub_fmt"].format(faces=proj["faces_total"], operable=len(proj["operable"]))
    cards = []
    for name in proj["operable"]:
        entry = faces.get(name) or {}
        if not entry:
            # A missing entry is graded by AC-SH3; render a named shell so the check
            # reports a missing row instead of crashing on it.
            entry = {"label": name, "can": "", "cannot": ""}
        label = entry.get("label") or ""
        can = entry.get("can") or ""
        cannot = entry.get("cannot") or ""
        kind = proj["rows"][name]["kind"]
        if "keys" in proj["rows"][name]:
            keys = proj["rows"][name]["keys"]
            keyline = ('    <p class="keyline" data-keys="%s" data-keys-write="%d" '
                       'data-keys-read="%d" data-keys-base="%s">%s</p>\n'
                       % (esc(name), len(keys["write"]), len(keys["read"]),
                          "paired" if keys["base_paired"] else "orphan",
                          esc(key_phrase(doc, keys))))
        else:
            keyline = ""
        if "tiers" in proj["rows"][name]:
            tiers = proj["rows"][name]["tiers"]
            tierline = ('    <p class="tierline" data-tiers="%s" data-tiers-write="%s" '
                        'data-tiers-read="%s" data-tiers-same="%s">%s</p>\n'
                        % (esc(name), esc(tiers["write_tier"] or ""),
                           esc(tiers["read_tier"] or ""), esc(tiers["same"]),
                           esc(tier_phrase(doc, tiers))))
        else:
            tierline = ""
        cards.append(
            '  <article class="face" data-face="%s">\n'
            '    <h3><a href="%s">%s</a> <code>%s</code></h3>\n'
            '    <p class="kindline"><span class="kbadge" data-kind="%s">%s</span></p>\n'
            '%s%s'
            '    <p><b>%s</b>%s</p>\n'
            '    <p class="limit"><b>%s</b>%s</p>\n'
            '    <p><a class="go" href="%s">%s &rarr;</a></p>\n'
            '  </article>\n' % (
                esc(name), esc(name), esc(label), esc(name),
                esc(kind), esc(kind_tag(doc, kind)), keyline, tierline,
                esc(doc["can_tag"]), esc(can),
                esc(doc["cannot_tag"]), esc(cannot),
                esc(name), esc(doc["open_link"]),
            )
        )
    kind_counts = "\n".join(
        '  <span class="kc" data-kind-count="%s"><b>%d</b>%s</span>'
        % (kind, proj["kind_counts"][kind], esc(kind_tag(doc, kind)))
        for kind in KINDS
    )
    legend = []
    for kind in KINDS:
        if proj["kind_counts"][kind]:
            legend.append('  <p data-kind-note="%s"><b>%s</b>：%s</p>'
                          % (kind, esc(kind_tag(doc, kind)), esc(kind_note(doc, kind))))
        else:
            absent = doc.get("kind_absent") or "{tag}"
            legend.append('  <p data-kind-absent="%s">%s</p>'
                          % (kind, esc(absent.format(tag=kind_tag(doc, kind)))))
    legend_block = "\n".join(legend)
    key_tags = doc.get("keys_count_tags") or {}
    key_counts_html = "\n".join(
        '  <span class="kc" data-keys-count="%s"><b>%d</b>%s</span>'
        % (key, proj["key_counts"][key], esc(key_tags.get(key) or key))
        for key in ("persists", "expr_paired", "base_paired", "orphan",
                    "unresolved", "outside")
    )
    keys_notes = []
    for name in proj["key_orphans"] or [None]:
        if not name:
            keys_notes.append('  <p data-keys-orphan-absent>%s</p>'
                              % esc(doc.get("keys_absent") or ""))
            continue
        keys = proj["rows"][name]["keys"]
        keys_notes.append(
            '  <p data-keys-orphan="%s" data-keys-read="%s">%s</p>'
            % (esc(name), esc(",".join(keys["read"])),
               esc((doc.get("keys_orphan_fmt") or "").format(
                   read=" , ".join(keys["read"]) or doc.get("keys_none", ""),
                   write=" , ".join(keys["write"]) or doc.get("keys_none", "")))))
    for name in proj["key_unresolved"] or [None]:
        if not name:
            keys_notes.append('  <p data-keys-unresolved-absent>%s</p>'
                              % esc(doc.get("keys_unresolved_absent") or ""))
            continue
        keys = proj["rows"][name]["keys"]
        keys_notes.append(
            '  <p data-keys-unresolved="%s" data-keys-symbols="%s">%s</p>'
            % (esc(name), esc(",".join(keys["unresolved"])),
               esc((doc.get("keys_unresolved_fmt") or "").format(
                   symbols=" , ".join(keys["unresolved"])))))
    if proj["key_outside"]:
        keys_notes.append(
            '  <p data-keys-outside="%d">%s</p>'
            % (len(proj["key_outside"]),
               esc((doc.get("keys_outside_fmt") or "").format(
                   n=len(proj["key_outside"]),
                   names=", ".join(proj["key_outside"])))))
    tier_tags = doc.get("tier_tags") or {}
    tier_count_tags = doc.get("tier_count_tags") or {}
    tier_counts_html = "\n".join(
        '  <span class="kc" data-tier-count="%s"><b>%d</b>%s</span>'
        % (tier, proj["tier_counts"][tier], esc(tier_tags.get(tier) or tier))
        for tier in TIERS
    )
    tier_counts_html += (
        '\n  <span class="kc" data-tier-count="cross"><b>%d</b>%s</span>'
        '\n  <span class="kc" data-tier-count="noread"><b>%d</b>%s</span>'
        % (len(proj["tier_cross"]), esc(tier_count_tags.get("cross") or "cross"),
           len(proj["tier_noread"]), esc(tier_count_tags.get("noread") or "noread")))
    tier_notes = []
    for name in proj["tier_cross"] or [None]:
        if not name:
            tier_notes.append('  <p data-tier-cross-absent>%s</p>'
                              % esc(doc.get("tier_cross_absent") or ""))
            continue
        tiers = proj["rows"][name]["tiers"]
        writes = ",".join(expr for expr, _ in tiers["writes"])
        reads = ",".join(expr for expr, _ in tiers["reads"])
        tier_notes.append(
            '  <p data-tier-cross="%s" data-tier-write="%s" data-tier-read="%s" '
            'data-tier-write-expr="%s" data-tier-read-expr="%s">%s</p>'
            % (esc(name), esc(tiers["write_tier"]), esc(tiers["read_tier"]),
               esc(writes), esc(reads),
               esc((doc.get("tier_cross_fmt") or "").format(
                   write=" , ".join(expr for expr, _ in tiers["writes"]) or doc.get("keys_none", ""),
                   read=" , ".join(expr for expr, _ in tiers["reads"]) or doc.get("keys_none", ""),
                   wt=tier_tag(doc, tiers["write_tier"]),
                   rt=tier_tag(doc, tiers["read_tier"])))))
    tiers_block = ('  <p class="kindshead">%s</p>\n  <div class="counts kinds">\n%s\n'
                   '  </div>\n  <div class="legend tiers">\n%s\n  </div>'
                   % (esc(doc.get("tiers_head", "")), tier_counts_html,
                      "\n".join(tier_notes)))
    keys_block = ('  <p class="kindshead">%s</p>\n  <div class="counts kinds">\n%s\n'
                  '  </div>\n  <div class="legend keys">\n%s\n  </div>\n%s'
                  % (esc(doc.get("keys_head", "")), key_counts_html,
                     "\n".join(keys_notes), tiers_block))
    if proj["missing"]:
        items = "\n".join(
            '    <li data-ceo-item="%s"><b>%s</b> &mdash; %s</li>'
            % (esc(row["id"]), esc(row["label"]), esc(row["how"]))
            for row in proj["missing"]
        )
        missing_block = ('  <p>%s</p>\n  <ul>\n%s\n  </ul>\n  <p>%s</p>'
                         % (esc(doc["missing_head_fmt"].format(n=len(proj["missing"]))),
                            items, esc(doc["missing_tail"])))
    else:
        missing_block = "  <p>%s</p>" % esc(doc["missing_absent"])
    notices = "\n".join(
        '  <p data-notice="%s">%s</p>' % (key, esc(doc["notices"][key]))
        for key in ("aigc", "advice", "mock")
    )
    return (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>%s</title>\n<style>\n"
        ":root{--ink:#182033;--muted:#6b7280;--line:#e5e7eb;--accent:#3b5bdb;--warn:#e8590c;}\n"
        "*{box-sizing:border-box;margin:0;padding:0}\n"
        'body{font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;color:var(--ink);'
        "background:#f7f8fa;line-height:1.65;padding:0 0 48px}\n"
        ".wrap{max-width:900px;margin:0 auto;padding:0 20px}\n"
        "header{background:linear-gradient(135deg,#1f2b4d,#3b5bdb);color:#fff;padding:34px 0 26px}\n"
        "header h1{font-size:26px;letter-spacing:1px}\n"
        "header .sub{margin-top:8px;font-size:14px;opacity:.94}\n"
        ".counts{margin-top:16px;display:flex;gap:10px;flex-wrap:wrap}\n"
        ".count{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.5);"
        "border-radius:8px;padding:8px 14px;font-size:13px}\n"
        ".count b{font-size:20px;margin-right:6px}\n"
        ".kindshead{margin-top:14px;font-size:13px;opacity:.94}\n"
        ".kc{display:inline-block;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.4);"
        "border-radius:6px;padding:4px 10px;font-size:12px;margin:4px 6px 0 0}\n"
        ".kc b{font-size:15px;margin-right:5px}\n"
        ".legend{background:#eef2ff;border:1px solid #c7d2fe;border-radius:8px;padding:10px 14px;"
        "font-size:13px;margin-bottom:12px}\n"
        ".legend p{margin:3px 0}\n"
        ".kbadge{display:inline-block;background:#e7f5ff;border:1px solid #a5d8ff;color:#1864ab;"
        "border-radius:999px;padding:1px 10px;font-size:11px}\n"
        ".kindline{margin:2px 0 6px}\n"
        ".keyline{font-size:12px;color:#1864ab;margin:0 0 6px}\n"
        ".tierline{font-size:12px;color:#5f3dc4;margin:0 0 6px}\n"
        ".legend.keys{background:#f1f8ff;border-color:#a5d8ff}\n"
        ".legend.tiers{background:#f3f0ff;border-color:#d0bfff}\n"
        "h2{font-size:18px;margin:32px 0 12px;padding-left:10px;border-left:4px solid var(--accent)}\n"
        ".face{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 16px;"
        "margin-bottom:12px}\n"
        ".face h3{font-size:16px;margin-bottom:4px}\n"
        ".face h3 code{font-size:12px;color:var(--muted);font-weight:400;margin-left:6px}\n"
        ".face .tagline{font-size:12px;color:var(--accent);margin-bottom:6px}\n"
        ".face .limit{color:var(--warn);font-size:13px}\n"
        ".face p{font-size:13px;margin:4px 0}\n"
        ".face b{font-size:12px;color:var(--muted);display:block}\n"
        ".go{display:inline-block;background:var(--accent);color:#fff;text-decoration:none;"
        "border-radius:6px;padding:4px 12px;font-size:13px}\n"
        "a{color:var(--accent)}\n"
        ".missing{background:#fde8ef;border:1px solid #f4b8cc;border-radius:8px;padding:14px 16px}\n"
        ".missing ul{padding-left:20px;margin:8px 0}\n"
        ".missing li{font-size:13px;margin:4px 0}\n"
        ".notices{background:#fffbe6;border:1px solid #ffe58f;border-radius:8px;padding:12px 16px;"
        "font-size:13px}\n"
        ".notices p{margin:4px 0}\n"
        "footer{margin-top:32px;font-size:12px;color:var(--muted);border-top:1px solid var(--line);"
        "padding-top:12px}\n"
        "code{background:#eef1f6;border-radius:3px;padding:1px 5px;font-size:12px}\n"
        "</style>\n</head>\n<body>\n"
        "<header><div class=\"wrap\">\n"
        "  <h1>%s</h1>\n"
        "  <div class=\"sub\">%s</div>\n"
        "  <div class=\"counts\">"
        "<span class=\"count\"><b data-count=\"faces\">%d</b>%s</span>"
        "<span class=\"count\"><b data-count=\"operable\">%d</b>%s</span>"
        "</div>\n"
        "  <p class=\"kindshead\">%s</p>\n"
        "  <div class=\"counts kinds\">\n%s\n  </div>\n"
        "%s\n"
        "</div></header>\n<div class=\"wrap\">\n"
        "<h2>%s</h2>\n<div class=\"legend\">\n%s\n</div>\n%s\n"
        "<h2>%s</h2>\n<div class=\"missing\">\n%s\n</div>\n"
        "<h2>%s</h2>\n<div class=\"notices\">\n%s\n</div>\n"
        "<footer>%s</footer>\n"
        "</div>\n</body>\n</html>\n"
    ) % (
        esc(doc["title"]),
        esc(doc["h1"]), esc(sub),
        proj["faces_total"], esc(doc.get("count_faces", "")),
        len(proj["operable"]), esc(doc.get("count_operable", "")),
        esc(doc.get("kind_counts_head", "")), kind_counts, keys_block,
        esc(doc["h2_can"].format(operable=len(proj["operable"]))), legend_block, "\n".join(cards),
        esc(doc["h2_cannot"]), missing_block,
        esc(doc["h2_rule"]), notices,
        "sources: state/start-here-faces.json %s / state/merchant-onboard-items.json via "
        "tools/merchant_onboard.project_items()" % proj["data16"],
    )


def write():
    proj = projection()
    html = render(proj)
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
    snapshot = {
        "face": "start-here",
        "generated_from": {
            "state/start-here-faces.json": proj["data16"],
        },
        "faces_total": proj["faces_total"],
        "operable": proj["operable"],
        "kinds": {name: proj["rows"][name]["kind"] for name in proj["operable"]},
        "kind_counts": proj["kind_counts"],
        "tier_counts": proj["tier_counts"],
        "tier_cross": proj["tier_cross"],
        "missing_ceo_items": [row["id"] for row in proj["missing"]],
        "sizes": {"html_bytes": len(html.encode("utf-8"))},
    }
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(snapshot, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("WROTE %s html=%dB operable=%d faces=%d missing=%d"
          % (os.path.relpath(OUT_HTML, ROOT), len(html.encode("utf-8")),
             len(proj["operable"]), proj["faces_total"], len(proj["missing"])))
    return 0


def check():
    proj = projection()
    failures = []
    if not os.path.exists(OUT_HTML):
        print("VERDICT FAIL reason=page_missing")
        return 2
    with open(OUT_HTML, encoding="utf-8") as fh:
        text = fh.read()

    # AC-SH1: the two counters on the page equal a fresh scan of preview/
    for key, want in (("faces", proj["faces_total"]), ("operable", len(proj["operable"]))):
        got = re.search(r'data-count="%s">(\d+)<' % key, text)
        if not got or int(got.group(1)) != want:
            failures.append("SH1 count:%s page=%s fresh=%d"
                            % (key, got.group(1) if got else "absent", want))

    # AC-SH2: listed faces == fresh operable set, every link resolves, zero external refs
    listed = set(re.findall(r'data-face="([^"]+)"', text))
    if listed != set(proj["operable"]):
        failures.append("SH2 listed=%s fresh=%s" % (sorted(listed), sorted(proj["operable"])))
    for href in HREF.findall(text):
        if not os.path.exists(os.path.join(PREVIEW, href)):
            failures.append("SH2 dead_link=%s" % href)
    if EXT.search(text):
        failures.append("SH2 external_ref_present")

    # AC-SH3: every operable face still has label/can/cannot in the data file
    for gap in proj["gaps"]:
        failures.append("SH3 " + gap)

    # AC-SH4: the blocked list carries every missing CEO item, by id
    want_ids = {row["id"] for row in proj["missing"]}
    got_ids = set(re.findall(r'data-ceo-item="([^"]+)"', text))
    if want_ids != got_ids:
        failures.append("SH4 ceo_items page=%s fresh=%s" % (sorted(got_ids), sorted(want_ids)))

    # AC-SH5: the three standing notices are verbatim on the page
    for key in ("aigc", "advice", "mock"):
        if esc(proj["doc"]["notices"][key]) not in text:
            failures.append("SH5 notice_missing=%s" % key)

    # AC-SH6: the page must be the current render of the current data (no self-proof)
    if text != render(proj):
        failures.append("SH6 page_out_of_date")

    # AC-SH7: every face's badge equals the kind derived from that face's own bytes this
    # run, and the data file may not carry a hand-authored kind (a written kind would
    # only be graded for drift, never for being true).
    for name in proj["operable"]:
        want = proj["rows"][name]["kind"]
        block = re.search(r'data-face="%s".*?</article>' % re.escape(name), text, re.S)
        got = re.search(r'data-kind="([^"]+)"', block.group(0)) if block else None
        if not got or got.group(1) != want:
            failures.append("SH7 kind:%s page=%s fresh=%s"
                            % (name, got.group(1) if got else "absent", want))
        elif esc(kind_tag(proj["doc"], want)) not in block.group(0):
            failures.append("SH7 badge_text:%s kind=%s" % (name, want))
    for name in proj["hand_written"]:
        failures.append("SH7 hand_written_kind:%s" % name)

    # AC-SH8: the per-kind counters equal a fresh reading, they sum to the operable
    # count, and a kind with none in it says so in words instead of printing nothing.
    printed = {}
    for kind in KINDS:
        got = re.search(r'data-kind-count="%s"><b>(\d+)</b>' % kind, text)
        printed[kind] = int(got.group(1)) if got else None
        if printed[kind] != proj["kind_counts"][kind]:
            failures.append("SH8 count:%s page=%s fresh=%d"
                            % (kind, printed[kind], proj["kind_counts"][kind]))
    if sum(v for v in printed.values() if v is not None) != len(proj["operable"]):
        failures.append("SH8 sum=%s operable=%d"
                        % (sum(v for v in printed.values() if v is not None),
                           len(proj["operable"])))
    for kind in KINDS:
        if proj["kind_counts"][kind] == 0 and not re.search(
                r'data-kind-absent="%s"' % kind, text):
            failures.append("SH8 absent_line_missing:%s" % kind)
    # A tag or note a kind cannot read is named, never a crash and never silence.
    for kind in KINDS:
        if not (proj["doc"].get("kind_tags") or {}).get(kind):
            failures.append("SH8 kind_tag_missing:%s" % kind)
        if proj["kind_counts"][kind] and not (proj["doc"].get("kind_notes") or {}).get(kind):
            failures.append("SH8 kind_note_missing:%s" % kind)

    # AC-SH9: every operable storage face prints its own key pairing, and every printed
    # number equals a fresh reading of THAT face's bytes this run.
    for name in proj["key_faces"]:
        keys = proj["rows"][name]["keys"]
        block = re.search(r'data-keys="%s"[^>]*>' % re.escape(name), text)
        if not block:
            failures.append("SH9 keys_line_missing:%s" % name)
            continue
        line = block.group(0)
        want = (len(keys["write"]), len(keys["read"]),
                "paired" if keys["base_paired"] else "orphan")
        got = (re.search(r'data-keys-write="(\d+)"', line),
               re.search(r'data-keys-read="(\d+)"', line),
               re.search(r'data-keys-base="([^"]+)"', line))
        printed = tuple(int(m.group(1)) if m and i < 2 else (m.group(1) if m else None)
                        for i, m in enumerate(got))
        if printed != want:
            failures.append("SH9 keys:%s page=%s fresh=%s" % (name, printed, want))
    for key in ("persists", "expr_paired", "base_paired", "orphan", "unresolved",
                "outside"):
        got = re.search(r'data-keys-count="%s"><b>(\d+)</b>' % key, text)
        value = int(got.group(1)) if got else None
        if value != proj["key_counts"][key]:
            failures.append("SH9 count:%s page=%s fresh=%d"
                            % (key, value, proj["key_counts"][key]))
    if not (proj["doc"].get("keys_head") or "").strip():
        failures.append("SH9 keys_head_missing")

    # AC-SH10: a face that reads a key it never writes, and a face keying on a symbol it
    # never declares, must be NAMED on the page - and a face that is neither may not be
    # listed (no crying wolf while the honest answer is "none today").
    for name in proj["key_orphans"]:
        if not re.search(r'data-keys-orphan="%s"' % re.escape(name), text):
            failures.append("SH10 orphan_unnamed:%s" % name)
    for name in proj["key_unresolved"]:
        if not re.search(r'data-keys-unresolved="%s"' % re.escape(name), text):
            failures.append("SH10 unresolved_unnamed:%s" % name)
    if not proj["key_orphans"] and "data-keys-orphan-absent" not in text:
        failures.append("SH10 orphan_absent_line_missing")
    if not proj["key_unresolved"] and "data-keys-unresolved-absent" not in text:
        failures.append("SH10 unresolved_absent_line_missing")
    listed_orphans = set(re.findall(r'data-keys-orphan="([^"]+)"', text))
    if listed_orphans != set(proj["key_orphans"]):
        failures.append("SH10 orphan_list page=%s fresh=%s"
                        % (sorted(listed_orphans), sorted(proj["key_orphans"])))
    listed_unresolved = set(re.findall(r'data-keys-unresolved="([^"]+)"', text))
    if listed_unresolved != set(proj["key_unresolved"]):
        failures.append("SH10 unresolved_list page=%s fresh=%s"
                        % (sorted(listed_unresolved), sorted(proj["key_unresolved"])))
    # The named line must carry the SAME expressions the fresh reading found, so a line
    # that names the right face while quoting the wrong key still reddens.
    for name in proj["key_orphans"]:
        keys = proj["rows"][name]["keys"]
        got = re.search(r'data-keys-orphan="%s" data-keys-read="([^"]*)"'
                        % re.escape(name), text)
        if not got or got.group(1) != esc(",".join(keys["read"])):
            failures.append("SH10 orphan_keys:%s page=%s fresh=%s"
                            % (name, got.group(1) if got else "absent",
                               ",".join(keys["read"])))
    for name in proj["key_unresolved"]:
        keys = proj["rows"][name]["keys"]
        got = re.search(r'data-keys-unresolved="%s" data-keys-symbols="([^"]*)"'
                        % re.escape(name), text)
        if not got or got.group(1) != esc(",".join(keys["unresolved"])):
            failures.append("SH10 unresolved_symbols:%s page=%s fresh=%s"
                            % (name, got.group(1) if got else "absent",
                               ",".join(keys["unresolved"])))
    if proj["key_outside"]:
        got = re.search(r'data-keys-outside="(\d+)"', text)
        if not got or int(got.group(1)) != len(proj["key_outside"]):
            failures.append("SH10 outside page=%s fresh=%d"
                            % (got.group(1) if got else "absent",
                               len(proj["key_outside"])))

    # AC-SH11: every operable storage face prints where the variable part of its key
    # comes from, and every tier counter equals a fresh reading of the same faces.
    for name in proj["key_faces"]:
        tiers = proj["rows"][name]["tiers"]
        got = re.search(r'data-tiers="%s" data-tiers-write="([^"]*)" '
                        r'data-tiers-read="([^"]*)" data-tiers-same="([^"]*)"'
                        % re.escape(name), text)
        want = (tiers["write_tier"] or "", tiers["read_tier"] or "", tiers["same"])
        if not got:
            failures.append("SH11 tiers_line_missing:%s" % name)
        elif got.groups() != want:
            failures.append("SH11 tiers:%s page=%s fresh=%s" % (name, got.groups(), want))
    for tier in TIERS:
        got = re.search(r'data-tier-count="%s"><b>(\d+)</b>' % tier, text)
        value = int(got.group(1)) if got else None
        if value != proj["tier_counts"][tier]:
            failures.append("SH11 count:%s page=%s fresh=%d"
                            % (tier, value, proj["tier_counts"][tier]))
        if not (proj["doc"].get("tier_tags") or {}).get(tier):
            failures.append("SH11 tier_tag_missing:%s" % tier)
    for key, want in (("cross", len(proj["tier_cross"])),
                      ("noread", len(proj["tier_noread"]))):
        got = re.search(r'data-tier-count="%s"><b>(\d+)</b>' % key, text)
        value = int(got.group(1)) if got else None
        if value != want:
            failures.append("SH11 count:%s page=%s fresh=%d" % (key, value, want))
    nowrite = [n for n in proj["key_faces"] if not proj["rows"][n]["tiers"]["write_tier"]]
    if sum(proj["tier_counts"].values()) + len(nowrite) != len(proj["key_faces"]):
        failures.append("SH11 sum=%d nowrite=%d faces=%d"
                        % (sum(proj["tier_counts"].values()), len(nowrite),
                           len(proj["key_faces"])))

    # AC-SH12: a face whose write and read take their variable part from different
    # places must be NAMED with both tiers and both expressions; a same-tier face may
    # not be listed as cross (no crying wolf), and none today prints so in words.
    listed_cross = set(re.findall(r'data-tier-cross="([^"]+)"', text))
    if listed_cross != set(proj["tier_cross"]):
        failures.append("SH12 cross_list page=%s fresh=%s"
                        % (sorted(listed_cross), sorted(proj["tier_cross"])))
    if not proj["tier_cross"] and "data-tier-cross-absent" not in text:
        failures.append("SH12 absent_line_missing")
    for name in proj["tier_cross"]:
        tiers = proj["rows"][name]["tiers"]
        got = re.search(r'data-tier-cross="%s" data-tier-write="([^"]*)" '
                        r'data-tier-read="([^"]*)" data-tier-write-expr="([^"]*)" '
                        r'data-tier-read-expr="([^"]*)"' % re.escape(name), text)
        want = (tiers["write_tier"], tiers["read_tier"],
                esc(",".join(expr for expr, _ in tiers["writes"])),
                esc(",".join(expr for expr, _ in tiers["reads"])))
        if not got or got.groups() != want:
            failures.append("SH12 cross:%s page=%s fresh=%s"
                            % (name, got.groups() if got else "absent", want))

    if failures:
        for line in failures:
            print("  FAIL " + line)
        print("VERDICT FAIL criteria=12 failures=%d" % len(failures))
        return 2
    print("VERDICT PASS criteria=12 faces=%d operable=%d missing_ceo=%d external_refs=0 "
          "kinds=%s keys=%s tiers=%s"
          % (proj["faces_total"], len(proj["operable"]), len(proj["missing"]),
             ",".join("%s:%d" % (kind, proj["kind_counts"][kind]) for kind in KINDS),
             ",".join("%s:%d" % (key, proj["key_counts"][key])
                      for key in ("persists", "expr_paired", "base_paired",
                                  "orphan", "unresolved", "outside")),
             ",".join("%s:%d" % (tier, proj["tier_counts"][tier]) for tier in TIERS)
             + ",cross:%d,noread:%d" % (len(proj["tier_cross"]), len(proj["tier_noread"]))))
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--write"]:
        return write()
    if argv[:1] == ["--check"]:
        return check()
    print(__doc__.strip().splitlines()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
