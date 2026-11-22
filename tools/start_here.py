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


# The tier says where the variable part comes from; it does not say the two sides name
# the SAME attribute. A face writing NS+':'+this.getAttribute('data-ck') and reading
# NS+':'+kk (kk = T[n].getAttribute('data-ck')) draws both sides from one attribute
# name - and a copy that renamed either side would still read dom/dom. The name lives
# in the raw bytes only, because key_reading blanked every string literal.
ATTR_GET = re.compile(r"getAttribute\s*\(\s*(?:'([^']*)'|\"([^\"]*)\"|([A-Za-z_$][\w$]*))")
RAW_ASSIGN = re.compile(r"(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*([^;]{0,240})")
ATTR_NONE = "none"
ATTR_VERDICTS = ("same-name", "different", "one-side", "no-attr", "unknown")


def _blank_strings(text):
    """Blank string literals in place so offsets still line up with the raw bytes: a
    call is located on the blanked copy and its argument sliced from the raw copy."""
    def swap(match):
        body = match.group(0)
        return body[0] + " " * (len(body) - 2) + body[-1]

    return STR.sub(swap, text)


def _attr_tokens(expr):
    """Attribute names a RAW expression names, plus how many getAttribute calls take a
    variable argument (those are not guessed)."""
    names, unknown = set(), 0
    for match in ATTR_GET.finditer(expr):
        literal = match.group(1) if match.group(1) is not None else match.group(2)
        if literal:
            names.add(literal)
        else:
            unknown += 1
    return names, unknown


def _attr_names(raw, blanked, expr, hops=1):
    """Attribute names one side rests on, one hop through declared names. Identifiers
    are followed but never reported as attributes."""
    names, unknown = _attr_tokens(expr)
    frontier = set(_key_symbols(expr))
    visited = set(frontier)
    for _ in range(hops):
        nxt = set()
        for name in sorted(frontier):
            for match in RAW_ASSIGN.finditer(blanked):
                if match.group(1) != name:
                    continue
                rhs = raw[match.start(2):match.start(2) + len(match.group(2))]
                got, bad = _attr_tokens(rhs)
                names |= got
                unknown += bad
                nxt |= set(_key_symbols(rhs))
                break
        frontier = nxt - visited
        visited |= nxt
    return names, unknown


def _attr_sides(raw, blanked):
    """The storage key argument as written, per side (strings intact)."""
    sides = {"setItem": [], "getItem": []}
    for match in CALL.finditer(blanked):
        kind = match.group(1)
        if kind not in sides:
            continue
        arg = _first_arg(raw, match.end() - 1)
        if arg.strip():
            sides[kind].append(arg)
    return sides


def attr_reading(text, keys=None):
    """Whether the two sides of a storage key name the same DOM attribute. Text only:
    the attribute name is compared, the element identity is NOT decided here."""
    keys = keys or key_reading(text)
    blanked = _blank_strings(text)
    sides = _attr_sides(text, blanked)
    write, w_bad = set(), 0
    read, r_bad = set(), 0
    for expr in sides["setItem"]:
        got, bad = _attr_names(text, blanked, expr)
        write |= got
        w_bad += bad
    for expr in sides["getItem"]:
        got, bad = _attr_names(text, blanked, expr)
        read |= got
        r_bad += bad
    shared = sorted(write & read)
    if w_bad or r_bad:
        verdict = "unknown"
    elif write and read:
        verdict = "same-name" if shared else "different"
    elif write or read:
        verdict = "one-side"
    else:
        verdict = "no-attr"
    return {"write": sorted(write), "read": sorted(read), "shared": shared,
            "unknown": w_bad + r_bad, "verdict": verdict}


# A shared attribute name is not a shared element: money-path-demo writes
# this.getAttribute('data-ck') and reads T[n].getAttribute('data-ck'), which the name
# column can only call same-name. The element a read sits on IS derivable from the
# bytes in three ways - a direct X.getAttribute(...) names X, a `this` inside
# TARGET.onX = function(){...} is TARGET, and a name bound to an attribute read takes
# that right-hand side's host. Comparing host EXPRESSIONS is still text, not identity.
H_ASSIGN = re.compile(r"([A-Za-z_$][\w$]*\s*(?:\[[^\]]*\])?)\s*\.\s*(on[a-z]+)"
                      r"\s*=\s*function\s*\(")
H_ADDL = re.compile(r"([A-Za-z_$][\w$]*\s*(?:\[[^\]]*\])?)\s*\.\s*addEventListener"
                    r"\s*\(\s*['\"][^'\"]*['\"]\s*,\s*function\s*\(")
A_HOST = re.compile(r"([A-Za-z_$][\w$]*\s*(?:\[[^\]]*\])?)\s*\.\s*getAttribute\s*\(")
THIS_GET = re.compile(r"\bthis\s*\.\s*getAttribute\s*\(")
HOST_NONE = "none"
HOST_VERDICTS = ("same-host", "different-host", "one-side", "no-host", "unknown",
                 "lexical")

# An arrow's `this` is lexical: it belongs to the nearest enclosing NON-arrow
# function, and if the chain above it holds no function literal it belongs to no
# element at all (module scope is undefined, a classic script is window). So an
# arrow body can never be read as the assignment target - the R3257 reader happened
# to be safe here only because it demanded the literal `= function(`, which also
# made a lexical `this` indistinguishable from a `this` it simply could not place.
ARROW = re.compile(r"=>")
TGT_ASSIGN = re.compile(r"([A-Za-z_$][\w$]*\s*(?:\[[^\]]*\])?)\s*\.\s*(on[a-z]+)\s*=\s*$")
TGT_ADDL = re.compile(r"([A-Za-z_$][\w$]*\s*(?:\[[^\]]*\])?)\s*\.\s*addEventListener"
                      r"\s*\(\s*['\"][^'\"]*['\"]\s*,\s*$")
FUNC_KIND = "function"
ARROW_KIND = "arrow"

# A handler is not always a literal body on a literal element. Two live forms were
# silent: a call-expression receiver ($('reset').addEventListener('click', function))
# and a named callback (boxes[i].addEventListener('change', onToggle)). A named
# callback supplies that element as `this` only when the face declares `function NAME(`
# exactly once, binds the name to ONE target expression, and never calls it directly -
# at a direct call `this` is not the element. All of it is text, never executed.
RECV_ATOM = r"[A-Za-z_$][\w$]*(?:\s*\([^()]*\))?(?:\s*\[[^\]]*\])?"
RECV_EXPR = RECV_ATOM + r"(?:\s*\.\s*" + RECV_ATOM + r")*"
CALL_RECV = (r"[A-Za-z_$][\w$]*\s*\([^()]*\)(?:\s*\[[^\]]*\])?"
             r"(?:\s*\.\s*" + RECV_ATOM + r")*")
