# src/oss_check/resolve

PyPI `info` 메타데이터에서 단일 라이선스를 식별함 (R2).

```python
from oss_check.resolve import resolve_license

result = resolve_license({
    "license_expression": None,
    "license": "UNKNOWN",
    "classifiers": ["License :: OSI Approved :: Apache Software License"],
})
assert result.identifier == "Apache-2.0"
assert result.confidence == "추정"
```

## 이번 작업 범위

- FR-LIC-01: `license_expression` → `license` → `classifiers` 중 처음 변환 성공한 단계 사용.
- FR-LIC-02·03: legacy license는 원문 200자 초과 시 건너뜀. 첫 줄, URL, 공백, 대소문자, license/licence 접미어 정규화.
- FR-LIC-08~10: classifier는 추정, 변환 실패는 미상. 성공 단계·원문과 시도한 문자열 근거를 보존.
- SPDX 3.29.0 목록의 단일 ID와 공식 이름, 초기 별칭 지원. `LicenseRef-*`는 R3 판정을 위해 유지.
- 로컬 JSON만 사용. 네트워크 요청·업로드 저장·로그 출력 없음.

이 결과는 라이선스 **식별**이며 사용 가능 여부 판정은 R3 `judge/`에서 수행함.
공통 모델은 아직 없으므로 R2 내부 데이터클래스를 사용하며 R0 모델 확정 후 연결할 수 있음.

## 후속 작업

- FR-LIC-04 / DR-03: 별칭 80종 이상과 표본 변환율 검증. 현재 초기 사전은 19개 표기이며 정규화 후 중복이 있음.
- FR-LIC-05~07: AND/OR/WITH·괄호 파싱과 선택지 전개. 현재 복합 표현식은 부분 해석하지 않고 다음 필드로 넘어가며, 전부 실패하면 미상.
- 복수의 서로 다른 라이선스 classifier 또는 미해석 license classifier가 함께 있으면 미상. 결합 관계를 추측하지 않음.
- FR-LIC-11: PEP 658 재조회 (권장 범위, R4와 연동).

## 결과 필드

| 필드 | 의미 |
|---|---|
| `identifier` | 식별한 단일 SPDX ID 또는 LicenseRef, 실패 시 None |
| `confidence` | 확실 / 추정 / 미상 |
| `source`, `raw` | 성공한 단계와 변환 전 원문, 실패 시 None |
| `evidence` | 확인한 필드의 단계와 원문 목록. 실패·길이 초과의 근거도 유지 |

SPDX 데이터와 사전은 프로세스 첫 사용 시 읽어 재사용함. JSON 수정 후 재시작하거나
`LicenseResolver(data_dir=...)`로 새 인스턴스를 만들면 반영됨.

## 오프라인 테스트

프로젝트 루트에서 의존성 설치 없이 실행할 수 있음 (Windows PowerShell):

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -p 'test_*.py' -v
```

개발 의존성이 설치되어 있으면 `python -m pytest`로도 실행 가능.
