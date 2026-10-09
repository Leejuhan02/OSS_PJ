"""FR-LIC-01~03·08~10의 오프라인 회귀 테스트."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from oss_check.resolve import LicenseResolver, resolve_license


MIT_CLASSIFIER = "License :: OSI Approved :: MIT License"
APACHE_CLASSIFIER = "License :: OSI Approved :: Apache Software License"


class MetadataResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = LicenseResolver()

    def test_expression_wins_over_legacy_license_and_classifiers(self):
        result = self.resolver.resolve({
            "license_expression": "GPL-3.0-only", "license": "MIT",
            "classifiers": [APACHE_CLASSIFIER],
        })
        self.assertEqual((result.identifier, result.source, result.confidence),
                         ("GPL-3.0-only", "license_expression", "확실"))

    def test_invalid_expression_falls_back_to_legacy_license(self):
        result = self.resolver.resolve({"license_expression": "not-a-license", "license": "MIT"})
        self.assertEqual((result.identifier, result.source), ("MIT", "license"))
        self.assertEqual([item.source for item in result.evidence], ["license_expression", "license"])

    def test_legacy_license_wins_over_classifiers(self):
        result = self.resolver.resolve({"license": "GPL-3.0-only", "classifiers": [MIT_CLASSIFIER]})
        self.assertEqual(result.identifier, "GPL-3.0-only")

    def test_invalid_legacy_license_falls_back_to_inferred_classifier(self):
        result = self.resolver.resolve({"license": "UNKNOWN", "classifiers": [APACHE_CLASSIFIER]})
        self.assertEqual((result.identifier, result.source, result.confidence),
                         ("Apache-2.0", "classifiers", "추정"))

    def test_long_legacy_text_is_skipped_before_normalizing_first_line(self):
        for length in (201, 74646):
            with self.subTest(length=length):
                raw = "MIT License\n" + "x" * (length - len("MIT License\n"))
                result = self.resolver.resolve({"license": raw, "classifiers": [APACHE_CLASSIFIER]})
                self.assertEqual(result.identifier, "Apache-2.0")
                self.assertEqual(result.evidence[0].raw, raw)

    def test_exact_200_character_legacy_text_is_not_skipped(self):
        raw = "MIT License\n" + "x" * (200 - len("MIT License\n"))
        self.assertEqual(self.resolver.resolve({"license": raw}).identifier, "MIT")

    def test_first_line_url_whitespace_case_and_suffix_normalization(self):
        for raw in ("MIT License\n\nCopyright...", "  mIt   LiCeNcE  ",
                    "MIT License (https://opensource.org/license/mit)",
                    "MIT License https://opensource.org/license/mit"):
            with self.subTest(raw=raw):
                result = self.resolver.resolve({"license": raw})
                self.assertEqual(result.identifier, "MIT")
                self.assertEqual(result.raw, raw)

    def test_structured_expression_does_not_discard_subsequent_lines(self):
        self.assertEqual(self.resolver.resolve({"license_expression": "MIT\nOR GPL-3.0-only"}).confidence,
                         "미상")

    def test_unsupported_expression_is_not_partially_accepted(self):
        for raw in ("MIT OR GPL-3.0-only", "MIT AND UNKNOWN", "(MIT)",
                    "Apache-2.0 WITH LLVM-exception", "MIT, GPL-3.0-only"):
            with self.subTest(raw=raw):
                result = self.resolver.resolve({"license_expression": raw})
                self.assertIsNone(result.identifier)
                self.assertEqual(result.confidence, "미상")

    def test_unknown_has_original_evidence(self):
        result = self.resolver.resolve({"license": "Some custom terms", "classifiers": ["License :: Unknown"]})
        self.assertIsNone(result.source)
        self.assertEqual(result.confidence, "미상")
        self.assertEqual(result.evidence[0].raw, "Some custom terms")
        self.assertEqual(result.evidence[1].raw, ("License :: Unknown",))

    def test_absent_empty_and_wrong_field_types_are_unknown(self):
        for metadata in ({}, {"license_expression": None, "license": "   "},
                         {"license_expression": ["MIT"], "license": 42, "classifiers": MIT_CLASSIFIER}):
            with self.subTest(metadata=metadata):
                self.assertEqual(self.resolver.resolve(metadata).confidence, "미상")

    def test_non_license_classifier_does_not_become_a_license(self):
        self.assertEqual(self.resolver.resolve({"classifiers": ["Topic :: MIT License"]}).confidence, "미상")

    def test_multiple_different_license_classifiers_are_not_guessed(self):
        self.assertEqual(self.resolver.resolve({"classifiers": [MIT_CLASSIFIER, APACHE_CLASSIFIER]}).confidence,
                         "미상")

    def test_unknown_classifier_prevents_partial_acceptance(self):
        self.assertEqual(self.resolver.resolve({"classifiers": [MIT_CLASSIFIER, "License :: Unknown"]}).confidence,
                         "미상")

    def test_duplicate_and_category_classifiers_do_not_conflict(self):
        result = self.resolver.resolve({"classifiers": ["License :: OSI Approved", MIT_CLASSIFIER, MIT_CLASSIFIER]})
        self.assertEqual((result.identifier, result.confidence), ("MIT", "추정"))

    def test_ambiguous_generic_license_names_are_unknown(self):
        for value in ("BSD License", "GPL License", "Apache License"):
            with self.subTest(value=value):
                self.assertEqual(self.resolver.resolve({"license": value}).confidence, "미상")

    def test_case_insensitive_standard_ids_and_official_names(self):
        self.assertEqual(self.resolver.resolve({"license": "apache-2.0"}).identifier, "Apache-2.0")
        self.assertEqual(self.resolver.resolve({"license": "GNU General Public License v3.0 only"}).identifier,
                         "GPL-3.0-only")

    def test_catalog_identifier_is_accepted_even_without_a_judgment_grade(self):
        self.assertEqual(self.resolver.resolve({"license_expression": "MIT-0"}).identifier, "MIT-0")

    def test_proprietary_classifier_and_license_ref_are_preserved(self):
        result = self.resolver.resolve({"classifiers": ["License :: Other/Proprietary License"]})
        self.assertEqual(result.identifier, "LicenseRef-Proprietary")
        self.assertEqual(result.confidence, "추정")
        self.assertEqual(self.resolver.resolve({"license_expression": "LicenseRef-Company"}).identifier,
                         "LicenseRef-Company")

    def test_alias_data_can_be_replaced_without_changing_code(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            path.joinpath("spdx_licenses.json").write_text(json.dumps({
                "licenses": [{"licenseId": "MIT", "name": "MIT License"}],
            }), encoding="utf-8")
            path.joinpath("license_aliases.json").write_text(json.dumps({"Team alias": "MIT"}), encoding="utf-8")
            self.assertEqual(LicenseResolver(path).resolve({"license": "Team alias"}).identifier, "MIT")
            path.joinpath("license_aliases.json").write_text(json.dumps({"Team alias": "NOT-SPDX"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                LicenseResolver(path)

    def test_offline_public_entrypoint(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
            self.assertEqual(resolve_license({"license_expression": "MIT"}).identifier, "MIT")


if __name__ == "__main__":
    unittest.main()
