"""Close the R2522 layout defect at its birth site (AC-SFOLD4).

The live state.json is written by the shipped append path with a 1-space key
indent, 2-space log-item indent and LF separators, while state_fold.py
insisted on 16-space items and 4-space keys - so the reader refused the very
file the append path produces. The repair is on the reader, not on the file:
derive the item indent from the file itself and insert with that same indent.
"""

import io

PATH = "src/os/state_fold.py"
text = io.open(PATH, encoding="utf-8", newline="").read()

old_signature = '''def split_layout(text, log_len):
    """Locate the log item lines in the canonical PS layout.

    Returns a dict with the split lines, the newline, the ordered item line
    indices and the first item index, or None when the file is not in the
    canonical layout for this log length.
    """
    newline = "\\r\\n" if "\\r\\n" in text else "\\n"
    lines = text.split(newline)
    first = None
    items = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(\'"log"\') and stripped.endswith("["):
            first = index
            continue
        if first is None:
            continue
        if (len(line) > ITEM_INDENT and line[:ITEM_INDENT] == ITEM_PREFIX
                and line[ITEM_INDENT] == \'"\'):
            items.append(index)
        elif stripped.startswith("]"):
            break
    if first is None or len(items) != log_len:
        return None
    return {
        "lines": lines,
        "newline": newline,
        "item_index": items,
        "first_item": items[0],
    }'''

new_signature = '''def split_layout(text, log_len):
    """Locate the log item lines in the layout the FILE ITSELF uses.

    R2522 measured a reader that insisted on a 16-space item indent while the
    shipped append path wrote 2-space items, so the fold refused the real
    file. The indent is therefore DERIVED from the first item line and every
    item must share it; a file whose items disagree with each other is refused
    rather than reformatted. Returns the split lines, the newline, the ordered
    item line indices, the first item index and the derived item prefix.
    """
    newline = "\\r\\n" if "\\r\\n" in text else "\\n"
    lines = text.split(newline)
    first = None
    items = []
    prefix = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(\'"log"\') and stripped.endswith("["):
            first = index
            continue
        if first is None:
            continue
        indent = line[:len(line) - len(line.lstrip(" "))]
        if indent and line[len(indent):len(indent) + 1] == \'"\':
            if prefix is None:
                prefix = indent
            if indent != prefix:
                return None
            items.append(index)
        elif stripped.startswith("]"):
            break
    if first is None or prefix is None or len(items) != log_len:
        return None
    return {
        "lines": lines,
        "newline": newline,
        "item_index": items,
        "first_item": items[0],
        "item_prefix": prefix,
    }'''

assert text.count(old_signature) == 1
text = text.replace(old_signature, new_signature)

old_literal = '''    literal = ITEM_PREFIX + ps_escape(summary)'''
new_literal = '''    literal = layout["item_prefix"] + ps_escape(summary)'''
assert text.count(old_literal) == 1
text = text.replace(old_literal, new_literal)

io.open(PATH, "w", encoding="utf-8", newline="").write(text)
print("repaired")