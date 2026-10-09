# AGENTS.md — AI 코딩 도구용 팀 규칙

이 저장소에서 코드를 쓰거나 고치는 AI 도구는 아래 규칙을 따름. 사람용 기준 문서는 `docs/`에 있음.

## 프로젝트

- `requirements.txt`를 받아 전이 의존성까지 펼치고, 각 패키지의 라이선스를 식별·판정해 보여주는 웹앱 + CLI (Python 3.11 이상)
- 요구사항: `docs/01_SRS_요구사항명세서.md` (요구사항 ID 예: `FR-DEP-08`, `FR-LIC-05`)
- 구조·모듈 간 약속: `docs/02_설계지침.md` §2, **§4**
- 개발 절차(TDD): `docs/02_설계지침.md` **§9**

## 반드시 TDD 순서로 작업함

요구사항 ID 하나 = 사이클 하나.

1. **RED** — SRS에서 요구사항 ID를 하나 고르고 테스트를 먼저 씀
   - 파일: `tests/test_<요구사항ID>_<내용>.py` (예: `tests/test_FR_DEP_08_lookup.py`), docstring 첫 줄에 요구사항 ID
   - `python -m pytest`를 실행해 **새 테스트만, 기능이 아직 없어서** 실패하는지 확인
   - 커밋: `test(red): <요구사항ID> <내용>`
2. **GREEN** — 그 테스트를 통과시키는 최소한의 코드만 씀
   - `python -m pytest` 전체 통과 확인 (`failed`·`error` 0)
   - 커밋: `feat(green): <요구사항ID> <내용>`
3. **REFACTOR** (필요할 때만) — 동작을 바꾸지 않고 정리. 전체 테스트가 계속 통과해야 함
   - 커밋: `refactor: <내용>`

버그 수정도 같음: 버그를 재현하는 테스트(RED) → 수정(GREEN).
예외: 문서, CSS, HTML 모양만 바꾸는 변경은 RED 단계 없이 진행함.

## 금지

- 테스트를 통과시키려고 테스트를 고치거나, 지우거나, `skip` 처리하지 않음. 테스트가 SRS와 다르면 작업을 멈추고 사람에게 알림
- 테스트에서 네트워크(PyPI, OSV)를 쓰지 않음. `oss_check.domain.ports`의 `PackageSource`·`VulnSource`를 구현한 가짜 객체를 씀
- `src/oss_check/domain/` (models.py, ports.py)를 임의로 바꾸지 않음. 팀 전체 약속이라 PR로 전원 확인을 받아야 함
- `domain/`에서 표준 라이브러리 외 패키지를 import 하지 않음
- 데이터 파일을 `src/oss_check/data/` 밖에 두지 않음. 읽을 때는 `importlib.resources.files("oss_check").joinpath("data", 파일명)`을 씀. `"src/..."` 같은 문자열 경로나 `Path(__file__)` 상대 경로는 쓰지 않음
- 자기 담당 모듈 밖의 코드나 테스트를 고치지 않음. 필요하면 사람에게 알림

## 모듈 간 약속 요약 (자세한 것은 설계지침 §4)

- 모듈끼리는 `oss_check.domain.models`의 `Package`, `LicenseInfo`, `Judgement`, `Row`, `Report`만 주고받음
- `LicenseInfo.raw`는 항상 문자열. `origin`은 `license_expression` / `license` / `classifiers` / `none`
- 미상은 `LicenseInfo.unknown(이름)`, 단일 식별자는 `LicenseInfo.single(...)`로 만듦
- `PackageSource.fetch(name)`은 PyPI JSON의 `info` dict를 돌려주고, 실패하면 예외 없이 `None`
- 조회 실패 패키지는 `Package(..., lookup_failed=True)`

## 명령

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash (맥·리눅스: .venv/bin/activate)
pip install -e ".[dev]"
python -m pytest -q
```

## 작업·PR 규칙

- `main`에 직접 푸시하지 않음. 브랜치 이름 `feat/<모듈>-<요구사항ID>` (예: `feat/collect-FR-DEP-08`)
- 강의 개념을 적용한 곳에는 `# [강의] 개념명` 주석을 닮
- 코드 주석·문서는 한국어로 씀
- PR 본문에 적을 것: 한 일(요구사항 ID), RED 실패 결과 한 줄, GREEN 통과 결과 한 줄, AI 도구 사용 여부와 사용한 프롬프트
