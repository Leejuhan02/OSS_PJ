# OSS_PJ — 의존성 라이선스·취약점 점검 도구

한밭대학교 「오픈소스 소프트웨어 프로그래밍」(COME210014) 2팀 프로젝트임.

## 무엇을 하는가

- `requirements.txt`를 올리면 실제로 설치되는 패키지 전부(전이 의존성 포함)를 펼침
- 패키지마다 라이선스를 찾아, 내 프로젝트 라이선스 기준으로 「안 됨 / 모름 / 조건 있음 / 판단보류 / 써도 됨」을 판정함
- 알려진 취약점 표시(OSV 조회)는 권장 범위임. 필수 범위가 끝나면 추가함
- 각 결과가 확실한지, 추정인지도 함께 표시함
- 웹 화면과 명령줄(CLI) 두 가지로 씀

## 디렉터리 구조

```
OSS_PJ/
├── .github/
│   ├── ISSUE_TEMPLATE/       이슈 양식 (예정)
│   └── workflows/test.yml    PR마다 테스트 자동 실행 (파이썬 3.11·3.14)
├── docs/                     SRS, 설계지침, 수행계획서 — 작업 전에 먼저 읽을 것
├── AGENTS.md                 AI 도구용 팀 규칙 (CLAUDE.md가 이 파일을 불러옴)
├── src/oss_check/
│   ├── data/                 별칭 사전, 등급표, SPDX 목록 (R2·R3)
│   ├── domain/               공통 모델과 포트 (R0)
│   ├── collect/              입력 파싱, 의존성 전개 (R1)
│   ├── resolve/              라이선스 식별 (R2)
│   ├── judge/                판정 규칙 (R3)
│   ├── vuln/                 취약점 분류 (R4)
│   ├── adapters/             PyPI·OSV 조회, 캐시 (R4)
│   ├── app/                  호출 순서 조정 (R0)
│   └── web/                  FastAPI 화면 (R5)
│       ├── routers/
│       └── templates/
└── tests/
    └── fixtures/             실제 API 응답 사본
```

## 역할

| 코드 | 역할 | 담당 폴더 |
|---|---|---|
| R0 | 팀장·통합 | `domain/`, `app/` |
| R1 | 수집 | `collect/` |
| R2 | 해석 | `resolve/`, `data/` |
| R3 | 판정 | `judge/`, `data/` |
| R4 | 조회 | `adapters/`, `vuln/` |
| R5 | 화면·배포 | `web/`, Dockerfile |

역할은 R0~R5 코드로만 구분함. 문서에 개인 이름은 적지 않음.

## 작업 규칙

- `main`에 직접 푸시하지 않음. 브랜치에서 작업 후 PR로 합침
- 브랜치 이름: `feat/<모듈>-<요구사항ID>` (예: `feat/judge-FR-JDG-03`)
- 코드는 테스트 먼저(RED) → 구현(GREEN) 순서로 씀 (설계지침 §9)
- PR 본문은 수행계획서 §4.2 양식을 따름. AI 도구 사용 여부와 사용한 프롬프트를 반드시 적음
- 강의 개념을 적용한 곳에는 `# [강의] 개념명` 주석을 닮

## 실행 방법

```bash
# 처음 한 번 (저장소 최상위 폴더에서)
python -m venv .venv
source .venv/Scripts/activate      # Windows Git Bash (맥·리눅스: source .venv/bin/activate)
pip install -e ".[dev]"

# 테스트
python -m pytest -q

# 웹 화면 (입력 화면까지 동작. 분석 기능은 연결 작업 중)
python -m uvicorn oss_check.web.main:app --reload   # Windows는 run.bat도 가능
```

- 파이썬 3.11 이상 필요 (SRS DC-01)
- 명령줄 실행 `python -m oss_check 파일`은 아직 없음 (SRS IF-UI-04, 작업 예정)
