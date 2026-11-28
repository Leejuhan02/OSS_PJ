# BSD 표기 사전 처리 방침

- 작성: R0, 2026-11-28. **결정: 방식 C 채택 (2026-11-28, R0)**
- 대상: R2(별칭 사전·식별 코드), R3(등급표). 함께 볼 문서: `03_별칭사전_확충목록.md`
- 기준 코드: main `01c9f40` (`src/oss_check/resolve/metadata.py`, `src/oss_check/data/license_aliases.json`)
- 근거 데이터: PyPI 다운로드 상위 15,000개(목록 갱신일 2026-11-01)의 PyPI JSON `info`를 2026-11-28에 수집함. 응답 14,989건, 없음(404) 11건

## 1. 결정

| 항목 | 결정 |
|---|---|
| 조항 수가 드러난 BSD 표기 16종 (3.1절) | 기존 별칭 사전 `license_aliases.json`에 추가함 |
| 조항 수가 없는 `BSD`·`BSD License` | `BSD-3-Clause`로 식별하고, 어느 필드에서 왔든 신뢰 수준은 **「추정」**으로 기록함 (방식 C) |
| 방식 C의 구현 | 새 데이터 파일 `data/license_aliases_estimated.json`(「추정 별칭」)과 식별 코드 수정. R2가 구현함 |
| 범위 | BSD뿐 아니라 확충 목록의 모호 계열 C3를 같은 파일에 넣음. 24항목 중 `Public Domain`은 R3가 판정 규칙을 고친 뒤에 넣음 (아래 근거 4번째) |

선택 근거

- 식별 범위가 가장 넓음: 상위 3,000개 식별률이 88.0%에서 95.4%로, `Public Domain`까지 넣으면 95.6%로 오름 (사전만 넣는 방식 B와 같음)
- 정확도가 가장 높음: 조항 수를 모르는 표기는 모두 「추정」으로 남음. 「확실」은 원문에 계열·버전이 드러난 경우에만 남음. FR-JDG-12에 따라 판정 사유에 「(신뢰 수준: 추정)」이 붙어 사용자가 구분할 수 있음
- 판정 결과는 바뀌지 않음: BSD 2·3·4조항은 모두 등급표 1등급이라, 대표 ID를 무엇으로 정해도 판정은 같음
- `Public Domain`을 먼저 넣지 않는 이유: SPDX에 맞는 ID가 없어 `LicenseRef-Public-Domain`을 써야 하는데, 지금 판정 규칙은 `LicenseRef-`로 시작하는 ID를 모두 독점(「안 됨」)으로 처리함. 규칙을 고치기 전에 넣으면 퍼블릭 도메인 패키지가 「안 됨」으로 잘못 나옴

## 2. 현재 동작

| 항목 | 내용 |
|---|---|
| 정규화 (FR-LIC-03) | 첫 줄만 사용, URL 제거, 공백 정리, 대소문자 무시, 끝의 `license`·`licence` 제거. 그래서 `BSD`, `BSD License`, `BSD license`, `BSD Licence`는 모두 같은 키 `bsd`가 됨 |
| 조회 순서 | `license_expression` → `license` → classifier. 앞 단계에서 식별되면 멈춤 |
| 신뢰 수준 | `license_expression`·`license`에서 식별하면 「확실」, classifier에서만 식별하면 「추정」. 지금 사전 값에는 신뢰 수준이 없음 |
| 사전 규칙 | 값은 유효한 SPDX ID나 `LicenseRef-…` 하나만 가능. SPDX ID 자체를 다른 ID로 바꾸는 별칭은 불러올 때 오류가 남 |
| 기존 방침 | `BSD License`, `GPL License`, `Apache License` 같은 일반 명칭은 미상으로 남김 (`data/README.md`, `data/license_aliases.md`). 이 문서로 바뀜 |
| 선례 | `Apache Software License` → `Apache-2.0`은 이미 사전에 있음. 버전이 없는 classifier를 2.0으로 매핑한 것임. SRS 4.2절에도 「`Apache Software License` (classifier) → `Apache-2.0`, 신뢰 추정」으로 적혀 있음 |

정규화 때문에 `BSD`와 `BSD License`는 같은 키임. 기존 사전에 넣으면 `license` 필드와 classifier에 함께 적용되고, `license` 필드 쪽은 「확실」이 됨. 방식 C가 필요한 이유임.

### 이미 식별되는 BSD 표기 (추가 불필요)

`BSD-3-Clause`, `BSD 3-Clause`, `BSD 3-Clause License`, `3-Clause BSD License`, `3-clause BSD`, `New BSD`, `New BSD License`, `Modified BSD License`, `Revised BSD License`, `BSD-3`, `BSD-2-Clause`, `BSD 2-Clause`, `BSD-2`, `2-clause BSD`, `Simplified BSD`, `Simplified BSD License`, `BSD 4-Clause`, `BSD-4-Clause`, `0BSD`

