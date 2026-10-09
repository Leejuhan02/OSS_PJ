"""공통 모델(domain/models.py)의 계약 테스트. 네트워크·외부 패키지 없이 실행됨."""

import unittest

from oss_check.domain.models import (
    RISK_ORDER, Judgement, LicenseInfo, Package, Report, Row, Tier,
)


class PackageTests(unittest.TestCase):
    def test_direct_package_has_depth_zero(self):
        self.assertEqual(Package("requests").depth, 0)
        self.assertEqual(Package("idna", "3.7", direct=False, depth=1).version, "3.7")

    def test_direct_and_depth_must_agree(self):
        for kwargs in ({"direct": True, "depth": 1}, {"direct": False, "depth": 0}, {"direct": False, "depth": -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Package("x", **kwargs)

    def test_name_must_not_be_blank(self):
        for name in ("", " requests"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                Package(name)


class LicenseInfoTests(unittest.TestCase):
    def test_single_identifier(self):
        lic = LicenseInfo.single("requests", "Apache-2.0", confidence="확실", origin="license_expression",
                                 raw="Apache-2.0")
        self.assertEqual(lic.options, (frozenset({"Apache-2.0"}),))
        self.assertEqual(lic.identifiers, frozenset({"Apache-2.0"}))

    def test_or_and_expansion_shape(self):
        lic = LicenseInfo("x", (frozenset({"MPL-2.0", "Apache-2.0"}), frozenset({"MPL-2.0", "MIT"})),
                          "확실", "license_expression", "MPL-2.0 AND (Apache-2.0 OR MIT)")
        self.assertEqual(lic.identifiers, frozenset({"MPL-2.0", "Apache-2.0", "MIT"}))

    def test_unknown(self):
        lic = LicenseInfo.unknown("x", raw="Some custom terms")
        self.assertIsNone(lic.options)
        self.assertEqual((lic.confidence, lic.origin, lic.raw), ("미상", "none", "Some custom terms"))
        self.assertEqual(lic.identifiers, frozenset())

    def test_raw_must_be_string(self):
        # 판정 단계에서 raw.lower()가 터지던 문제를 만드는 순간 막음
        for raw in (None, ("License :: OSI Approved :: MIT License",)):
            with self.subTest(raw=raw), self.assertRaises(TypeError):
                LicenseInfo("x", (frozenset({"MIT"}),), "추정", "classifiers", raw)

    def test_unknown_state_must_be_consistent(self):
        bad = [
            (None, "확실", "license"),                                # options 없는데 확실
            ((frozenset({"MIT"}),), "미상", "none"),                  # options 있는데 미상
            ((frozenset({"MIT"}),), "확실", "none"),                  # options 있는데 출처 없음
            ((frozenset({"MIT"}),), "확실", "classifiers"),           # classifier인데 확실
        ]
        for options, confidence, origin in bad:
            with self.subTest(options=options, confidence=confidence, origin=origin), self.assertRaises(ValueError):
                LicenseInfo("x", options, confidence, origin)

    def test_options_shape_is_checked(self):
        for options in ((), (frozenset(),), ({"MIT"},), (frozenset({""}),), [frozenset({"MIT"})]):
            with self.subTest(options=options), self.assertRaises(ValueError):
                LicenseInfo("x", options, "확실", "license")

    def test_unknown_labels_are_rejected(self):
        with self.assertRaises(ValueError):
            LicenseInfo("x", (frozenset({"MIT"}),), "certain", "license")
        with self.assertRaises(ValueError):
            LicenseInfo("x", (frozenset({"MIT"}),), "확실", "expression")


class JudgementTests(unittest.TestCase):
    def test_reason_is_required(self):
        for reason in ("", "   "):
            with self.subTest(reason=reason), self.assertRaises(ValueError):
                Judgement("x", "써도 됨", reason)

    def test_unknown_verdict_is_rejected(self):
        with self.assertRaises(ValueError):
            Judgement("x", "OK", "사유")


class ReportTests(unittest.TestCase):
    @staticmethod
    def row(name, verdict, direct=True):
        return Row(Package(name, direct=direct, depth=0 if direct else 1),
                   LicenseInfo.single(name, "MIT", confidence="확실", origin="license"),
                   Judgement(name, verdict, "사유"))

    def test_rows_sorted_by_risk_then_name(self):
        report = Report("MIT", [self.row("b", "써도 됨"), self.row("a", "써도 됨"),
                                self.row("z", "안 됨", direct=False), self.row("m", "조건 있음")])
        self.assertEqual([r.package.name for r in report.sorted_rows()], ["z", "m", "a", "b"])

    def test_counts(self):
        report = Report("MIT", [self.row("a", "써도 됨"), self.row("b", "써도 됨", direct=False)])
        self.assertEqual(report.counts(), {"total": 2, "direct": 1, "transitive": 1})

    def test_row_names_must_match(self):
        with self.assertRaises(ValueError):
            Row(Package("a"), LicenseInfo.unknown("b"), Judgement("a", "모름", "사유"))

    def test_risk_order_and_tier(self):
        self.assertEqual(min(RISK_ORDER, key=RISK_ORDER.get), "안 됨")
        self.assertLess(Tier.WEAK_COPYLEFT, Tier.STRONG_COPYLEFT)
        self.assertEqual(Tier(1), Tier.PERMISSIVE)


if __name__ == "__main__":
    unittest.main()
