"""Tests for the SKU x compliance map gate (AC-CM1..CM5, pre-registered R675).

Seat-7 rider enforcement: A-tier pre-launch gate, no billing before the
table passes, BigCompute co-sign column pending. All Chinese fixtures are
loaded from the JSON data file; this test module stays pure ASCII.
"""
import unittest

import sku_compliance_map as scm


class VerifyRegistryTest(unittest.TestCase):
    """AC-CM2: full in-force canon registration, zero invented SKUs."""

    def setUp(self):
        self.data = scm.load_map()

    def test_in_force_count_is_32(self):
        self.assertEqual(scm.verify_registry(self.data), [])
        self.assertEqual(len(self.data["in_force_skus"]), 32)

    def test_family_counts_match_canon(self):
        counts = {}
        for row in self.data["in_force_skus"]:
            counts[row["family"]] = counts.get(row["family"], 0) + 1
        self.assertEqual(counts, {"C": 18, "B": 9, "live": 3, "kp": 2})

    def test_every_row_has_five_columns_and_cosign_key(self):
        cols = set(self.data["meta"]["column_keys"])
        for row in self.data["in_force_skus"]:
            self.assertEqual(set(row["cells"].keys()), cols)
            self.assertIn(scm.COSIGN_KEY, row)
            for key in self.data["meta"]["column_keys"]:
                self.assertTrue(
                    str(row["cells"][key].get("obligation", "")).strip(),
                    "row %s col %s must not be empty" % (row["id"], key))

    def test_pending_pool_lists_n_series(self):
        ids = [item["id"] for item in self.data["pending_pool"]]
        self.assertEqual(ids, ["N1", "N3", "N4", "N5", "N7", "N8"])


class VerifyATierTest(unittest.TestCase):
    """AC-CM3: A-tier rows filled across five columns + cosign pending."""

    def setUp(self):
        self.data = scm.load_map()
        self.by_id = {r["id"]: r for r in self.data["in_force_skus"]}

    def test_a_tier_is_exactly_case_a_skus(self):
        self.assertEqual(sorted(self.data["meta"]["a_tier_skus"]),
                         ["C2-B", "C2-C"])

    def test_a_tier_rows_fully_filled(self):
        self.assertEqual(scm.verify_a_tier(self.data), [])

    def test_a_tier_refund_cells_carry_refund_and_prepaid(self):
        kw = self.data["meta"]["invariants"]["a_tier_refund_keywords"]
        for sku in self.data["meta"]["a_tier_skus"]:
            text = self.by_id[sku]["cells"]["renewal_refund_prepaid"]["obligation"]
            for word in kw:
                self.assertIn(word, text)

    def test_a_tier_aigc_cells_carry_marking(self):
        words = self.data["meta"]["invariants"]["a_tier_aigc_keywords_any"]
        for sku in self.data["meta"]["a_tier_skus"]:
            text = self.by_id[sku]["cells"]["aigc_mark"]["obligation"]
            self.assertTrue(any(word in text for word in words),
                            "sku %s aigc cell lacks any marking keyword" % sku)

    def test_a_tier_cosign_is_pending(self):
        token = self.data["meta"]["invariants"]["cosign_pending_token"]
        for sku in self.data["meta"]["a_tier_skus"]:
            self.assertEqual(self.by_id[sku][scm.COSIGN_KEY]["status"], token)


class BillingGateTest(unittest.TestCase):
    """AC-CM4-5: no billing before table pass (rider mechanically enforced)."""

    def setUp(self):
        self.data = scm.load_map()

    def test_gate_closed_while_cosign_pending(self):
        open_, reasons = scm.billing_gate_open(self.data)
        self.assertFalse(open_)
        self.assertTrue(reasons)
        joined = " | ".join(reasons)
        self.assertIn("co-sign pending", joined)

    def test_gate_opens_only_after_cosign_signs(self):
        token = self.data["meta"]["invariants"]["cosign_pending_token"]
        for row in self.data["in_force_skus"]:
            if row["id"] in self.data["meta"]["a_tier_skus"]:
                row[scm.COSIGN_KEY]["status"] = "SIGNED_BIGCOMPUTE"
        open_, reasons = scm.billing_gate_open(self.data)
        self.assertTrue(open_)
        self.assertEqual(reasons, [])
        # sanity: token no longer referenced in gate reasons
        self.assertNotIn(token, " ".join(reasons))

    def test_tampered_pending_cell_blocks_gate(self):
        by_id = {r["id"]: r for r in self.data["in_force_skus"]}
        by_id["C2-B"]["cells"]["minor_limit"]["status"] = "pending"
        open_, reasons = scm.billing_gate_open(self.data)
        self.assertFalse(open_)
        self.assertTrue(any("minor_limit" in r for r in reasons))


class RenderTest(unittest.TestCase):
    """AC-CM4-6: rendered table carries all rows and column headers."""

    def setUp(self):
        self.data = scm.load_map()
        self.table = scm.render_markdown(self.data)

    def test_all_32_ids_present(self):
        for row in self.data["in_force_skus"]:
            self.assertIn(row["id"], self.table)

    def test_five_column_labels_and_cosign_header(self):
        meta = self.data["meta"]
        for key in meta["column_keys"]:
            self.assertIn(meta["column_labels"][key], self.table)
        self.assertIn(meta["cosign_label"], self.table)

    def test_gate_status_line_rendered_closed(self):
        self.assertIn("BILLING GATE: CLOSED", self.table)


if __name__ == "__main__":
    unittest.main(verbosity=2)
