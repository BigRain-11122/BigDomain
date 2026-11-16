"""value_domain.py - the ONE value-domain assertion every price face imports.

WHY THIS FILE EXISTS (D-20261116-13, dispatched to @BigDomain 2026-11-16,
deadline 2026-11-17 12:00): a --check that reads green must carry at least one
VALUE-DOMAIN assertion - a price, entitlement, period or quota compared against
the CATALOG - and not merely structural self-consistency. R2816 measured three
faces printing PASS while the landed price table still carried 1990 against a
config reading 990, because "landed == fresh derivation" and "size == disk" are
both satisfied by a chain that is consistently wrong with itself.

The catalog is src/sandbox/pay/config.json (products) joined to
src/sandbox/member/config.json (tiers: period_days, monthly_credits,
privileges). This module is the single implementation: payment_gate_report,
money_path_demo, membership_face and membership_benefit_report IMPORT it
instead of each writing its own comparison loop (AC-VD1/AC-VD7).

CONTRACT: every failure string starts with E_VALUE_DOMAIN and names the entity
plus both sides, so a red face says which product and which numbers disagree.
require_one=True is the ruling's teeth: a face that compares NOTHING is red,
so "structurally green" can never be mistaken for a value-domain pass.

Read-only. No network. No Chinese literals (source is ASCII by house law).
"""
import hashlib
import json
import os

ERR = "E_VALUE_DOMAIN"

FIELDS_PRODUCT = ("price_cent", "channel", "entitlement")
FIELDS_TIER = ("period_days", "monthly_credits", "privileges")


def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def paths(root):
    return {
        "pay": os.path.join(root, "src", "sandbox", "pay", "config.json"),
        "member": os.path.join(root, "src", "sandbox", "member", "config.json"),
    }


def catalog(root):
    """The live catalog, read from disk. Never cached across calls."""
    p = paths(root)
    pay_cfg = read_json(p["pay"]) if os.path.isfile(p["pay"]) else {}
    mem_cfg = read_json(p["member"]) if os.path.isfile(p["member"]) else {}
    products = {}
    for pid, row in (pay_cfg.get("products") or {}).items():
        if not isinstance(row, dict):
            continue
        products[pid] = {
            "price_cent": row.get("price_cent"),
            "channel": row.get("channel"),
            "entitlement": row.get("entitlement"),
            "name": row.get("name"),
        }
    tiers = {}
    for key, row in (mem_cfg.get("tiers") or {}).items():
        if not isinstance(row, dict):
            continue
        tiers[key] = {
            "period_days": row.get("period_days"),
            "monthly_credits": row.get("monthly_credits"),
            "privileges": sorted(row.get("privileges") or []),
        }
    return {
        "products": products,
        "tiers": tiers,
        "pay_path": p["pay"],
        "member_path": p["member"],
        "pay_sha256": sha256_of(p["pay"]) if os.path.isfile(p["pay"]) else None,
        "member_sha256": sha256_of(p["member"]) if os.path.isfile(p["member"]) else None,
    }


def _same(a, b):
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        return sorted(a or []) == sorted(b or [])
    return a == b


def product_failures(rows, cat, fields=FIELDS_PRODUCT, require_one=True,
                     stats=None):
    """Compare landed product rows against the catalog, by value.

    rows: any sequence of dicts carrying an "id". Extra keys in the row are
    ignored; only `fields` are compared. A row whose id is absent from the
    catalog is red (the row is selling something the catalog does not have).

    stats: optional dict filled with {"products": <rows actually compared>} so
    a face can print how much value work it did without counting twice.
    """
    fails = []
    catalog_products = cat.get("products") or {}
    seen = 0
    for row in (rows or []):
        pid = row.get("id")
        if not pid:
            continue
        want = catalog_products.get(pid)
        if want is None:
            fails.append("%s product %s is not in the catalog" % (ERR, pid))
            continue
        for key in fields:
            got = row.get(key)
            exp = want.get(key)
            if key in row and not _same(got, exp):
                fails.append("%s stale product row on %s: landed %s=%r != "
                             "catalog %r" % (ERR, pid, key, got, exp))
            elif key not in row:
                fails.append("%s product %s does not carry %s, so no value was "
                             "compared" % (ERR, pid, key))
        seen += 1
    if require_one and seen == 0:
        fails.append("%s no product row was compared against the catalog "
                     "(structural green is not a value-domain pass)" % ERR)
    if stats is not None:
        stats["products"] = seen
    return fails


def tier_key_from_entitlement(entitlement):
    """'tier:patron' -> 'patron'. Anything else -> None."""
    text = str(entitlement or "")
    if text.startswith("tier:"):
        return text.split(":", 1)[1] or None
    return None


def tier_failures(rows, cat, fields=FIELDS_TIER, require_one=True,
                  stats=None):
    """Compare tier rows (period / quota / privileges) against the catalog.

    rows: a dict keyed by tier name, OR a sequence of dicts carrying "tier"
    (or "entitlement" shaped 'tier:<key>'). Rows whose tier key is absent from
    the catalog are red.
    """
    fails = []
    catalog_tiers = cat.get("tiers") or {}
    if isinstance(rows, dict):
        items = [(k, v) for k, v in rows.items()]
    else:
        items = []
        for row in (rows or []):
            key = row.get("tier") or tier_key_from_entitlement(row.get("entitlement"))
            if key:
                items.append((key, row))
    seen = 0
    for key, row in items:
        want = catalog_tiers.get(key)
        if want is None:
            fails.append("%s tier %s is not in the catalog" % (ERR, key))
            continue
        for field in fields:
            got = row.get(field)
            exp = want.get(field)
            if field in row and not _same(got, exp):
                fails.append("%s stale tier row on %s: landed %s=%r != "
                             "catalog %r" % (ERR, key, field, got, exp))
            elif field not in row:
                fails.append("%s tier %s does not carry %s, so no value was "
                             "compared" % (ERR, key, field))
        seen += 1
    if require_one and seen == 0:
        fails.append("%s no tier row was compared against the catalog" % ERR)
    if stats is not None:
        stats["tiers"] = seen
    return fails


def config_drift(landed_sha, cat, key="pay_sha256"):
    """The document was rendered against another config than the live one."""
    want = cat.get(key)
    if landed_sha != want:
        return ["%s config drift: landed sha256 %s != current %s" % (
            ERR, str(landed_sha)[:16], str(want)[:16])]
    return []


NO_COMPARISON = (ERR + " no row was compared against the catalog, so the "
                       "formatter refuses to print PASS")


def teeth(rows_checked, tier_rows_checked, failures):
    """Fold the no-comparison refusal into the caller's OWN failure list.

    A face that prints `line()` and exits on a different list could print FAIL
    and still exit 0, so both sides read this one list (AC-VD11).
    """
    fails = list(failures or [])
    if not rows_checked and not tier_rows_checked and not fails:
        fails.append(NO_COMPARISON)
    return fails


def line(rows_checked, tier_rows_checked, failures):
    """One printable line so a green face says its value-domain work out loud.

    The formatter itself refuses to certify an empty comparison (AC-VD11): the
    count of what was compared is part of the claim, not decoration.
    """
    fails = teeth(rows_checked, tier_rows_checked, failures)
    if fails:
        return "value-domain: FAIL %d (products=%d tiers=%d) %s" % (
            len(fails), rows_checked, tier_rows_checked, fails[0])
    return "value-domain: PASS products=%d tiers=%d" % (rows_checked,
                                                        tier_rows_checked)