### 상위 15,000개에서 식별된 BSD 계열 분포

| SPDX ID | 패키지 수 |
|---|---:|
| BSD-3-Clause | 755 |
| BSD-2-Clause | 164 |
| 0BSD | 8 |
| BSD-3-Clause-LBNL | 5 |
| BSD-3-Clause-Clear | 2 |
| BSD-4-Clause, BSD-2-Clause-Views, BSD-1-Clause | 각 1 |

2조항·3조항으로 식별된 919개 중 755개(약 82%)가 3조항임. 대표 ID를 `BSD-3-Clause`로 정한 근거임.

## 3. 처리 내용

### 3.1 기존 사전에 추가: 조항 수가 드러난 표기

상위 15,000개에서 관측한 표기와 PyPI 공식 classifier임. 정규화 후 키가 겹치지 않고, 대상 ID가 모두 SPDX 3.29.0에 있으며, 넣어도 기존 테스트가 모두 통과함.

| 원문 표기 | 대상 ID | 관측 수 (15,000 / 3,000) | 예시 패키지 |
|---|---|---|---|
| `BSD 3` | BSD-3-Clause | 5 / 0 | ddapm-test-agent, pymonctl |
| `BSD (3-clause)` | BSD-3-Clause | 4 / 0 | findspark, pyriemann |
| `BSD 3 clause` | BSD-3-Clause | 2 / 0 | feature-engine, boruta |
| `BSD3` | BSD-3-Clause | 1 / 0 | flagsmith-flag-engine |
| `BSD (3 clause)` | BSD-3-Clause | 1 / 0 | ptable |
| `NewBSD` | BSD-3-Clause | 1 / 0 | watermark |
| `BSD 3-clause "New" or "Revised License"` | BSD-3-Clause | 1 / 0 | redfish |
| `Revised BSD License (LICENSE.txt)` | BSD-3-Clause | 1 / 0 | json-tricks |
| `" BSD-3-Clause"` | BSD-3-Clause | 1 / 0 | fsql |
| `BSD2` | BSD-2-Clause | 4 / 0 | pephubclient, eido |
| `FreeBSD` | BSD-2-Clause | 3 / 2 | parameterized, pycocotools |
| `BSD 2 Clause` | BSD-2-Clause | 1 / 0 | libbs |
| `Two-clause BSD license` | BSD-2-Clause | 1 / 0 | whoosh |
| `The BSD 2-Clause License` | BSD-2-Clause | 1 / 1 | justext |
| `Zero-Clause BSD (0BSD)` | 0BSD | 0 / 0 | PyPI 공식 classifier |
| `LBNL BSD` | BSD-3-Clause-LBNL | 1 / 0 | cppyy-backend |

- `FreeBSD`: 옛 SPDX ID `BSD-2-Clause-FreeBSD`는 폐기되어 `BSD-2-Clause`로 통합됐음
- `BSD-3-Clause-LBNL`은 등급표에 없음. R3가 등급을 넣기 전까지는 「판단보류」로 나옴

### 3.2 추정 별칭 파일에 추가: `BSD`, `BSD License`

| 관측 | 15,000개 | 상위 3,000개 | 예시 |
|---|---:|---:|---|
| `license` 필드가 `BSD`·`BSD License` 등 (키 `bsd`) | 494 | 95 | numba, sympy, torchvision, httpie |
| `license`로 식별이 안 되고 classifier `BSD License`만 있음 | 355 | 98 | jinja2, scipy, seaborn, itsdangerous |
| 합계 | 865 | 196 | |

원문 철자는 `BSD` 446건, `BSD License` 39건, `BSD license` 8건, `BSD Licence` 1건임.

`data/license_aliases_estimated.json`에 넣을 BSD 항목

```json
{
  "BSD": "BSD-3-Clause",
  "BSD License": "BSD-3-Clause",
  "'BSD'": "BSD-3-Clause"
}
```

- `BSD`와 `BSD License`는 정규화 후 같은 키지만, 원문 근거를 남기기 위해 둘 다 적음. 같은 ID를 가리키므로 충돌 오류는 나지 않음
- 나머지 모호 계열 20항목은 `03_별칭사전_확충목록.md` 부록 C에 있음 (`Public Domain` 제외)

### 3.3 방식 C 동작 명세 (R2 구현용)

| 경우 | 지금 | 바뀐 뒤 |
|---|---|---|
| `license`가 `BSD` | 미상 | BSD-3-Clause, **추정**, origin `license` |
| classifier가 `BSD License`뿐 | 미상 | BSD-3-Clause, 추정, origin `classifiers` |
| `license_expression`이 `BSD License OR MIT` | 미상 | 선택지 {BSD-3-Clause}, {MIT}, **추정**, origin `license_expression` |
| `license`가 `BSD-3-Clause`·`New BSD License` | BSD-3-Clause, 확실 | 그대로 |
| `license`가 `BSD-like`·`BSD-style` | 미상 | 그대로 미상 |

