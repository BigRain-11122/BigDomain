"""registry_counter_census.py - which registry rows can be refuted at run time.

Why this exists: every row of src/sandbox/reconcile_all.py SUITES declares an
expected criteria count, and most of those numbers are typed in exactly one
place, so nothing refuses a second edit that leaves them wrong. R2917 bound ONE
row to its own suite. The R2918 board question is whether that binding is worth
extending, and it cannot be answered without knowing WHICH rows the shipped
battery reader can even read: a suite that prints no parseable counter can never
refute its row.

What is measured, per registry row, by reading the suite SOURCE (never running
it): does the file contain a print of a SUITE row whose leaf shape the shipped
tools/battery_shard.py reader parses? Three classes, total and disjoint:

  READABLE - at least one printed SUITE leaf is parsed by the shipped reader,
             so the battery's crit_mismatch comparison can see a drift.
  UNPARSED - the file prints a SUITE row, but no printed leaf is parseable
             (e.g. "SUITE PASS 163 checks" states no FAIL count, so the
             shipped reader refuses it by design).
  SILENT   - the file prints no SUITE row at all, counting both the literals
             on a print line and the module constants that line references
             (a row printed through `V = "SUITE PASS"` is not silent); the
             row's number is typed and nothing on the run path compares it.

The parser is IMPORTED from the tool, not copied: a second regex family here
would be a second opinion instead of the battery's own one.

Disclosed limits: this is a STATIC upper bound. A shape found in the source is
not proof that the runtime line carries the declared number - a suite may print
a counter whose value is an assertion count rather than its criteria count.
Read-only, ASCII source, stdlib only, zero network.

Criteria AC-RCC1..AC-RCC12 are pre-registered in src/os/backlog.md (R2918 row,
extended at R2921/R2922/R3076/R3077/R3078/R3079).

R3079 split the last 89 UNPARSED rows by measurement instead of by label and
found one read gap and one encoding artefact, not three buckets. (a) 76 rows
print `"%s %d/%d" % (verdict, expr, expr)` with the SUITE word bound to a
NAME: the text join refused any argument that was not a single token (so
`len(...)` and `a - b` killed the whole line), and the AST pass demanded SUITE
inside the format string. Taking the word from the argument, and accepting the
filled leaf only when it carries SUITE, flips 77 rows with 0 regressions.
(b) 9 rows print `"SUITE %s %d/%d"` with the verdict name bound to the bare
`"PASS"/"FAIL"`, which the constant collector dropped because it filtered on
SUITE; collecting the exact verdict words flips 8 more (85 total). (c) The 4
rows left are all UTF-8 BOM files: ast.parse dies on U+FEFF, so the AST pass
was blind to the whole file; reading with utf-8-sig flips them. Together: 89
rows flipped, 0 regressed, 0 SILENT moved, assembled still 293. Refused, with
reasons: reading `SUITE %d/%d green` as PASS (green is not the law's word),
letting an unknown name become a PASS/FAIL candidate (that would invent a
verdict), pinning assembled_print_lines (still this reader's own limit), and
fixing one label family at a time (the missing reach is one read).

R3078 closed two things the R3077 round left open, both by measurement. (a) The
119-vs-122 gap was the PROBE, not the tree: that probe ran its AST pass on
continuation-joined text, and the join leaves 11 files syntactically invalid
("'[' was never closed"), so those rows lost their AST reach; 8 of them were
already text-READABLE (the loss was invisible as a flip) and exactly 3 were
text-only UNPARSED - ledger-incentive-persist, ledger-eventtickets-boardlimit,
ledger-freetrial-capusage - which is the 122-119=3. (b) The remaining bucket
was over-counted for one reason: a format argument that is a NAME not bound to
a literal (a runtime counter such as `passed`/`total`) was refused, while the
same argument as a call (len(...)) already took a placeholder digit. Taking the
digit for both flips 215 live rows with 0 regressions; eight were RUN across
eight families and their own SUITE rows read back 8/8. The 89 rows left after
that are named in the R3078 board row: 9 genuinely carry no verdict word and
are a SUITE-side fix (the reader must not invent a verdict), 54 still carry
names in a shape the pass does not resolve, 26 are other.

R3077 widened the reach WITHOUT replacing the text pass: `ast_leaves()` resolves
a printed row through the CALL (an inline conditional argument, a `len(...)`
argument, a constant named inside the format tuple), and classify() only asks it
when every text leaf failed. Measured before the change: a text-level
continuation join flips 0 rows and regresses 1 (it swallows lines through an
apostrophe in a comment), a replacement-style AST pass flips 119 but regresses
220, and the UNION flips 119 with 0 regressions, ten of which were RUN and read
their own SUITE row. Refused, with reasons: splitting the fix per label family
(the missing reach is one read, not two dialects) and putting
assembled_print_lines into the pin (it counts THIS reader's own limit, not a
fact about a suite).

R3097 - each suite source is parsed ONCE (equivalence, measured):

The closeout dry run became slow enough that people stop running it: over 734
registry rows `census()` measured 5699.0ms, of which 2390.4ms was AST work and
1710.5ms of that was a SECOND parse of a file already parsed - `suite_constants`
parsed the text, and `classify` reached `ast_leaves`, which parsed it again
whenever the text pass found no readable leaf (443 of 734 rows). `census()` now
parses once and passes the tree into `suite_constants`, `classify` and
`ast_leaves`; a SyntaxError still takes the shipped text-only path, and every
optional parameter defaults to None so an outside caller keeps its old
behaviour. Nothing about the reading changed: the pin on disk was written by
the pre-R3097 code, so a passing --check is the equivalence proof, not a claim.
"""
import ast
import hashlib
import importlib.util
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
REGISTRY = os.path.join(ROOT, 'src', 'sandbox', 'reconcile_all.py')
TOOL = os.path.join(ROOT, 'tools', 'battery_shard.py')
PIN = os.path.join(BASE, 'registry_counter_census_pin.json')
CACHE = os.path.join(BASE, 'registry_counter_census_cache.json')
CACHE_VERSION = 1
LABEL = 'os-registry-counter-census'