H_ADDL_CALL = re.compile(r"(" + CALL_RECV + r")\s*\.\s*addEventListener\s*\("
                         r"\s*['\"][^'\"]*['\"]\s*,\s*function\s*\(")
H_ADDL_NAME = re.compile(r"(" + RECV_EXPR + r")\s*\.\s*addEventListener\s*\("
                         r"\s*['\"][^'\"]*['\"]\s*,\s*([A-Za-z_$][\w$]*)\s*\)")
FUNC_DECL = re.compile(r"function\s+([A-Za-z_$][\w$]*)\s*\(")
# R3260: `function NAME(` is one way to declare a callback, not the only one. A
# var/let/const bound to a function literal is the SAME weight - its body is a function
# literal, so the binding target supplies `this`. One bound to an arrow is a
# declaration of a DIFFERENT weight: an arrow's `this` is lexical (R3258) and can never
# be read as the element. All three forms count toward "declared exactly once", because
# `function upd(` PLUS `var upd = function(` is two declarations - and R3259 resolved
# that pair as one, since it only counted the first form.
DECL_VARFUNC = re.compile(r"\b(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*function\s*\(")
DECL_ARROW = re.compile(r"\b(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*"
                        r"(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>")
DECL_FORMS = ("func", "varfunc", "arrow", "mixed", "none")
CALL_NAME = re.compile(r"([A-Za-z_$][\w$]*)\s*\(")
H_SITE = re.compile(r"(" + RECV_EXPR + r")\s*\.\s*addEventListener\s*\("
                    r"\s*['\"][^'\"]*['\"]\s*,\s*([^)]{0,64})")
H_ONX_SITE = re.compile(r"(" + RECV_EXPR + r")\s*\.\s*(on[a-z]+)\s*=\s*([^;]{0,64})")
ATTR_SITE = re.compile(r"<[^>]+\son(?:click|change|input|submit|keyup|keydown)\s*=")
HANDLER_FORMS = ("simple", "call", "named", "attr")
NAMED_REASONS = ("called", "nodecl", "twodecl", "twotarget", "lexical", "nobody")


def _decl_index(blanked):
    """Every declaration of a name, by FORM, with where a body scan starts: the
    parameter paren for `function NAME(` and for a var/let/const bound to a function
    literal, the arrow itself for one bound to an arrow. A face that declares one name
    twice - in the same form or across forms - is ambiguous, which is what makes a
    lookup here a count and not a flag."""
    out = {}
    for match in FUNC_DECL.finditer(blanked):
        out.setdefault(match.group(1), []).append(("func", match.end() - 1))
    for match in DECL_VARFUNC.finditer(blanked):
        out.setdefault(match.group(1), []).append(("varfunc", match.end() - 1))
    for match in DECL_ARROW.finditer(blanked):
        out.setdefault(match.group(1), []).append(("arrow", match.end()))
    return out


def _body_span(text, frm):
    """The braces of the function literal starting at or after frm."""
    i = text.find("{", frm)
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return (i, j)
    return None


def _raw_slice(raw, blanked, start, end):
    """The text at [start,end) from the RAW copy when one is given: a receiver such as
    $('reset') must not be printed as $('') just because strings are blanked for
    matching. Blanking preserves offsets, so the slice is exact."""
    text = raw if raw is not None else blanked
    return text[start:end].replace(" ", "")


def _handler_spans(blanked, raw=None):
    """Every handler literal in the page: body start/end, the target it is assigned
    to, the form, and whether its body is a `function` or an arrow. Only literal
    forms with a brace body are recognised; anything else stays silence."""
    spans = []
    for match in H_ASSIGN.finditer(blanked):
        got = _body_span(blanked, match.end())
        if got:
            spans.append((got[0], got[1],
                          _raw_slice(raw, blanked, match.start(1), match.end(1)),
                          match.group(2), FUNC_KIND))
    for match in H_ADDL.finditer(blanked):
        got = _body_span(blanked, match.end())
        if got:
            spans.append((got[0], got[1],
                          _raw_slice(raw, blanked, match.start(1), match.end(1)),
                          "addEventListener", FUNC_KIND))
    for match in H_ADDL_CALL.finditer(blanked):
        got = _body_span(blanked, match.end())
        if got:
            spans.append((got[0], got[1],
                          _raw_slice(raw, blanked, match.start(1), match.end(1)),
                          "addEventListener", FUNC_KIND))
    spans.extend(_arrow_spans(blanked))
    named, _ = _named_spans(blanked, raw)
    spans.extend(named)
    return spans


def _named_report(blanked, raw=None):
    """Per named callback bound as a listener: whether its declaration body can stand
    for the binding target, which form declared it, or the closed-set reason it cannot.
    An arrow declaration is named `lexical` rather than resolved: its `this` is not the
    element even though the declaration itself is unambiguous."""
    bindings = {}
    for match in H_ADDL_NAME.finditer(blanked):
        bindings.setdefault(match.group(2), []).append(
            _raw_slice(raw, blanked, match.start(1), match.end(1)))
    decls = _decl_index(blanked)
    direct = set()
    for match in CALL_NAME.finditer(blanked):
        before = blanked[max(0, match.start() - 12):match.start()]
        if not re.search(r"function\s+$", before):
            direct.add(match.group(1))
    out = {}
    for name, targets in bindings.items():
        inner = sorted(set(targets))
        got = decls.get(name) or []
        forms = sorted(set(form for form, _ in got))
        form = "none" if not got else (forms[0] if len(forms) == 1 and
                                       len(got) == 1 else "mixed")
        if name in direct:
            status = "called"
        elif not got:
            status = "nodecl"
        elif len(got) > 1:
            status = "twodecl"
        elif len(inner) > 1:
            status = "twotarget"
        elif got[0][0] == "arrow":
            status = "lexical"
        else:
            status = "resolved"
        out[name] = {"status": status, "targets": inner, "form": form}
    return out


def _named_spans(blanked, raw=None):
    """Named callbacks resolved one hop, with the report that says why a name was not
    resolved. A direct call anywhere in the same face disqualifies the name, because
    `this` at that call is not the element it was bound to."""
    spans = []
    report = _named_report(blanked, raw)
    decls = _decl_index(blanked)
    for name, got in list(report.items()):
        if got["status"] != "resolved":
            continue
        body = _body_span(blanked, decls[name][0][1])
        if not body:
            got["status"] = "nobody"
            continue
        spans.append((body[0], body[1], got["targets"][0], "named", FUNC_KIND))
    return spans, report


