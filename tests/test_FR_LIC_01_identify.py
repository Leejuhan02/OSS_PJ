"""FR-LIC-01: 공개 식별 함수와 실제 분석 경로가 공통 모델로 연결된다."""

from collections import Counter

import pytest

from oss_check.app.service import analyze
from oss_check.domain.models import LicenseInfo
from oss_check.domain.ports import PackageSource


class OfflineSource(PackageSource):
    """외부 조회만 대체하고 식별·판정은 실제 구현을 사용한다."""

    def __init__(self, infos):
        self.infos = infos
        self.calls = Counter()

    def fetch(self, name):
        self.calls[name] += 1
        return self.infos.get(name)


@pytest.mark.parametrize("info, identifier, origin, raw", [
    ({"license_expression": "MIT", "license": "Apache-2.0"},
     "MIT", "license_expression", "MIT"),
    ({"license_expression": "unrecognized", "license": "Apache-2.0"},
     "Apache-2.0", "license", "Apache-2.0"),
    ({"license": "MIT License\nCopyright example"},
     "MIT", "license", "MIT License\nCopyright example"),
])
def test_identify_returns_common_model(info, identifier, origin, raw):
    """FR-LIC-01: 첫 변환 성공 결과를 패키지 이름과 함께 LicenseInfo로 반환한다."""
    from oss_check.resolve import identify

    assert identify("example-pkg", info) == LicenseInfo.single(
        "example-pkg", identifier, confidence="확실", origin=origin, raw=raw)


def test_analyze_uses_real_identify_and_judge():
    """FR-LIC-01: identify·judge를 주입하지 않아도 전이 의존성까지 판정한다."""
    source = OfflineSource({
        "root-pkg": {"license_expression": "MIT", "requires_dist": ["dep-pkg"]},
        "dep-pkg": {"license": "GPL-3.0-only", "requires_dist": None},
    })

    report = analyze("Root_Pkg", project="MIT", source=source)

    assert [(row.package.name, row.license.identifiers, row.judgement.verdict)
            for row in report.rows] == [
        ("dep-pkg", frozenset({"GPL-3.0-only"}), "안 됨"),
        ("root-pkg", frozenset({"MIT"}), "써도 됨"),
    ]
    assert all(isinstance(row.license, LicenseInfo) for row in report.rows)
    assert all(row.judgement.reason for row in report.rows)
    assert source.calls == {"root-pkg": 1, "dep-pkg": 1}


@pytest.mark.parametrize("info, expected", [
    ({"classifiers": ["License :: OSI Approved :: Apache Software License"]},
     LicenseInfo.single("pkg", "Apache-2.0", confidence="추정", origin="classifiers",
                        raw="License :: OSI Approved :: Apache Software License")),
    ({"classifiers": ["License :: OSI Approved", "License :: OSI Approved :: MIT License"]},
     LicenseInfo.single("pkg", "MIT", confidence="추정", origin="classifiers",
                        raw="License :: OSI Approved\nLicense :: OSI Approved :: MIT License")),
    ({}, LicenseInfo.unknown("pkg")),
    ({"license_expression": None, "license": 42, "classifiers": [None]},
     LicenseInfo.unknown("pkg")),
    ({"license_expression": "unrecognized", "license": "also unrecognized"},
     LicenseInfo.unknown("pkg", raw="unrecognized")),
    ({"license": "unknown text\nCopyright example"},
     LicenseInfo.unknown("pkg", raw="unknown text\nCopyright example")),
    ({"classifiers": ["License :: Custom License"]},
     LicenseInfo.unknown("pkg", raw="License :: Custom License")),
])
def test_identify_preserves_fallback_result(info, expected):
    """FR-LIC-01: classifier·변환 실패도 §4의 신뢰 수준·출처·문자열 원문을 지킨다."""
    from oss_check.resolve import identify

    assert identify("pkg", info) == expected


def test_real_pipeline_handles_classifier_and_unknown():
    """FR-LIC-01: classifier·미상 식별 결과가 실제 판정까지 전달된다."""
    source = OfflineSource({
        "classifier-pkg": {"classifiers": ["License :: OSI Approved :: MIT License"]},
        "unknown-pkg": {"license": "unrecognized"},
    })

    report = analyze("classifier-pkg\nunknown-pkg", project="MIT", source=source)
    rows = {row.package.name: row for row in report.rows}

    assert rows["classifier-pkg"].license.confidence == "추정"
    assert rows["classifier-pkg"].judgement.verdict == "써도 됨"
    assert rows["unknown-pkg"].license == LicenseInfo.unknown("unknown-pkg", raw="unrecognized")
    assert rows["unknown-pkg"].judgement.verdict == "모름"
    assert source.calls == {"classifier-pkg": 1, "unknown-pkg": 1}