PLACEHOLDER = re.compile(r'%[dsrf]|\{[^}]*\}')
PRINT_LINE = re.compile(r'(?:print|write)\s*\(')
STRING_LIT = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\'')
# A same-line format application: print("%s %d/%d" % (V, p, t)). R2921 moved
# these rows out of SILENT (the constant is seen) but they stayed UNPARSED,
# because the words live in the constant and the numbers in the format string.
FMT_APPLY = re.compile(r'("(?:[^"\\]|\\.)*")\s*%\s*\(([^()]*)\)')
PLACE = re.compile(r'%[sdif]')


class CensusError(Exception):
    def __init__(self, code, detail=''):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def reader():
    """The shipped reader, imported by path so no tool side effect is trusted."""
    spec = importlib.util.spec_from_file_location('bd_battery_shard', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def registry_rows(path):
    src = io.open(path, encoding='utf-8').read()
    tree = ast.parse(src)
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == 'SUITES'
                   for t in node.targets):
            continue
        for elt in node.value.elts:
            label = elt.elts[0].value
            path_node = elt.elts[1]
            crit = elt.elts[2].value
            if isinstance(path_node, ast.Call):
                rel = os.path.join(*[a.value for a in path_node.args])
            else:
                rel = path_node.value
            out.append((label, os.path.normpath(rel), crit))
    return out


def _suite_literals(node, alone=False):
    """String literals containing SUITE reachable from an assignment value.

    ast.walk reaches both arms of an if/else expression, the left operand of a
    `%` format and the literal parts of an f-string, which are the three shapes
    the shipped suites use to name their SUITE row once and print it later.

    With alone=True an exact "PASS"/"FAIL" literal is collected too: the R3079
    measured family prints "SUITE %s %d/%d" % (verdict, ...) with the verdict
    name bound to the bare word, and refusing it made the argument fall back to
    the placeholder digit ("SUITE 7 7/7"). Only the exact verdict words are
    added - "GREEN" or "PASS %s" stay refused, so no word the suite never said
    can be invented (AC-RCC12-R7).
    """
    out = []
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Constant):
            continue
        if not isinstance(sub.value, str):
            continue
        if 'SUITE' in sub.value or (alone and sub.value in ('PASS', 'FAIL')):
            out.append(sub.value)
    return out