def _recv_form(recv):
    """A receiver that starts with a call (`$('reset')`, `document.getElementById('x')`)
    is a call expression; everything else RECV_EXPR accepts is an element expression."""
    if re.match(r"^[A-Za-z_$][\w$]*\s*\(", (recv or "").strip()):
        return "call"
    return "simple"


def handler_census(text):
    """How each handler site in one face is BOUND: a simple element expression, a call
    expression, a named callback, or an inline string attribute. Text only - a name in
    the named bucket is resolved (or refused) by _named_report, not guessed."""
    blanked = _blank_strings(text)
    forms = {form: 0 for form in HANDLER_FORMS}
    calls, names = [], []
    for match in H_SITE.finditer(blanked):
        recv = _raw_slice(text, blanked, match.start(1), match.end(1))
        cb = match.group(2).strip()
        if re.match(r"^[A-Za-z_$][\w$]*$", cb):
            forms["named"] += 1
            continue
        form = _recv_form(recv)
        forms[form] += 1
        if form == "call":
            calls.append(recv)
    for match in H_ONX_SITE.finditer(blanked):
        recv = _raw_slice(text, blanked, match.start(1), match.end(1))
        cb = match.group(3).strip()
        if cb.startswith("function") or "=>" in cb[:20]:
            form = _recv_form(recv)
            forms[form] += 1
            if form == "call":
                calls.append(recv)
        elif re.match(r"^[A-Za-z_$][\w$]*$", cb):
            forms["named"] += 1
    forms["attr"] += len(ATTR_SITE.findall(text))
    report = _named_report(blanked, text)
    for name in sorted(report):
        names.append((name, report[name]["status"], report[name]["targets"],
                      report[name]["form"]))
    return {"forms": forms, "calls": sorted(set(calls)), "named": names,
            "sites": sum(forms.values())}


def _arrow_target(head):
    """The element expression an arrow literal is bound to, if the bytes say so."""
    h = head.rstrip()
    if h.endswith(")"):
        depth = 0
        for k in range(len(h) - 1, -1, -1):
            if h[k] == ")":
                depth += 1
            elif h[k] == "(":
                depth -= 1
                if depth == 0:
                    h = h[:k]
                    break
    else:
        ident = re.findall(r"[A-Za-z_$][\w$]*$", h)
        if ident:
            h = h[:len(h) - len(ident[0])]
    for pat in (TGT_ASSIGN, TGT_ADDL):
        match = pat.search(h)
        if match:
            return match.group(1).replace(" ", "")
    return None


def _arrow_spans(blanked):
    """Brace-bodied arrows anywhere in the page. A bare `var go = () => {` is a span
    too - its target is None, and a lexical `this` inside it still is not an element.
    An expression body (`e => expr`) is not a span: the brace that follows belongs to
    something else, so it falls to unknown instead of being guessed."""
    out = []
    for match in ARROW.finditer(blanked):
        tail = blanked[match.end():match.end() + 8]
        i = match.end() + (len(tail) - len(tail.lstrip()))
        if i >= len(blanked) or blanked[i] != "{":
            continue
        got = _body_span(blanked, i)
        if not got:
            continue
        head = blanked[max(0, match.start() - 160):match.start()]
        out.append((got[0], got[1], _arrow_target(head), "arrow", ARROW_KIND))
    return out


def _resolve_this(at, spans):
    """(host, lexical) for a `this` read at offset at.

    Nearest enclosing function literal wins - an arrow in between does not change
    whose `this` it is, which is why an arrow nested in a handler still reads that
    handler's target. If the enclosing chain is arrows only, the value is lexical and
    no element is claimed; if nothing encloses it, nothing is claimed either."""
    inside = [s for s in spans if s[0] <= at <= s[1]]
    if not inside:
        return None, False
    for span in sorted(inside, key=lambda s: s[0], reverse=True):
        if span[4] == FUNC_KIND:
            return span[2], False
    return None, True


def _sides_pos(raw, blanked):
    """The storage call arguments with their offsets, so a `this` can be tied to the
    handler literal that encloses it."""
    sides = {"setItem": [], "getItem": []}
    for match in CALL.finditer(blanked):
        kind = match.group(1)
        if kind not in sides:
            continue
        open_paren = match.end() - 1
        arg = _first_arg(raw, open_paren)
        if arg.strip():
            sides[kind].append((arg, open_paren + 1))
    return sides


def _side_hosts(raw, blanked, expr, pos, spans):
    """Host expressions the attribute reads of one key side sit on, one hop deep."""
    hosts, unknown, lexical, targets = set(), 0, 0, set()
    for match in A_HOST.finditer(expr):
        # 'this' is not a host name - it is resolved through its enclosing handler.
        # Counting it as a host would make two unresolved sides look equal.
        got = match.group(1).replace(" ", "")
        if got != "this":
            hosts.add(got)
    for match in THIS_GET.finditer(expr):
        host, lex = _resolve_this(pos + match.start(), spans)
        if host:
            hosts.add(host)
        elif lex:
            lexical += 1
            targets.add(_arrow_label(pos + match.start(), spans))
        else:
            unknown += 1
    for name in _key_symbols(expr):
        for decl in RAW_ASSIGN.finditer(blanked):
            if decl.group(1) != name:
                continue
            rhs = raw[decl.start(2):decl.start(2) + len(decl.group(2))]
            for match in A_HOST.finditer(rhs):
                got = match.group(1).replace(" ", "")
                if got != "this":
                    hosts.add(got)
            for match in THIS_GET.finditer(rhs):
                at = decl.start(2) + match.start()
                host, lex = _resolve_this(at, spans)
                if host:
                    hosts.add(host)
                elif lex:
                    lexical += 1
                    targets.add(_arrow_label(at, spans))
                else:
                    unknown += 1
            break
    return hosts, unknown, lexical, targets


def _arrow_label(at, spans):
    """The lexical `this` named by the arrow it sits in: target where one is bound,
    a bare marker where the arrow is not bound to an element."""
    inside = [s for s in spans if s[0] <= at <= s[1] and s[4] == ARROW_KIND]
    if not inside:
        return HOST_NONE
    return sorted(inside, key=lambda s: s[0], reverse=True)[0][2] or "arrow"


