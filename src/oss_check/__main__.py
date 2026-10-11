"""명령줄 실행 (R0) — IF-UI-04.

    python -m oss_check requirements.txt
    python -m oss_check requirements.txt --project Apache-2.0

웹과 같은 app.service.analyze() 를 부르고, Report 를 위험 순으로 출력함.
출력은 cp949(윈도우 기본 인코딩)로도 쓸 수 있는 문자만 씀. 파일로 저장(`> 결과.txt`)해도 깨지지 않게 하려는 것임.
종료 코드: 0 분석 완료 / 1 분석하지 못함(파일 없음, 1MB 초과, 필요한 모듈 없음) / 2 인수 오류(argparse)
"""

import argparse
import sys
from collections.abc import Sequence

from oss_check.app.service import ComponentMissing, Identify, Judge, analyze
from oss_check.collect.parser import get_project_license
from oss_check.domain.models import LicenseInfo, Report, Row
from oss_check.domain.ports import PackageSource


def _default_source() -> PackageSource:
    """실제 PyPI 조회 구현 (R4). 설계지침 §4.0 의 이름 adapters.pypi_adapter.PyPIPackageSource"""
    from oss_check.adapters import pypi_adapter
    source_class = getattr(pypi_adapter, "PyPIPackageSource", None)
    if source_class is None:
        raise ComponentMissing("adapters.pypi_adapter.PyPIPackageSource 가 아직 없음 (설계지침 §4.0, R4 담당)")
    return source_class()


def _license_text(lic: LicenseInfo) -> str:
    if lic.options is None:
        return "미상"
    return " OR ".join(" AND ".join(sorted(choice)) for choice in lic.options)


def _row_line(row: Row) -> str:
    package = row.package
    name = package.name if package.version is None else f"{package.name} {package.version}"
    kind = "" if package.direct else " (따라옴)"
    return f"[{row.judgement.verdict}] {name}{kind} | {_license_text(row.license)} | {row.judgement.reason}"


def format_report(report: Report) -> str:
    """Report 를 사람이 읽는 글로 바꿈. 정렬은 Report.sorted_rows() 를 그대로 씀 (설계지침 §4.3 web·CLI)."""
    counts = report.counts()
    lines = [
        f"프로젝트 라이선스: {report.project_license}",
        f"패키지 {counts['total']}개 (직접 {counts['direct']} · 따라온 {counts['transitive']}"
        f" · 조회 실패 {counts['failed']})",
        "",
        *map(_row_line, report.sorted_rows()),
    ]
    if report.warnings:
        lines += ["", f"경고 {len(report.warnings)}건", *(f"- {w}" for w in report.warnings)]
    return "\n".join(lines)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m oss_check",
                                     description="requirements.txt 의 패키지 라이선스를 점검함")
    parser.add_argument("path", help="requirements.txt 경로")
    parser.add_argument("--project", default=None, help="내 프로젝트 라이선스 SPDX ID (기본 MIT)")
    return parser


def main(argv: Sequence[str] | None = None, *, source: PackageSource | None = None,
         identify: Identify | None = None, judge: Judge | None = None) -> int:
    """source·identify·judge 는 테스트에서 가짜를 넣을 때만 씀. 생략하면 실제 구현을 씀."""
    args = _parser().parse_args(argv)
    try:
        with open(args.path, "rb") as file:
            content = file.read()
        report = analyze(content, project=get_project_license(args.project),
                         source=source or _default_source(), identify=identify, judge=judge)
    except (OSError, ValueError, ComponentMissing) as error:     # QR-R-01: 추적 정보 대신 원인
        print(f"분석하지 못함: {error}", file=sys.stderr)
        return 1
    print(format_report(report))
    return 0


if __name__ == "__main__":
    # 다른 모듈이 만든 사유·경고에 cp949 밖 문자가 섞여도 출력 중에 멈추지 않게 함
    sys.stdout.reconfigure(errors="replace")
    sys.exit(main())