규칙

1. `LicenseResolver`가 `license_aliases.json`과 함께 `license_aliases_estimated.json`을 읽음. 형식과 불러오기 검사(유효 ID, 정규화 후 충돌 금지)는 기존 사전과 같음
2. 두 파일의 정규화 키가 겹치면 불러올 때 오류로 처리함 (같은 표기가 확실과 추정 둘 다가 되지 않게)
3. 이름 변환 순서는 「SPDX ID → `LicenseRef-` → 기존 사전 → SPDX 공식 이름 → 추정 별칭」으로 함. 추정 별칭을 맨 뒤에 두어 기존 식별 결과가 바뀌지 않게 함
4. 한 번의 조회에서 피연산자 중 하나라도 추정 별칭으로 변환됐으면, 그 결과의 신뢰 수준은 「추정」으로 기록함. origin과 raw는 지금 규칙대로 둠
5. classifier 단계는 지금처럼 항상 「추정」임
6. `data_dir`로 데이터 폴더를 바꾸는 기존 테스트가 깨지지 않도록, 추정 별칭 파일이 없으면 빈 사전으로 봄 (예외 목록 파일과 같은 처리)

시험 구현 결과 (작업 공간에서만 시험함. 저장소에는 넣지 않음. 기존 사전에 C1·C2, 추정 별칭에 `Public Domain`을 뺀 C3 23항목)

| 항목 | 값 |
|---|---|
| 상위 3,000개 | 확실 2,330 · 추정 531 · 미상 139 (식별률 95.4%) |
| 그중 `license` 필드인데 추정으로 기록된 것 | 115 |
| 상위 15,000개 | 확실 10,854 · 추정 2,906 · 미상 1,229 (식별률 91.8%) |

「확실」 수는 C1·C2만 넣었을 때와 같음. 모호한 매핑이 「확실」을 늘리지 않는다는 뜻임.

### 3.4 처리하지 않는 BSD 관련 표기

| 표기 | 관측 수 | 이유 |
|---|---:|---|
| `BSD-derived (…)`, `BSD-like (…)`, `BSD-style`, `opensource, BSD-style` | 10 | BSD와 「비슷한」 별도 라이선스임 (예: Repoze). 같은 라이선스가 아님 |
| `BSD, Public Domain`, `MIT, BSD`, `Apache-2.0 or BSD`, `GPLv3+/BSD`, `FreeBSD and LGPLv3+` 등 | 9 | 라이선스 여러 개를 쉼표·슬래시로 적음. 사전 값은 ID 하나만 가능함 |
| `BSD license (see LICENSE.txt for details), Copyright (c) 2000-2025, …` (reportlab) | 2 | 연도가 들어 있어 해마다 키가 바뀜 |
| `LICENSE.BSD3` (ddtrace) | 1 | 파일 이름임. 넣을지는 R2 판단 |

## 4. 작업 순서와 담당

| # | 할 일 | 담당 | 비고 |
|---|---|---|---|
| 1 | 방식 C 테스트 작성 (RED) | R2 | 5절의 새 테스트 예 |
| 2 | 추정 별칭 파일 읽기·신뢰 수준 처리 구현 (GREEN) | R2 | 3.3절 규칙 |
| 3 | 3.1절 16종과 확충 목록 C1·C2를 기존 사전에 추가 | R2 | 확충 목록 부록 B |
| 4 | 3.2절 BSD와 확충 목록 C3를 추정 별칭 파일에 추가 | R2 | 확충 목록 부록 C |
| 5 | 기존 정책 테스트 9개 수정 | R2 | 5절. 같은 PR에서 함 |
| 6 | `data/README.md`, `data/license_aliases.md`의 「일반 명칭은 매핑하지 않음」 문구 수정 | R2 | |
| 7 | 등급표에 없는 대상 ID 등급 추가 (`BSD-3-Clause-LBNL` 등) | R3 | 확충 목록 부록 A |
| 7-1 | 독점 규칙에 `LicenseRef-Public-Domain` 예외(0등급) 추가. 끝나면 R2가 추정 별칭에 `Public Domain` 추가 | R3 → R2 | 확충 목록 5절 |
| 8 | SRS FR-LIC-08에 「모호한 별칭에서 얻은 결과도 추정」 추가, 설계지침 §4 데이터 파일 목록에 추정 별칭 파일 추가 | R0 | |

## 5. 바꿔야 할 기존 테스트