def host_reading(text, keys=None):
    """Which element expression each side of a storage key reads an attribute from.
    Text only: two sides naming one expression is not proof of one node at runtime."""
    keys = keys or key_reading(text)
    blanked = _blank_strings(text)
    spans = _handler_spans(blanked, text)
    sides = _sides_pos(text, blanked)
    write, read = set(), set()
    w_bad = r_bad = w_lex = r_lex = 0
    lex_targets = set()
    for expr, pos in sides["setItem"]:
        got, bad, lex, targets = _side_hosts(text, blanked, expr, pos, spans)
        write |= got
        w_bad += bad
        w_lex += lex
        lex_targets |= targets
    for expr, pos in sides["getItem"]:
        got, bad, lex, targets = _side_hosts(text, blanked, expr, pos, spans)
        read |= got
        r_bad += bad
        r_lex += lex
        lex_targets |= targets
    shared = sorted(write & read)
    lexical = w_lex + r_lex
    if w_bad or r_bad:
        verdict = "unknown"
    elif lexical:
        verdict = "lexical"
    elif write and read:
        verdict = "same-host" if shared else "different-host"
    elif write or read:
        verdict = "one-side"
    else:
        verdict = "no-host"
    return {"write": sorted(write), "read": sorted(read), "shared": shared,
            "unknown": w_bad + r_bad, "lexical": lexical,
            "lexical_targets": sorted(lex_targets), "verdict": verdict,
            "handlers": len(spans),
            "bound": len([s for s in spans if s[4] == FUNC_KIND
                          and s[3] != "addEventListener"])}


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
            row["attrs"] = attr_reading(text, row["keys"])
            row["hosts"] = host_reading(text, row["keys"])
            row["forms"] = handler_census(text)
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
    attr_counts = {verdict: 0 for verdict in ATTR_VERDICTS}
    for name in key_faces:
        attr_counts[rows[name]["attrs"]["verdict"]] += 1
    attr_different = [n for n in key_faces
                      if rows[n]["attrs"]["verdict"] == "different"]
    attr_unknown = [n for n in key_faces if rows[n]["attrs"]["verdict"] == "unknown"]
    host_counts = {verdict: 0 for verdict in HOST_VERDICTS}
    for name in key_faces:
        host_counts[rows[name]["hosts"]["verdict"]] += 1
    host_different = [n for n in key_faces
                      if rows[n]["hosts"]["verdict"] == "different-host"]
    host_unknown = [n for n in key_faces
                    if rows[n]["hosts"]["verdict"] == "unknown"]
    host_lexical = [n for n in key_faces
                    if rows[n]["hosts"]["lexical"]]
    host_lexical_calls = sum(rows[n]["hosts"]["lexical"] for n in host_lexical)
    form_counts = {form: 0 for form in HANDLER_FORMS}
    for name in key_faces:
        for form, count in rows[name]["forms"]["forms"].items():
            form_counts[form] += count
    form_calls = [n for n in key_faces if rows[n]["forms"]["calls"]]
    form_named = [n for n in key_faces if rows[n]["forms"]["named"]]
    form_named_open = [n for n in form_named
                       if any(got[1] != "resolved" for got in rows[n]["forms"]["named"])]
    named_decl_counts = {form: 0 for form in DECL_FORMS}
    for name in form_named:
        for got in rows[name]["forms"]["named"]:
            named_decl_counts[got[3]] += 1
    named_total = sum(named_decl_counts.values())
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
        "attr_counts": attr_counts,
        "attr_different": attr_different,
        "attr_unknown": attr_unknown,
        "host_counts": host_counts,
        "host_different": host_different,
        "host_unknown": host_unknown,
        "host_lexical": host_lexical,
        "host_lexical_calls": host_lexical_calls,
        "form_counts": form_counts,
        "form_calls": form_calls,
        "form_named": form_named,
        "form_named_open": form_named_open,
        "named_decl_counts": named_decl_counts,
        "named_total": named_total,
        "form_sites": sum(form_counts.values()),
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


def attr_word(doc, verdict):
    return ((doc.get("attr_words") or {}).get(verdict) or verdict)


def attr_phrase(doc, attrs):
    """One face's attribute names in words. An empty side prints the word for 'none',
    so 'no attribute here' never reads as 'could not tell'."""
    none = doc.get("attrs_none") or ATTR_NONE
    return (doc.get("attrs_fmt") or "").format(
        write=" , ".join(attrs["write"]) or none,
        read=" , ".join(attrs["read"]) or none,
        verdict=attr_word(doc, attrs["verdict"]))


def host_word(doc, verdict):
    return ((doc.get("host_words") or {}).get(verdict) or verdict)


def host_phrase(doc, hosts):
    """One face's host expressions in words, with the unresolved `this` count printed
    instead of hidden when a handler could not be located."""
    none = doc.get("host_none") or HOST_NONE
    return (doc.get("host_fmt") or "").format(
        write=" , ".join(hosts["write"]) or none,
        read=" , ".join(hosts["read"]) or none,
        verdict=host_word(doc, hosts["verdict"]),
        unknown=hosts["unknown"],
        lexical=hosts["lexical"])


def form_word(doc, form):
    return ((doc.get("form_tags") or {}).get(form) or form)


def form_phrase(doc, forms):
    """One face's handler bindings by form. A zero is printed as zero, not hidden."""
    return (doc.get("forms_fmt") or "").format(**{form: forms[form]
                                                  for form in HANDLER_FORMS})


def named_reason(doc, status):
    return ((doc.get("form_reasons") or {}).get(status) or status)


