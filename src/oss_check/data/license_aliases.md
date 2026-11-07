# 라이선스 별칭 보강 근거

2026-11-06, main `700fe98`의 28개에 22개를 추가함. 원문 키 50개, 정규화 후 49개로 DR-03 필수 40종 이상을 충족함. 표본에서 관측한 이름과 공식 이름의 버전 명시 변형을 구분해 보강했으며, 전체 3,000개 변환율을 측정한 결과는 아님.

## 관측한 표기

| 표기 | SPDX ID | 근거 |
|---|---|---|
| `GNU GPLv3+` | GPL-3.0-or-later | [rfc3987 PyPI](https://pypi.org/project/rfc3987/), [JSON info](https://pypi.org/pypi/rfc3987/json), 동봉 AT-1 응답 사본 |
| `Modified BSD License` | BSD-3-Clause | 동봉 jsonpointer 3.8 응답 사본, [공식 배포 소스의 3개 조항](https://github.com/stefankoegl/python-json-pointer/blob/master/LICENSE.txt) |

rfc3987의 `license_expression`은 없고 `license`는 `GNU GPLv3+`임. 기존 사전에는 이 이름이 없어 미상이 됐음. 패키지 이름에 따른 예외 처리가 아니라 라이선스 문자열을 사전에 등록함. jsonpointer도 같은 방식으로 처리함.

## 공식 classifier·버전 명시 표기

[PyPI 공식 classifier 목록](https://pypi.org/classifiers/)의 버전 있는 GNU 표기를 추가함. 버전이 없는 `GNU General Public License (GPL)`, `GNU Library or Lesser General Public License (LGPL)`은 대상 버전을 추측하지 않음.

| 추가한 이름 묶음 | 대상 ID·기준 |
|---|---|
| GNU GPL v2 / v3의 버전과 `(GPLv2)` / `(GPLv3)`가 있는 classifier | [GPL-2.0-only](https://spdx.org/licenses/GPL-2.0-only.html), [GPL-3.0-only](https://spdx.org/licenses/GPL-3.0-only.html) |
| GNU GPL v2 / v3의 `or later`와 `+`가 있는 classifier | [GPL-2.0-or-later](https://spdx.org/licenses/GPL-2.0-or-later.html), [GPL-3.0-or-later](https://spdx.org/licenses/GPL-3.0-or-later.html) |
| GNU LGPL v2 / v3의 버전 명시 classifier, v3 이후 버전 허용 classifier | [LGPL-2.0-only](https://spdx.org/licenses/LGPL-2.0-only.html), [LGPL-3.0-only](https://spdx.org/licenses/LGPL-3.0-only.html), [LGPL-3.0-or-later](https://spdx.org/licenses/LGPL-3.0-or-later.html) |
| GNU AGPL v3 classifier와 v3 이후 버전 허용 classifier | [AGPL-3.0-only](https://spdx.org/licenses/AGPL-3.0-only.html), [AGPL-3.0-or-later](https://spdx.org/licenses/AGPL-3.0-or-later.html) |
| `GPLv3+`, `GNU GPLv2+`, `LGPLv2.1+`, `LGPLv3+`, `AGPLv3+` | 버전·계열·`+`를 보존한 해당 `-or-later` ID. 버전 없는 이름까지 일반화하지 않음 |
| `New BSD License`, `Revised BSD License`, `BSD 3-Clause License (Revised)` | [BSD-3-Clause 공식 이름과 3개 조항](https://spdx.org/licenses/BSD-3-Clause.html) |
| `BSD 2-Clause License (FreeBSD/Simplified)` | [BSD-2-Clause 공식 이름과 2개 조항](https://spdx.org/licenses/BSD-2-Clause.html) |
| `Mozilla Public License 1.1 (MPL 1.1)` | [공식 MPL-1.1](https://spdx.org/licenses/MPL-1.1.html), PyPI 버전 명시 classifier |
| `Zope Public License 2.1 (ZPL 2.1)` | [공식 ZPL-2.1](https://spdx.org/licenses/ZPL-2.1.html)의 이름·버전·식별자를 함께 쓴 표기 |

## 해석·검증 규칙

- `or later`가 등록된 이름 안에 있으면 하나의 피연산자로 먼저 인식하고, 이름 밖의 AND/OR/WITH만 해석함. 원문은 그대로 남김.
- classifier에서만 얻은 결과는 추정, expression/license에서 식별하면 확실이라는 기존 계약을 유지함.
- `BSD License`, `GPL License`, `Apache License` 등 모호한 이름은 계속 미상으로 남김.
- 전체 별칭을 기존 FR-LIC-07 피연산자·공백/대소문자 회귀 테스트로 확인함. 추가 22개는 각 3개 필드의 버전·신뢰 수준을 고정된 기대값과 비교함.
- AT-1 3단계는 R2 회귀 테스트 `tests/test_FR_LIC_04_rfc3987.py`에서 웹·CLI·결정 ID까지 확인함. Docker 재실행과 실제 네트워크 시간 측정은 실행 환경 담당의 별도 확인 범위임.