방식 C와 C3를 적용하면 아래 R2 테스트 9개가 실패함 (2026-11-28, 기존 사전에 C1·C2·C3를 함께 넣어 실행한 결과. 나머지는 모두 통과. 방식 C로 나눠 넣어도 이 9개는 「미상」을 확인하므로 똑같이 실패함). 모두 「일반 명칭은 미상」이라는 기존 방침을 확인하는 테스트임.

| 테스트 | 실패하는 값 | 바꿀 방향 |
|---|---|---|
| `tests/test_DR_03_expanded_aliases.py::test_unspecified_versions_stay_unknown` | `BSD License`, `GPL License`, `Apache License`, `GNU General Public License (GPL)`, `GNU Library or Lesser General Public License (LGPL)` (5개) | 「미상」 대신 「후보 ID + 추정」을 확인하는 테스트로 바꿈 |
| `tests/test_FR_LIC_01_metadata.py::MetadataResolutionTests::test_ambiguous_generic_license_names_are_unknown` | subTest `BSD License`, `GPL License`, `Apache License` (3개) | 같음 |
| `tests/test_FR_LIC_07_alias_operands.py::test_invalid_alias_expression_falls_back_as_a_whole` | `BSD License OR MIT` (1개) | 예시를 실제로 모르는 이름(예: `Foo License OR MIT`)으로 바꿈 |

- `GPL License`, `Apache License`는 정규화 후 `gpl`, `apache` 키가 되어 C3의 `GPL`, `Apache`와 같아짐
- 테스트를 통과시키려고 고치는 것이 아니라 방침이 바뀌어서 고치는 것임. 이 문서를 근거로 같은 PR에서 바꾸고, PR 본문에 이 문서를 적음 (AGENTS.md 규칙)

새로 둘 테스트 예 (RED 먼저)

```python
@pytest.mark.parametrize("field", ["license", "classifiers"])
def test_ambiguous_bsd_is_estimated_bsd_3_clause(field):
    value = ["License :: OSI Approved :: BSD License"] if field == "classifiers" else "BSD"
    result = identify("pkg", {field: value})
    assert result.options == (frozenset({"BSD-3-Clause"}),)
    assert result.confidence == "추정"


def test_estimated_operand_makes_whole_expression_estimated():
    result = identify("pkg", {"license_expression": "BSD License OR MIT"})
    assert result.options == (frozenset({"BSD-3-Clause"}), frozenset({"MIT"}))
    assert result.confidence == "추정"


def test_explicit_bsd_stays_certain():
    assert identify("pkg", {"license": "New BSD License"}).confidence == "확실"


def test_bsd_like_stays_unknown():
    assert identify("pkg", {"license": "BSD-like"}).options is None
```

## 6. 적용 효과 (같은 날 수집 자료로 재계산)

「식별」은 신뢰 수준이 미상이 아닌 것(확실 또는 추정)임.

| 단계 | 사전 항목 수 (기존 + 추정) | 15,000개 식별률 | 상위 3,000개 식별률 | 상위 3,000개 미상 |
|---|---|---:|---:|---:|
| 현재 main | 50 + 0 | 83.9% | 88.0% | 359 |
| 기존 사전에 C1·C2 추가 (3.1절 포함) | 187 + 0 | 85.6% | 88.5% | 344 |
| + 추정 별칭에 BSD 3항목 | 187 + 3 | 91.2% | 94.9% | 153 |
| + 추정 별칭에 C3 23항목 (결정안 1단계) | 187 + 23 | 91.8% | 95.4% | 139 |
| + R3 규칙 수정 후 `Public Domain` (결정안 2단계) | 187 + 24 | 91.9% | 95.6% | 133 |

- 현재 main은 상위 3,000개 기준 88.0%로, 이 수집 기준에서는 QR-A-02(90% 이상)에 못 미침. 결정안을 적용하면 QR-A-02와 QR-A-03(95% 이상, 권장)을 모두 넘음
- 남은 미상 중 상위 3,000개의 88건은 PyPI `info`에 라이선스 정보가 아예 없음. 사전이 아니라 FR-LIC-11(PEP 658 메타데이터 재조회, 권장)의 범위임

## 7. 재현 방법

작업 공간 스크립트로 계산했음. 스크립트와 수집 자료는 저장소에 넣지 않았음.

1. 상위 목록: `https://hugovk.github.io/top-pypi-packages/top-pypi-packages.min.json` (15,000개, 2026-11-01 갱신)
2. 각 패키지의 `https://pypi.org/pypi/<이름>/json`에서 `license`, `license_expression`, `License ::` classifier만 저장 (동시 16개, 약 82초)
3. `LicenseResolver().resolve(info)`로 신뢰 수준을 셈. 사전을 바꾼 경우는 `LicenseResolver(data_dir=…)`에 수정한 사전을 넣어 다시 셈
4. 방식 C는 `LicenseResolver`를 상속한 시험용 클래스로 계산함 (추정 별칭에서 변환된 경우 「확실」을 「추정」으로 바꿈)