def decl_word(doc, form):
    return ((doc.get("decl_tags") or {}).get(form) or form)


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
        if "attrs" in proj["rows"][name]:
            attrs = proj["rows"][name]["attrs"]
            attrline = ('    <p class="attrline" data-attrs="%s" data-attrs-write="%s" '
                        'data-attrs-read="%s" data-attrs-verdict="%s">%s</p>\n'
                        % (esc(name), esc(",".join(attrs["write"])),
                           esc(",".join(attrs["read"])), esc(attrs["verdict"]),
                           esc(attr_phrase(doc, attrs))))
        else:
            attrline = ""
        if "hosts" in proj["rows"][name]:
            hosts = proj["rows"][name]["hosts"]
            hostline = ('    <p class="hostline" data-hosts="%s" data-hosts-write="%s" '
                        'data-hosts-read="%s" data-hosts-verdict="%s" '
                        'data-hosts-lexical="%d">%s</p>\n'
                        % (esc(name), esc(",".join(hosts["write"])),
                           esc(",".join(hosts["read"])), esc(hosts["verdict"]),
                           hosts["lexical"], esc(host_phrase(doc, hosts))))
        else:
            hostline = ""
        if "forms" in proj["rows"][name]:
            forms = proj["rows"][name]["forms"]["forms"]
            formline = ('    <p class="formline" data-forms="%s" data-forms-simple="%d" '
                        'data-forms-call="%d" data-forms-named="%d" data-forms-attr="%d">%s</p>\n'
                        % (esc(name), forms["simple"], forms["call"], forms["named"],
                           forms["attr"], esc(form_phrase(doc, forms))))
        else:
            formline = ""
        cards.append(
            '  <article class="face" data-face="%s">\n'
            '    <h3><a href="%s">%s</a> <code>%s</code></h3>\n'
            '    <p class="kindline"><span class="kbadge" data-kind="%s">%s</span></p>\n'
            '%s%s%s%s%s'
            '    <p><b>%s</b>%s</p>\n'
            '    <p class="limit"><b>%s</b>%s</p>\n'
            '    <p><a class="go" href="%s">%s &rarr;</a></p>\n'
            '  </article>\n' % (
                esc(name), esc(name), esc(label), esc(name),
                esc(kind), esc(kind_tag(doc, kind)), keyline, tierline, attrline,
                hostline, formline,
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
    attr_tags = doc.get("attr_count_tags") or {}
    attr_counts_html = "\n".join(
        '  <span class="kc" data-attr-count="%s"><b>%d</b>%s</span>'
        % (verdict, proj["attr_counts"][verdict],
           esc(attr_tags.get(verdict) or attr_word(doc, verdict)))
        for verdict in ATTR_VERDICTS
    )
    attr_notes = []
    for name in proj["attr_different"] or [None]:
        if not name:
            attr_notes.append('  <p data-attrs-different-absent>%s</p>'
                              % esc(doc.get("attrs_different_absent") or ""))
            continue
        attrs = proj["rows"][name]["attrs"]
        attr_notes.append(
            '  <p data-attrs-different="%s" data-attrs-write="%s" data-attrs-read="%s">'
            '%s</p>'
            % (esc(name), esc(",".join(attrs["write"])), esc(",".join(attrs["read"])),
               esc((doc.get("attrs_different_fmt") or "").format(
                   write=" , ".join(attrs["write"]) or doc.get("attrs_none", ""),
                   read=" , ".join(attrs["read"]) or doc.get("attrs_none", "")))))
    for name in proj["attr_unknown"] or [None]:
        if not name:
            attr_notes.append('  <p data-attrs-unknown-absent>%s</p>'
                              % esc(doc.get("attrs_unknown_absent") or ""))
            continue
        attrs = proj["rows"][name]["attrs"]
        attr_notes.append(
            '  <p data-attrs-unknown="%s" data-attrs-calls="%d">%s</p>'
            % (esc(name), attrs["unknown"],
               esc((doc.get("attrs_unknown_fmt") or "").format(calls=attrs["unknown"]))))
    attrs_block = ('  <p class="kindshead">%s</p>\n  <div class="counts kinds">\n%s\n'
                   '  </div>\n  <div class="legend attrs">\n%s\n  </div>'
                   % (esc(doc.get("attrs_head", "")), attr_counts_html,
                      "\n".join(attr_notes)))
    host_tags = doc.get("host_count_tags") or {}
    host_counts_html = "\n".join(
        '  <span class="kc" data-host-count="%s"><b>%d</b>%s</span>'
        % (verdict, proj["host_counts"][verdict],
           esc(host_tags.get(verdict) or host_word(doc, verdict)))
        for verdict in HOST_VERDICTS
    )
    host_notes = []
    for name in proj["host_different"] or [None]:
        if not name:
            host_notes.append('  <p data-hosts-different-absent>%s</p>'
                              % esc(doc.get("host_different_absent") or ""))
            continue
        hosts = proj["rows"][name]["hosts"]
        host_notes.append(
            '  <p data-hosts-different="%s" data-hosts-write="%s" data-hosts-read="%s">'
            '%s</p>'
            % (esc(name), esc(",".join(hosts["write"])), esc(",".join(hosts["read"])),
               esc((doc.get("host_different_fmt") or "").format(
                   write=" , ".join(hosts["write"]) or doc.get("host_none", ""),
                   read=" , ".join(hosts["read"]) or doc.get("host_none", "")))))
    for name in proj["host_unknown"] or [None]:
        if not name:
            host_notes.append('  <p data-hosts-unknown-absent>%s</p>'
                              % esc(doc.get("host_unknown_absent") or ""))
            continue
        hosts = proj["rows"][name]["hosts"]
        host_notes.append(
            '  <p data-hosts-unknown="%s" data-hosts-calls="%d">%s</p>'
            % (esc(name), hosts["unknown"],
               esc((doc.get("host_unknown_fmt") or "").format(calls=hosts["unknown"]))))
    for name in proj["host_lexical"] or [None]:
        if not name:
            host_notes.append('  <p data-hosts-lexical-absent>%s</p>'
                              % esc(doc.get("host_lexical_absent") or ""))
            continue
        hosts = proj["rows"][name]["hosts"]
        host_notes.append(
            '  <p data-hosts-lexical="%s" data-hosts-lexical-calls="%d" '
            'data-hosts-lexical-target="%s">%s</p>'
            % (esc(name), hosts["lexical"],
               esc(",".join(hosts["lexical_targets"]) or doc.get("host_none", "")),
               esc((doc.get("host_lexical_fmt") or "").format(
                   calls=hosts["lexical"],
                   target=" , ".join(hosts["lexical_targets"]) or doc.get("host_none", "")))))
    hosts_block = ('  <p class="kindshead">%s</p>\n  <div class="counts kinds">\n%s\n'
                   '  </div>\n  <div class="legend hosts">\n%s\n  </div>\n  <p class="note">%s</p>'
                   % (esc(doc.get("hosts_head", "")), host_counts_html,
                      "\n".join(host_notes), esc(doc.get("host_note", ""))))
    form_counts_html = "\n".join(
        '  <span class="kc" data-form-count="%s"><b>%d</b>%s</span>'
        % (form, proj["form_counts"][form], esc(form_word(doc, form)))
        for form in HANDLER_FORMS
    )
    form_notes = []
    for name in proj["form_calls"] or [None]:
        if not name:
            form_notes.append('  <p data-forms-call-absent>%s</p>'
                              % esc(doc.get("form_calls_absent") or ""))
            continue
        for recv in proj["rows"][name]["forms"]["calls"]:
            form_notes.append(
                '  <p data-forms-call="%s" data-forms-recv="%s">%s</p>'
                % (esc(name), esc(recv),
                   esc((doc.get("form_calls_fmt") or "").format(recv=recv))))
    for name in proj["form_named"] or [None]:
        if not name:
            form_notes.append('  <p data-forms-named-absent>%s</p>'
                              % esc(doc.get("form_named_absent") or ""))
            continue
        for cb, status, targets, form in proj["rows"][name]["forms"]["named"]:
            shown = " , ".join(targets) or doc.get("host_none", "")
            form_notes.append(
                '  <p data-forms-named="%s" data-forms-cb="%s" '
                'data-forms-status="%s" data-forms-target="%s" '
                'data-forms-form="%s">%s</p>'
                % (esc(name), esc(cb), esc(status), esc(shown), esc(form),
                   esc((doc.get("form_named_fmt") or "").format(
                       cb=cb, status=named_reason(doc, status), target=shown,
                       form=decl_word(doc, form)))))
    decl_counts_html = "\n".join(
        '  <span class="kc" data-decl-count="%s"><b>%d</b>%s</span>'
        % (form, proj["named_decl_counts"][form], esc(decl_word(doc, form)))
        for form in DECL_FORMS
    )
    forms_block = ('  <p class="kindshead">%s</p>\n  <div class="counts kinds">\n%s\n'
                   '  </div>\n  <p class="kindshead">%s</p>\n'
                   '  <div class="counts kinds">\n%s\n  </div>\n'
                   '  <div class="legend forms">\n%s\n  </div>\n  <p class="note">%s</p>\n'
                   '  <p class="note">%s</p>'
                   % (esc(doc.get("forms_head", "")), form_counts_html,
                      esc(doc.get("decl_head", "")), decl_counts_html,
                      "\n".join(form_notes), esc(doc.get("form_note", "")),
                      esc(doc.get("decl_note", ""))))
    keys_block = ('  <p class="kindshead">%s</p>\n  <div class="counts kinds">\n%s\n'
                  '  </div>\n  <div class="legend keys">\n%s\n  </div>\n%s\n%s\n%s\n%s'
                  % (esc(doc.get("keys_head", "")), key_counts_html,
                     "\n".join(keys_notes), tiers_block, attrs_block, hosts_block,
                     forms_block))

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
        "attr_counts": proj["attr_counts"],
        "attr_different": proj["attr_different"],
        "attr_unknown": proj["attr_unknown"],
        "host_counts": proj["host_counts"],
        "host_lexical": proj["host_lexical"],
        "host_lexical_calls": proj["host_lexical_calls"],
        "form_counts": proj["form_counts"],
        "form_sites": proj["form_sites"],
        "named_decl_counts": proj["named_decl_counts"],
        "named_total": proj["named_total"],
        "form_calls": {name: proj["rows"][name]["forms"]["calls"]
                       for name in proj["form_calls"]},
        "form_named": {name: proj["rows"][name]["forms"]["named"]
                       for name in proj["form_named"]},
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

    # AC-SH13: the tier says both sides are dom-derived; it does not say they name the
    # same attribute. Every storage face prints the attribute names it writes and reads
    # plus the verdict, every verdict counter equals a fresh reading, and a face whose
    # two sides name different attributes is NAMED with both names (a same-name face
    # listed there reddens, so the table cannot cry wolf).
    for name in proj["key_faces"]:
        attrs = proj["rows"][name]["attrs"]
        got = re.search(r'data-attrs="%s" data-attrs-write="([^"]*)" '
                        r'data-attrs-read="([^"]*)" data-attrs-verdict="([^"]*)"'
                        % re.escape(name), text)
        want = (esc(",".join(attrs["write"])), esc(",".join(attrs["read"])),
                attrs["verdict"])
        if not got:
            failures.append("SH13 attrs_line_missing:%s" % name)
        elif got.groups() != want:
            failures.append("SH13 attrs:%s page=%s fresh=%s" % (name, got.groups(), want))
    for verdict in ATTR_VERDICTS:
        got = re.search(r'data-attr-count="%s"><b>(\d+)</b>' % verdict, text)
        value = int(got.group(1)) if got else None
        if value != proj["attr_counts"][verdict]:
            failures.append("SH13 count:%s page=%s fresh=%d"
                            % (verdict, value, proj["attr_counts"][verdict]))
        if not (proj["doc"].get("attr_words") or {}).get(verdict):
            failures.append("SH13 word_missing:%s" % verdict)
    if sum(proj["attr_counts"].values()) != len(proj["key_faces"]):
        failures.append("SH13 sum=%d faces=%d"
                        % (sum(proj["attr_counts"].values()), len(proj["key_faces"])))
    for verdict, wanted, tag, absent in (
            ("different", proj["attr_different"], "data-attrs-different",
             "data-attrs-different-absent"),
            ("unknown", proj["attr_unknown"], "data-attrs-unknown",
             "data-attrs-unknown-absent")):
        listed = set(re.findall(r'%s="([^"]+)"' % tag, text))
        if listed != set(wanted):
            failures.append("SH13 %s_list page=%s fresh=%s"
                            % (verdict, sorted(listed), sorted(wanted)))
        if not wanted and absent not in text:
            failures.append("SH13 %s_absent_line_missing" % verdict)
    for name in proj["attr_different"]:
        attrs = proj["rows"][name]["attrs"]
        got = re.search(r'data-attrs-different="%s" data-attrs-write="([^"]*)" '
                        r'data-attrs-read="([^"]*)"' % re.escape(name), text)
        want = (esc(",".join(attrs["write"])), esc(",".join(attrs["read"])))
        if not got or got.groups() != want:
            failures.append("SH13 different:%s page=%s fresh=%s"
                            % (name, got.groups() if got else "absent", want))

    # AC-SH14: the name column says both sides read one attribute; it does not say they
    # sit on one element. Every storage face prints the host expression it writes from
    # and reads from, every verdict counter equals a fresh reading, and the five
    # counters sum to the number of storage faces.
    for name in proj["key_faces"]:
        hosts = proj["rows"][name]["hosts"]
        got = re.search(r'data-hosts="%s" data-hosts-write="([^"]*)" '
                        r'data-hosts-read="([^"]*)" data-hosts-verdict="([^"]*)"'
                        % re.escape(name), text)
        want = (esc(",".join(hosts["write"])), esc(",".join(hosts["read"])),
                hosts["verdict"])
        if not got:
            failures.append("SH14 hosts_line_missing:%s" % name)
        elif got.groups() != want:
            failures.append("SH14 hosts:%s page=%s fresh=%s" % (name, got.groups(), want))
    for verdict in HOST_VERDICTS:
        got = re.search(r'data-host-count="%s"><b>(\d+)</b>' % verdict, text)
        value = int(got.group(1)) if got else None
        if value != proj["host_counts"][verdict]:
            failures.append("SH14 count:%s page=%s fresh=%d"
                            % (verdict, value, proj["host_counts"][verdict]))
        if not (proj["doc"].get("host_words") or {}).get(verdict):
            failures.append("SH14 word_missing:%s" % verdict)
    if sum(proj["host_counts"].values()) != len(proj["key_faces"]):
        failures.append("SH14 sum=%d faces=%d"
                        % (sum(proj["host_counts"].values()), len(proj["key_faces"])))

    # AC-SH15: two sides reading one attribute on DIFFERENT host expressions must be
    # NAMED with both expressions, an unresolved `this` must be named with its count,
    # none today prints in words, and a same-host face listed as different reddens.
    for verdict, wanted, tag, absent in (
            ("different", proj["host_different"], "data-hosts-different",
             "data-hosts-different-absent"),
            ("unknown", proj["host_unknown"], "data-hosts-unknown",
             "data-hosts-unknown-absent")):
        listed = set(re.findall(r'%s="([^"]+)"' % tag, text))
        if listed != set(wanted):
            failures.append("SH15 %s_list page=%s fresh=%s"
                            % (verdict, sorted(listed), sorted(wanted)))
        if not wanted and absent not in text:
            failures.append("SH15 %s_absent_line_missing" % verdict)
    for name in proj["host_different"]:
        hosts = proj["rows"][name]["hosts"]
        got = re.search(r'data-hosts-different="%s" data-hosts-write="([^"]*)" '
                        r'data-hosts-read="([^"]*)"' % re.escape(name), text)
        want = (esc(",".join(hosts["write"])), esc(",".join(hosts["read"])))
        if not got or got.groups() != want:
            failures.append("SH15 different:%s page=%s fresh=%s"
                            % (name, got.groups() if got else "absent", want))

    # AC-SH16: a lexical `this` is not a parse failure and not an element. Every face
    # whose `this` read sits in an arrow body above no function literal must be NAMED
    # with its call count and the arrow's target, every per-face call count on the card
    # equals a fresh reading, none today prints in words, and a face with zero lexical
    # reads listed in that table reddens.
    for name in proj["key_faces"]:
        hosts = proj["rows"][name]["hosts"]
        got = re.search(r'data-hosts="%s" data-hosts-write="[^"]*" '
                        r'data-hosts-read="[^"]*" data-hosts-verdict="[^"]*" '
                        r'data-hosts-lexical="(\d+)"' % re.escape(name), text)
        if not got:
            failures.append("SH16 lexical_column_missing:%s" % name)
        elif int(got.group(1)) != hosts["lexical"]:
            failures.append("SH16 lexical:%s page=%s fresh=%d"
                            % (name, got.group(1), hosts["lexical"]))
    listed = {}
    for name, calls, target in re.findall(
            r'data-hosts-lexical="([^"]+)" data-hosts-lexical-calls="(\d+)" '
            r'data-hosts-lexical-target="([^"]*)"', text):
        listed[name] = (int(calls), target)
    if set(listed) != set(proj["host_lexical"]):
        failures.append("SH16 list page=%s fresh=%s"
                        % (sorted(listed), sorted(proj["host_lexical"])))
    for name in proj["host_lexical"]:
        hosts = proj["rows"][name]["hosts"]
        if name in listed and listed[name][0] != hosts["lexical"]:
            failures.append("SH16 calls:%s page=%d fresh=%d"
                            % (name, listed[name][0], hosts["lexical"]))
        if name in listed and listed[name][1] != (",".join(hosts["lexical_targets"])
                                                  or proj["doc"].get("host_none", "")):
            failures.append("SH16 target:%s page=%s fresh=%s"
                            % (name, listed[name][1], hosts["lexical_targets"]))
        if not hosts["lexical"]:
            failures.append("SH16 clean_face_listed:%s" % name)
    if not proj["host_lexical"] and "data-hosts-lexical-absent" not in text:
        failures.append("SH16 absent_line_missing")
    if proj["host_lexical_calls"] != sum(proj["rows"][n]["hosts"]["lexical"]
                                         for n in proj["host_lexical"]):
        failures.append("SH16 total_calls")
    if not (proj["doc"].get("host_lexical_fmt") or "").strip():
        failures.append("SH16 word_missing:host_lexical_fmt")
    if not (proj["doc"].get("host_lexical_absent") or "").strip():
        failures.append("SH16 word_missing:host_lexical_absent")
    if not (proj["doc"].get("host_words") or {}).get("lexical"):
        failures.append("SH16 word_missing:lexical")
    if not (proj["doc"].get("host_count_tags") or {}).get("lexical"):
        failures.append("SH16 tag_missing:lexical")

    # AC-SH17: how a handler is BOUND is counted per face (simple / call / named /
    # attr), every call-expression receiver and every named callback is named with its
    # target or a closed-set reason, and a face with no such site listed reddens.
    for name in proj["key_faces"]:
        got = re.search(r'data-forms="%s" data-forms-simple="(\d+)" '
                        r'data-forms-call="(\d+)" data-forms-named="(\d+)" '
                        r'data-forms-attr="(\d+)"' % re.escape(name), text)
        fresh = proj["rows"][name]["forms"]["forms"]
        want = (str(fresh["simple"]), str(fresh["call"]), str(fresh["named"]),
                str(fresh["attr"]))
        if not got:
            failures.append("SH17 column_missing:%s" % name)
        elif got.groups() != want:
            failures.append("SH17 counts:%s page=%s fresh=%s"
                            % (name, got.groups(), want))
    for form in HANDLER_FORMS:
        got = re.search(r'data-form-count="%s"><b>(\d+)</b>' % form, text)
        if not got:
            failures.append("SH17 total_missing:%s" % form)
        elif int(got.group(1)) != proj["form_counts"][form]:
            failures.append("SH17 total:%s page=%s fresh=%d"
                            % (form, got.group(1), proj["form_counts"][form]))
        if not (proj["doc"].get("form_tags") or {}).get(form):
            failures.append("SH17 tag_missing:%s" % form)
    if sum(proj["form_counts"].values()) != proj["form_sites"]:
        failures.append("SH17 sum=%d sites=%d"
                        % (sum(proj["form_counts"].values()), proj["form_sites"]))
    listed_calls = {}
    for name, recv in re.findall(r'data-forms-call="([^"]+)" '
                                 r'data-forms-recv="([^"]+)"', text):
        listed_calls.setdefault(name, set()).add(recv)
    fresh_calls = {n: set(proj["rows"][n]["forms"]["calls"]) for n in proj["form_calls"]}
    if listed_calls != fresh_calls:
        failures.append("SH17 call_list page=%s fresh=%s"
                        % (sorted(listed_calls), sorted(fresh_calls)))
    if not proj["form_calls"] and "data-forms-call-absent" not in text:
        failures.append("SH17 call_absent_missing")
    for name in proj["form_calls"]:
        if not proj["rows"][name]["forms"]["calls"]:
            failures.append("SH17 clean_face_called:%s" % name)
    listed_named = {}
    for name, cb, status, target in re.findall(
            r'data-forms-named="([^"]+)" data-forms-cb="([^"]+)" '
            r'data-forms-status="([^"]+)" data-forms-target="([^"]*)"', text):
        listed_named[(name, cb)] = (status, target)
        if status not in NAMED_REASONS + ("resolved",):
            failures.append("SH17 reason_open:%s" % status)
    fresh_named = {}
    for name in proj["form_named"]:
        for cb, status, targets, _form in proj["rows"][name]["forms"]["named"]:
            fresh_named[(name, cb)] = (status, " , ".join(targets)
                                       or proj["doc"].get("host_none", ""))
    if listed_named != fresh_named:
        failures.append("SH17 named_list page=%s fresh=%s"
                        % (sorted(listed_named), sorted(fresh_named)))
    if not proj["form_named"] and "data-forms-named-absent" not in text:
        failures.append("SH17 named_absent_missing")
    for name in proj["form_named"]:
        if not proj["rows"][name]["forms"]["named"]:
            failures.append("SH17 clean_face_listed:%s" % name)
    for key in ("forms_head", "forms_fmt", "form_calls_fmt", "form_calls_absent",
                "form_named_fmt", "form_named_absent", "form_note"):
        if not (proj["doc"].get(key) or "").strip():
            failures.append("SH17 word_missing:%s" % key)

    # AC-SH18: WHICH form declared a named callback is graded, not assumed. A
    # `function NAME(` and a var/let/const bound to a function literal are one weight;
    # an arrow is a declaration whose `this` is lexical and must never be resolved to
    # the element; and a name declared in two forms is ambiguous (`twodecl`), never
    # merged into the "exactly one declaration" the resolution rests on.
    listed_decl = {}
    for name, cb, status, target, form in re.findall(
            r'data-forms-named="([^"]+)" data-forms-cb="([^"]+)" '
            r'data-forms-status="([^"]+)" data-forms-target="([^"]*)" '
            r'data-forms-form="([^"]+)"', text):
        listed_decl[(name, cb)] = (status, target, form)
    fresh_decl = {}
    for name in proj["form_named"]:
        for cb, status, targets, form in proj["rows"][name]["forms"]["named"]:
            fresh_decl[(name, cb)] = (status, " , ".join(targets)
                                      or proj["doc"].get("host_none", ""), form)
    if listed_decl != fresh_decl:
        failures.append("SH18 decl_list page=%s fresh=%s"
                        % (sorted(listed_decl), sorted(fresh_decl)))
    for (name, cb), (status, _target, form) in sorted(fresh_decl.items()):
        if form not in DECL_FORMS:
            failures.append("SH18 form_open:%s=%s" % (cb, form))
        if form == "mixed" and status != "twodecl":
            failures.append("SH18 mixed_resolved:%s=%s" % (cb, status))
        if form == "arrow" and status != "lexical":
            failures.append("SH18 arrow_not_lexical:%s=%s" % (cb, status))
        if form in ("func", "varfunc") and status in ("nodecl", "twodecl", "lexical"):
            failures.append("SH18 declared_refused:%s=%s" % (cb, status))
    for form in DECL_FORMS:
        got = re.search(r'data-decl-count="%s"><b>(\d+)</b>' % form, text)
        if not got:
            failures.append("SH18 total_missing:%s" % form)
        elif int(got.group(1)) != proj["named_decl_counts"][form]:
            failures.append("SH18 total:%s page=%s fresh=%d"
                            % (form, got.group(1), proj["named_decl_counts"][form]))
        if not (proj["doc"].get("decl_tags") or {}).get(form):
            failures.append("SH18 tag_missing:%s" % form)
    if sum(proj["named_decl_counts"].values()) != proj["named_total"]:
        failures.append("SH18 sum=%d named=%d"
                        % (sum(proj["named_decl_counts"].values()),
                           proj["named_total"]))
    if proj["named_total"] != sum(len(proj["rows"][n]["forms"]["named"])
                                  for n in proj["form_named"]):
        failures.append("SH18 named_total=%d" % proj["named_total"])
    for key in ("decl_head", "decl_note"):
        if not (proj["doc"].get(key) or "").strip():
            failures.append("SH18 word_missing:%s" % key)
    if "{form}" not in (proj["doc"].get("form_named_fmt") or ""):
        failures.append("SH18 slot_missing:form_named_fmt")

    if failures:
        for line in failures:
            print("  FAIL " + line)
        print("VERDICT FAIL criteria=18 failures=%d" % len(failures))
        return 2
    print("VERDICT PASS criteria=18 faces=%d operable=%d missing_ceo=%d external_refs=0 "
          "kinds=%s keys=%s tiers=%s attrs=%s hosts=%s lexical=faces:%d,calls:%d "
          "forms=%s"
          % (proj["faces_total"], len(proj["operable"]), len(proj["missing"]),
             ",".join("%s:%d" % (kind, proj["kind_counts"][kind]) for kind in KINDS),
             ",".join("%s:%d" % (key, proj["key_counts"][key])
                      for key in ("persists", "expr_paired", "base_paired",
                                  "orphan", "unresolved", "outside")),
             ",".join("%s:%d" % (tier, proj["tier_counts"][tier]) for tier in TIERS)
             + ",cross:%d,noread:%d" % (len(proj["tier_cross"]), len(proj["tier_noread"])),
             ",".join("%s:%d" % (verdict, proj["attr_counts"][verdict])
                      for verdict in ATTR_VERDICTS),
             ",".join("%s:%d" % (verdict, proj["host_counts"][verdict])
                      for verdict in HOST_VERDICTS),
             len(proj["host_lexical"]), proj["host_lexical_calls"],
             ",".join("%s:%d" % (form, proj["form_counts"][form])
                      for form in HANDLER_FORMS)
             + " decl=%s" % ",".join("%s:%d" % (form, proj["named_decl_counts"][form])
                                     for form in DECL_FORMS)))

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