def suite_constants(text, tree=None):
    """Names bound to a string literal that contains SUITE (simple propagation).

    leaf_lines reads one line at a time, so a suite that prints its row through
    a constant (`V = "SUITE PASS"` ... `print("%s %d/%d" % (V, ...))`) looked
    SILENT - a statement about this reader, not about the suite. Collecting the
    constant assignments (both arms of an if/else) is the smallest propagation
    that makes the class name mean what it says. The bare verdict words are
    collected too, because print("SUITE %s %d/%d" % (verdict, ...)) names its
    word through a constant that carries no SUITE itself (R3079).
    """
    out = {}
    if tree is None:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        literals = _suite_literals(node.value, alone=True)
        if not literals:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                out.setdefault(target.id, []).extend(literals)
    return out


def _joined(line, consts):
    """Same-line join of a SUITE constant with the format string beside it.

    Only ONE line is read. A constant on one line and the numbers on another
    are not a printed row, and joining them would fabricate a leaf the runtime
    never emits - that case is measured, not trusted (AC-RCC8-R2). The joined
    text is handed to the SHIPPED reader unchanged, whose patterns are anchored
    at a line start, so a join that puts SUITE anywhere but the head is refused
    by that reader rather than by a rule invented here (AC-RCC8-R3).
    """
    out = []
    for match in FMT_APPLY.finditer(line):
        try:
            fmt = ast.literal_eval(match.group(1))
        except (ValueError, SyntaxError):
            continue
        args = [a.strip() for a in match.group(2).split(',') if a.strip()]
        holes = list(PLACE.finditer(fmt))
        if not holes or len(holes) != len(args):
            continue
        pieces = []
        last = 0
        usable = True
        for hole, arg in zip(holes, args):
            pieces.append(fmt[last:hole.start()])
            last = hole.end()
            if arg in consts:
                pieces.append(consts[arg][0])
            elif re.match(r'^[-0-9A-Za-z_.\'\"]+$', arg):
                pieces.append('7' if hole.group(0) == '%d' else 'x')
            else:
                usable = False
                break
        if not usable:
            continue
        pieces.append(fmt[last:])
        out.append(''.join(pieces))
    return out


def leaf_lines(text, consts=None):
    """Every printed leaf that starts with SUITE, placeholders neutralised.

    Returns (leaves, assembled). `assembled` counts print lines whose SUITE row
    is built from more than one literal (print("SUITE PASS", n, "/", m)), i.e.
    rows THIS READER cannot see whole even though the runtime line may be
    parseable - the extractor's own limit, counted rather than hidden in the
    unparsed bucket.

    A print line whose own literals carry no SUITE still counts when it
    references a name from suite_constants(): the row exists in the source even
    though this one line does not spell it, and when the same line also applies
    a format string to that name the two halves are joined before the shipped
    reader sees them.
    """
    out = []
    assembled = 0
    consts = consts or {}
    for line in text.split('\n'):
        if not PRINT_LINE.search(line):
            continue
        literals = [a if a else b for a, b in STRING_LIT.findall(line)]
        hits = [lit for lit in literals if 'SUITE' in lit]
        if consts:
            named = any(re.search(r'\b%s\b' % re.escape(name), line)
                        for name in consts)
            if named:
                hits.extend(_joined(line, consts))
                if not hits:
                    for name, values in consts.items():
                        if re.search(r'\b%s\b' % re.escape(name), line):
                            hits.extend(values)
        if not hits:
            continue
        if len(literals) > 1:
            assembled += 1
        for literal in hits:
            out.append(PLACEHOLDER.sub('7', literal))
    return out, assembled


