# src/oss_check/resolve

PyPI `info` 메타데이터에서 라이선스와 괄호 없는 복합식을 식별함 (R2).

```python
from oss_check.resolve import identify

result = identify("example-pkg", {
    "license_expression": None,
    "license": "UNKNOWN",
    "classifiers": ["License :: OSI Approved :: Apache Software License"],
})
assert result.options == (frozenset({"Apache-2.0"}),)
assert result.confidence == "추정"
assert result.origin == "classifiers"
```

## 이번 작업 범위

- FR-LIC-01: `license_expression` → `license` → `classifiers` 중 처음 변환 성공한 단계 사용.
- FR-LIC-02·03: legacy license는 원문 200자 초과 시 건너뜀. 첫 줄, URL, 공백, 대소문자, license/licence 접미어 정규화.
- FR-LIC-08~10: classifier는 추정, 변환 실패는 미상. 성공 단계·원문과 시도한 문자열 근거를 보존.
- SPDX 3.29.0 목록의 단일 ID와 공식 이름, 초기 별칭 지원. `LicenseRef-*`는 R3 판정을 위해 유지.
- DR-02: SPDX 3.29.0 예외 86종 동봉.
- FR-LIC-05·06: 괄호 없는 AND/OR/WITH, OR 선택지와 AND 동시 적용을 지원.
  WITH는 공식 예외 이름을 확인하고 기본 라이선스 ID를 선택지에 남김. 예외는 원문에 보존.
  알 수 없는 예외·잘못된 식은 해당 단계 실패 후 다음 필드로 이동하는 보수적 정책을 사용함.
- FR-LIC-07: 피연산자에 기존 별칭 사전을 적용함. 사전에 등록된 이름 속 괄호
  (`ISC License (ISCL)` 등)는 허용하지만 그룹·중첩 괄호는 해석하지 않음.
  미상 피연산자가 있으면 식 전체를 실패 처리하며 일부 ID만 반환하지 않음.
- 로컬 JSON만 사용. 네트워크 요청·업로드 저장·로그 출력 없음.

이 결과는 라이선스 **식별**이며 사용 가능 여부 판정은 R3 `judge/`에서 수행함.
공개 계약은 `identify(name, info) → LicenseInfo`임 (설계지침 §4.0·4.3).
`LicenseResolution`과 `resolve_license()`는 R2 내부 구현이며 다른 모듈에는 전달하지 않음.
기존 R2 단위 테스트용 `LicenseResolver`·`resolve_license` import는 호환 목적으로 유지함.

## 후속 작업

- FR-LIC-04 / DR-03: 별칭 40종 이상과 표본 변환율 검증. 80종 이상은 DR-06 권장 범위. 현재 초기 사전은 19개 표기이며 정규화 후 중복이 있음.
- FR-LIC-12: 괄호·중첩 표현식 파서 (권장). 현재 괄호식은 미지원.
- IF-SW-13 기동 시 초기화 및 함수 전략 목록 구조는 후속 범위.
- 복수의 서로 다른 라이선스 classifier 또는 미해석 license classifier가 함께 있으면 미상. 결합 관계를 추측하지 않음.
- FR-LIC-11: PEP 658 재조회 (권장 범위, R4와 연동).

## 공개 결과 필드

| 필드 | 의미 |
|---|---|
| `package` | 입력으로 받은 패키지 이름 그대로 |
| `options` | OR는 여러 frozenset, AND는 한 frozenset 안의 ID들. 단일은 `(frozenset({ID}),)`, 실패 시 None |
| `confidence` | 확실 / 추정 / 미상 |
| `origin` | license_expression / license / classifiers, 미상은 none |
| `raw` | 항상 문자열. 성공한 필드의 원문 전체, classifier는 줄바꿈 연결 |

미상일 때는 확인한 첫 필드의 원문을 보존함 (expression → license → classifiers 순).
원문이 없으면 빈 문자열. 시도한 모든 필드의 근거는 내부 `LicenseResolution.evidence`에 유지함.

SPDX 데이터와 사전은 프로세스 첫 사용 시 읽어 재사용함. JSON 수정 후 재시작하거나
`LicenseResolver(data_dir=...)`로 새 인스턴스를 만들면 반영됨.

## 오프라인 테스트

팀 테스트 표준은 Python 3.11 가상환경임. 프로젝트 루트의 `.venv`가 3.11인지
먼저 확인하고 개발 의존성을 설치한 뒤 실행함 (Windows PowerShell):

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
```

`test_FR_LIC_01_identify.py`는 외부 조회만 가짜 `PackageSource`로 바꾸고,
실제 `analyze()` → `identify()` → `judge()` 연결과 공통 모델 반환을 검증함.

`test_FR_LIC_05_expressions.py`는 정상·잘못된 식·폴백·원문 보존,
`test_FR_LIC_06_options.py`는 혼합식 우선순위·선택지 구조·중복 제거를 검증함.
`test_FR_LIC_07_alias_operands.py`는 기존 별칭 전체의 AND/OR/WITH 적용,
오른쪽 피연산자·정규화·사전 교체·폴백·잘못된 괄호 거부·실제 분석 연결을 검증함.
내부 `LicenseResolution.identifier`는 선택지가 단일 ID일 때만 채워지므로
복합식의 성공 여부는 `options is not None`으로 확인해야 함.
