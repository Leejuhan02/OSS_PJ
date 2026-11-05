# tests/fixtures

실제 API 응답 사본을 둘 자리임. 테스트는 네트워크 대신 이 사본을 읽음 (SRS DC-05, 설계지침 §9.2).

## AT-1 「웹앱 구성 11줄」 (SRS §4.3)

| 파일 | 내용 |
|---|---|
| `at1_webapp_requirements.txt` | AT-1 1단계 입력 11줄. 버전 고정 없음 |
| `at1_pypi_info.json` | 위 입력과 3단계 입력(`jsonschema[format]` 추가)을 전개할 때 조회한 46개 패키지의 PyPI `info` 사본. 식별·전개에 쓰는 필드만 저장 |
| `make_at1_snapshot.py` | 사본을 다시 만드는 스크립트. 실제 PyPI를 조회하므로 필요할 때만 실행함 |

- 입력 출처: 타당성 검증(2026-09-30) 측정 스크립트 `resolve_deps.py`·`validate.py`의 표본 「웹앱 (이 프로젝트 예상 구성)」 11개 패키지. 참고 리포트 §2.5의 「웹앱 구성 11 → 30」이 이 표본임
- 사본 작성일: 2026-11-05. 이 날 실제 PyPI로 CLI를 실행한 결과도 「30개 (직접 11 · 따라온 19)」, `certifi` 「조건 있음」으로 SRS AT-1 2단계와 같았음
- 사용하는 테스트: `tests/test_AT_1_webapp_sample.py` (AT-1 2·4·5단계)
- 버전을 고정하지 않은 입력이라, 사본을 다시 만들면 PyPI의 새 버전 때문에 패키지 수가 바뀔 수 있음. 그때는 위 테스트가 실패해 알려 줌

```bash
python tests/fixtures/make_at1_snapshot.py     # 저장소 최상위에서, 가상환경을 켠 상태로
```