def _arg_text(node, consts):
    """One argument of a format tuple, as the text it contributes.

    An inline conditional resolves to its FIRST arm: both arms of the shipped
    dialects are verdict words, so the arm chosen never decides readability,
    and inventing a rule that prefers PASS would be a guess. A call (len(...))
    contributes one placeholder digit - its value is not a source fact.
    """
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return node.value
        return '7'
    if isinstance(node, ast.IfExp):
        return _arg_text(node.body, consts)
    if isinstance(node, ast.Name):
        # A name bound to a SUITE literal is a source fact and is read verbatim.
        # A name bound to anything else is a counter the runtime computes, which
        # is the same thing len(...) is: not a source fact, so one placeholder
        # digit. R3078 measured this branch as the single reason 215 rows stayed
        # UNPARSED, with zero rows regressing when they were read.
        values = consts.get(node.id)
        return values[0] if values else '7'
    if isinstance(node, (ast.Call, ast.BinOp, ast.Attribute, ast.Subscript,
                         ast.Compare)):
        return '7'
    return None


def _filled(fmt, args, consts):
    holes = list(PLACE.finditer(fmt))
    if not holes:
        return None
    values = []
    for arg in args:
        text = _arg_text(arg, consts)
        if text is None:
            return None
        values.append(text)
    if len(values) != len(holes):
        return None
    pieces = []
    last = 0
    for hole, value in zip(holes, values):
        pieces.append(fmt[last:hole.start()])
        pieces.append(value if hole.group(0) != '%d' else (re.sub(r'\D', '', value) or '7'))
        last = hole.end()
    pieces.append(fmt[last:])
    return ''.join(pieces)


def ast_leaves(text, consts, tree=None):
    """Rows reachable through the print CALL rather than through one line.

    This is the union the R3077 measurement justified: it is asked only after
    every text leaf failed, so a shape the text pass already reads keeps its
    exact reading. A print whose literal puts any word before SUITE yields a
    leaf the shipped anchored reader refuses, so this pass cannot fabricate a
    row either (AC-RCC10-R3).
    """
    out = []
    if tree is None:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, 'id', None) or getattr(func, 'attr', None)
        if name not in ('print', 'write'):
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if 'SUITE' in arg.value:
                    out.append(arg.value)
            elif isinstance(arg, ast.JoinedStr):
                parts = []
                for part in arg.values:
                    if isinstance(part, ast.Constant) and isinstance(part.value, str):
                        parts.append(part.value)
                    else:
                        parts.append('7')
                joined = ''.join(parts)
                if 'SUITE' in joined:
                    out.append(joined)
            elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):
                fmt = arg.left
                if not (isinstance(fmt, ast.Constant)
                        and isinstance(fmt.value, str)):
                    continue
                args = arg.right.elts if isinstance(arg.right, ast.Tuple) else [arg.right]
                leaf = _filled(fmt.value, list(args), consts)
                # The SUITE word may live in the ARGUMENTS rather than in the
                # format string: print("%s %d/%d" % (verdict, a - b, c)) with
                # verdict bound to a SUITE literal is the R3079 measured family
                # (76 rows). The leaf is kept only when the FILLED text carries
                # SUITE, so a format with no SUITE anywhere still yields
                # nothing and no word is invented (AC-RCC12-R4).
                if leaf and 'SUITE' in leaf:
                    out.append(leaf)
            elif isinstance(arg, ast.Name) and arg.id in consts:
                out.extend(consts[arg.id])
    return out


def classify(text, module, consts=None, tree=None):
    leaves, assembled = leaf_lines(text, consts)
    if not leaves:
        return 'SILENT', assembled
    for leaf in leaves:
        if module.parse_suite_row(leaf + '\n') is not None:
            return 'READABLE', assembled
    for leaf in ast_leaves(text, consts or {}, tree):
        if module.parse_suite_row(PLACEHOLDER.sub('7', leaf) + '\n') is not None:
            return 'READABLE', assembled
    return 'UNPARSED', assembled


