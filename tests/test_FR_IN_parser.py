"""
tests/test_FR_IN_parser.py

FR-IN 요구사항 단위 테스트:
- FR-IN-01: 파일 입력 처리
- FR-IN-02: 텍스트 입력과 파일 입력의 동일성
- FR-IN-03: 주석(#) 및 빈 줄 무시
- FR-IN-04: PEP 508 표기(이름, extras, 버전 지정, 마커) 파싱
- FR-IN-05: 해석 불가 줄(-r, -e, URL 등) 건너뛰기 및 경고 기록
- FR-IN-06: 기본 프로젝트 라이선스 MIT
- FR-IN-07: 이름==버전 형식의 확정 버전(pinned version) 기록
- FR-IN-08: 1MB 초과 입력 거부
"""
import unittest

from oss_check.collect.parser import (
    DEFAULT_PROJECT_LICENSE,
    ParsedRequirement,
    extract_pinned_version,
    get_project_license,
    parse_requirements,
)


class TestFRINParser(unittest.TestCase):
    def test_FR_IN_01_and_02_text_and_bytes_equivalence(self):
        """FR-IN-01, FR-IN-02: 문자열 입력과 바이트(파일) 입력이 동일하게 처리되어야 함."""
        content = "requests==2.31.0\nfastapi>=0.100.0\n"
        reqs_str, warn_str = parse_requirements(content)
        reqs_bytes, warn_bytes = parse_requirements(content.encode("utf-8"))

        self.assertEqual(len(reqs_str), 2)
        self.assertEqual(reqs_str, reqs_bytes)
        self.assertEqual(warn_str, warn_bytes)
        self.assertEqual(reqs_str[0].name, "requests")
        self.assertEqual(reqs_str[1].name, "fastapi")

    def test_FR_IN_03_ignore_comments_and_empty_lines(self):
        """FR-IN-03: 주석(#)과 빈 줄은 무시되어야 함."""
        content = """
        # 전체 줄 주석
        
        requests==2.31.0  # 인라인 주석
           # 공백 뒤 주석
        flask   
        """
        reqs, warnings = parse_requirements(content)
        self.assertEqual(len(reqs), 2)
        self.assertEqual(reqs[0].name, "requests")
        self.assertEqual(reqs[0].pinned_version, "2.31.0")
        self.assertEqual(reqs[1].name, "flask")
        self.assertEqual(len(warnings), 0)

    def test_FR_IN_04_pep508_parsing(self):
        """FR-IN-04: PEP 508 표기(이름, extras, 버전, 마커)를 올바르게 파싱해야 함."""
        content = "requests[security,socks] >= 2.20.0; python_version < '3.12'"
        reqs, warnings = parse_requirements(content)

        self.assertEqual(len(reqs), 1)
        r = reqs[0]
        self.assertEqual(r.name, "requests")
        self.assertEqual(r.extras, frozenset({"security", "socks"}))
        self.assertTrue("python_version" in (r.marker or "") and "3.12" in (r.marker or ""))
        self.assertIsNone(r.pinned_version)  # >= 이므로 pinned_version 아님
        self.assertEqual(len(warnings), 0)

    def test_FR_IN_05_unsupported_lines_warning(self):
        """FR-IN-05: -r, -e, URL 등 지원하지 않는 줄은 건너뛰고 줄 번호와 사유를 기록해야 함."""
        content = """
        requests==2.31.0
        -r requirements-dev.txt
        -e .
        --extra-index-url https://example.com/pypi
        https://github.com/psf/requests/archive/main.zip
        git+https://github.com/foo/bar.git@v1.0
        urllib3==2.0.0
        """
        reqs, warnings = parse_requirements(content)

        self.assertEqual(len(reqs), 2)
        self.assertEqual([r.name for r in reqs], ["requests", "urllib3"])

        # 경고에 건너뛴 줄 번호와 사유가 포함되어 있는지 확인
        self.assertEqual(len(warnings), 5)
        self.assertTrue(any("Line 3" in w and "-r" in w for w in warnings))
        self.assertTrue(any("Line 4" in w and "-e" in w for w in warnings))
        self.assertTrue(any("Line 5" in w and "--extra-index-url" in w for w in warnings))
        self.assertTrue(any("Line 6" in w and "URL" in w for w in warnings))
        self.assertTrue(any("Line 7" in w and "URL" in w for w in warnings))

    def test_FR_IN_06_default_project_license(self):
        """FR-IN-06: 프로젝트 라이선스를 지정하지 않으면 기본값 MIT를 반환해야 함."""
        self.assertEqual(get_project_license(None), DEFAULT_PROJECT_LICENSE)
        self.assertEqual(get_project_license(""), DEFAULT_PROJECT_LICENSE)
        self.assertEqual(get_project_license("   "), DEFAULT_PROJECT_LICENSE)
        self.assertEqual(get_project_license("Apache-2.0"), "Apache-2.0")

    def test_FR_IN_07_pinned_version(self):
        """FR-IN-07: 이름==버전 형태인 경우에만 확정 버전을 추출해야 함."""
        content = """
        pkg1 == 1.2.3
        pkg2 >= 2.0.0
        pkg3 <= 3.0.0
        pkg4 ~= 1.4.2
        pkg5 == 2.1.*
        pkg6
        """
        reqs, warnings = parse_requirements(content)
        self.assertEqual(len(reqs), 6)

        pinned_map = {r.name: r.pinned_version for r in reqs}
        self.assertEqual(pinned_map["pkg1"], "1.2.3")
        self.assertIsNone(pinned_map["pkg2"])
        self.assertIsNone(pinned_map["pkg3"])
        self.assertIsNone(pinned_map["pkg4"])
        self.assertIsNone(pinned_map["pkg5"])
        self.assertIsNone(pinned_map["pkg6"])

    def test_FR_IN_08_input_size_limit(self):
        """FR-IN-08: 입력 크기가 1MB(1,048,576 bytes)를 넘으면 ValueError가 발생해야 함."""
        # 1MB 초과 문자열 생성 (1MB + 10 bytes)
        oversized = "a" * (1_048_576 + 10)
        with self.assertRaises(ValueError) as ctx:
            parse_requirements(oversized)
        self.assertIn("1MB", str(ctx.exception))

        # 1MB 초과 바이트 생성
        oversized_bytes = b"a" * (1_048_576 + 10)
        with self.assertRaises(ValueError) as ctx:
            parse_requirements(oversized_bytes)
        self.assertIn("1MB", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
