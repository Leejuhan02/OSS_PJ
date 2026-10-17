# src/oss_check/data

별칭 사전, 등급표, SPDX 목록을 둘 자리임 (R2·R3).

## 라이선스 식별 데이터 (R2)

- `spdx_licenses.json`: 공식 SPDX 3.29.0 라이선스 목록 원본, 740개 ID (폐기된 ID 포함).
  출처: https://raw.githubusercontent.com/spdx/license-list-data/v3.29.0/json/licenses.json
  목록 안내: https://spdx.org/licenses/
- `license_aliases.json`: 팀 초기 별칭 사전. 코드를 수정하지 않고 보강할 수 있음.
  이름만으로 버전을 알 수 없는 `BSD License`, `GPL License`, `Apache License` 등은 추측해서 매핑하지 않음.
  필수 40종(DR-03), 권장 80종(DR-06) 및 변환율(QR-A-02)은 후속 작업임.

- `spdx_exceptions.json`: 공식 SPDX 3.29.0 예외 목록 원본, 86개 ID.
  출처: https://raw.githubusercontent.com/spdx/license-list-data/v3.29.0/json/exceptions.json
  WITH 예외 이름 검증에 사용하고, 원문과 출처 URL을 보존함.
  기존 package-data의 `data/*.json`에 포함됨.

등급표와 판정 정답셋은 R3와 협의해 별도 작업.