def reader_digest():
    """The identity a cache entry is only valid under (R3098).

    A cached CLASS is a statement about one reader applied to one file, so the
    reader belongs in the key: if `tools/battery_shard.py` or this module's
    classifier changes, every old entry must be thrown away rather than reused
    against a reader that no longer answers the same question.
    """
    with io.open(TOOL, 'rb') as handle:
        tool = hashlib.sha256(handle.read()).hexdigest()
    with io.open(os.path.abspath(__file__), 'rb') as handle:
        own = hashlib.sha256(handle.read()).hexdigest()
    return 'v%d:%s:%s' % (CACHE_VERSION, tool, own)


def _rows_digest(rows):
    """Content digest of the entry table itself (R3098).

    A cache that pairs a content hash with a cached CLASS is only as trustworthy
    as the file that carries the pair: one corrupted byte would serve a wrong
    class under a right hash. Sealing the table makes any accidental edit a
    NAMED refusal instead of a quiet wrong answer. Deliberately forging both
    the entries and this seal is the same act as forging the pin, and is stated
    as the unprovable face rather than claimed away.
    """
    blob = json.dumps(rows, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


def load_cache(path, digest):
    """(entries_by_rel, note). note names why the cache was refused, never ''."""
    if not path or not os.path.isfile(path):
        return {}, 'E_RCC_CACHE_ABSENT'
    try:
        with io.open(path, encoding='utf-8') as handle:
            data = json.load(handle)
    except (IOError, OSError, ValueError) as exc:
        return {}, 'E_RCC_CACHE_UNREADABLE %s' % type(exc).__name__
    if not isinstance(data, dict) or not isinstance(data.get('rows'), dict):
        return {}, 'E_RCC_CACHE_SHAPE'
    if data.get('reader') != digest:
        return {}, 'E_RCC_CACHE_STALE_READER'
    if data.get('rows_digest') != _rows_digest(data['rows']):
        return {}, 'E_RCC_CACHE_TAMPERED'
    return data['rows'], ''


def write_cache(path, digest, rows):
    """(note). A failed write is published, never raised into a verdict."""
    try:
        with io.open(path, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps({'version': CACHE_VERSION, 'reader': digest,
                                     'rows_digest': _rows_digest(rows),
                                     'rows': rows}, indent=1,
                                    sort_keys=True) + '\n')
        return ''
    except (IOError, OSError) as exc:
        return 'E_RCC_CACHE_WRITE %s' % type(exc).__name__


def census(registry=REGISTRY, sandbox=None, cache_path=None, cache_write=True):
    """Walk every registry row and classify its suite by reading its source.

    R3098: with `cache_path` given, an entry is reused only when BOTH the file's
    content digest and the reader digest match. The key is the content, not
    (size, mtime): measured this round, two writes of different 1KB contents in
    the same second carried the SAME st_mtime_ns (1795181163516169600), so an
    mtime-keyed cache would have served a stale class. `cache_path=None` keeps
    the pre-R3098 path byte for byte, and `cache_write=False` lets a read-only
    caller (the closeout gate) read the cache without writing it.
    """
    module = reader()
    rows = registry_rows(registry)
    sandbox = sandbox or os.path.dirname(registry)
    digest = reader_digest() if cache_path else ''
    cached, note = (load_cache(cache_path, digest) if cache_path
                    else ({}, 'E_RCC_CACHE_OFF'))
    reused = 0
    report = {'rows': len(rows), 'READABLE': [], 'UNPARSED': [],
              'SILENT': [], 'assembled': 0, 'cache': note,
              'cache_reused': 0}
    fresh = {}
    for label, rel, crit in rows:
        path = os.path.join(sandbox, rel)
        if not os.path.exists(path):
            raise CensusError('E_RCC_MISSING_SUITE', '%s %s' % (label, rel))
        with io.open(path, 'rb') as handle:
            raw = handle.read()
        sha = hashlib.sha256(raw).hexdigest()
        hit = cached.get(rel)
        if hit is not None and hit.get('sha') == sha:
            kind = hit.get('kind')
            if kind in ('READABLE', 'UNPARSED', 'SILENT'):
                report[kind].append(label)
                report['assembled'] += int(hit.get('assembled') or 0)
                fresh[rel] = hit
                reused += 1
                continue
        # Text mode keeps universal-newline translation, which the shipped
        # reading was measured under; reading the bytes once and decoding the
        # same bytes keeps that behaviour without a second pass over the disk.
        with io.TextIOWrapper(io.BytesIO(raw), encoding='utf-8-sig',
                              errors='replace') as text_io:
            text = text_io.read()
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None
        consts = suite_constants(text, tree)
        kind, assembled = classify(text, module, consts, tree)
        report[kind].append(label)
        report['assembled'] += assembled
        fresh[rel] = {'sha': sha, 'kind': kind, 'assembled': assembled}
    if cache_path:
        written = write_cache(cache_path, digest, fresh) if cache_write else ''
        if written:
            report['cache'] = written if not note else note + ' ' + written
        elif not note:
            report['cache'] = 'E_RCC_CACHE_HIT' if reused == len(rows) \
                else 'E_RCC_CACHE_PARTIAL'
    report['cache_reused'] = reused
    total = sum(len(report[kind])
                for kind in ('READABLE', 'UNPARSED', 'SILENT'))
    if total != report['rows']:
        raise CensusError('E_RCC_NOT_TOTAL',
                          '%d != %d' % (total, report['rows']))
    return report


def pin_shape(report):
    return {'readable': sorted(report['READABLE']),
            'unparsed': sorted(report['UNPARSED']),
            'silent': sorted(report['SILENT'])}


def compare(report, pinned):
    """Two-way diff per class; an unknown class is a refusal, not a skip."""
    fails = []
    measured = pin_shape(report)
    for key in ('readable', 'unparsed', 'silent'):
        got = set(measured[key])
        want = set(pinned.get(key, []))
        if got != want:
            fails.append('%s +%d -%d' % (key, len(got - want), len(want - got)))
    for key in pinned:
        if key not in measured:
            fails.append('unknown-class %s' % key)
    return fails


def render(report):
    return ('REGISTRY COUNTER CENSUS rows=%d readable=%d unparsed=%d '
            'silent=%d assembled_print_lines=%d'
            % (report['rows'], len(report['READABLE']),
               len(report['UNPARSED']), len(report['SILENT']),
               report['assembled']))


def main(argv):
    as_json = False
    check = False
    write_pin = False
    use_cache = True
    for arg in argv:
        if arg == '--json':
            as_json = True
        elif arg == '--check':
            check = True
        elif arg == '--write-pin':
            write_pin = True
        elif arg == '--no-cache':
            use_cache = False
        elif arg in ('--help', '-h'):
            sys.stdout.write('usage: registry_counter_census.py '
                             '[--json] [--check] [--write-pin] [--no-cache]\n')
            return 0
        else:
            sys.stdout.write('E_RCC_BAD_ARGS %s\n' % arg)
            return 5
    cache_path = CACHE if use_cache else None
    try:
        report = census(cache_path=cache_path)
    except CensusError as exc:
        sys.stdout.write('%s %s\n' % (exc.code, exc.detail))
        return 2
    if cache_path:
        # Published, never silent: a reader must be able to see whether the
        # numbers above came from a cache and whether it was usable at all.
        sys.stdout.write('CACHE %s reused=%d/%d\n'
                         % (report['cache'] or 'E_RCC_CACHE_HIT',
                            report['cache_reused'], report['rows']))
    if write_pin:
        with io.open(PIN, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(json.dumps(pin_shape(report), indent=2,
                                    sort_keys=True) + '\n')
    if as_json:
        sys.stdout.write(json.dumps(pin_shape(report), sort_keys=True) + '\n')
    else:
        sys.stdout.write(render(report) + '\n')
    if check:
        if not os.path.exists(PIN):
            sys.stdout.write('E_RCC_NO_PIN %s\n' % PIN)
            return 2
        pinned = json.loads(io.open(PIN, encoding='utf-8').read())
        fails = compare(report, pinned)
        if fails:
            sys.stdout.write('VERDICT FAIL %s\n' % ' '.join(fails))
            return 2
        sys.stdout.write('VERDICT PASS pinned=%d\n'
                         % sum(len(v) for v in pinned.values()))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
