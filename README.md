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
│   ├── app/                  호출 순서 조정, 화면 개발용 예시 결과 (R0)
│   ├── __main__.py           명령줄 실행 python -m oss_check (R0)
│   └── web/                  FastAPI 화면 (R5)
│       ├── forms.py          입력 크기 제한 (1MB)
│       ├── routers/          GET /, POST /analyze, GET /preview
│       ├── templates/
│       └── static/
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

# 테스트 (네트워크 없이 실행됨)
python -m pytest -q

# 웹 화면
python -m uvicorn oss_check.web.main:app --reload   # Windows는 run.bat도 가능
#   http://127.0.0.1:8000/          입력 화면
#   http://127.0.0.1:8000/preview   예시 결과 화면 (가상 데이터, PyPI 조회 없음)

# 명령줄 (SRS IF-UI-04)
python -m oss_check requirements.txt                 # 프로젝트 라이선스 기본값 MIT
python -m oss_check requirements.txt --project Apache-2.0
```

- 파이썬 3.11 이상 필요 (SRS DC-01)
- 웹 분석(`POST /analyze`)과 명령줄은 실제 PyPI를 조회함. 인터넷 연결이 필요함
- 프롬프트 앞에 `(.venv)`가 보이는지 확인함. 가상환경 밖(예: Anaconda 기본 파이썬)에서 실행하면 `No module named 'fastapi'` 같은 오류가 남

## 스모크 테스트 (실제 PyPI로 끝까지 동작하는지 확인)

`python -m pytest`는 PyPI 응답 사본으로 돌아가므로, 실제 조회까지 확인하려면 아래를 실행함. 입력은 SRS AT-1의 「웹앱 구성 11줄」(`tests/fixtures/at1_webapp_requirements.txt`)을 씀.

### 1. 명령줄

```bash
time python -m oss_check tests/fixtures/at1_webapp_requirements.txt
```

| 확인할 것 | 기대 결과 (2026-11-07 실측) | 근거 |
|---|---|---|
| 둘째 줄 | `패키지 30개 (직접 11 · 따라온 19 · 조회 실패 0)` | AT-1 2단계 |
| `certifi` 줄 | `[조건 있음] certifi (따라옴)`로 시작함 | AT-1 2단계 |
| `time`의 `real` | 30초 미만 (실측 약 3초) | AT-1 1단계, QR-P-01 |
| 종료 코드 (`echo $?`) | `0` | IF-UI-04 |

**AT-1 3단계** (`jsonschema[format]`을 더한 입력)

```bash
(cat tests/fixtures/at1_webapp_requirements.txt; echo "jsonschema[format]") > ../at1_step3.txt
python -m oss_check ../at1_step3.txt | head -5
```

- 기대 결과: `패키지 46개 (직접 12 · 따라온 34 · 조회 실패 0)`, 결과 목록 첫 줄이 `[안 됨] rfc3987 (따라옴)`로 시작함 (GPL-3.0-or-later)
- `../`에 만드는 것은 저장소 안에 임시 파일을 남기지 않으려는 것임

**오류 처리**

```bash
python -m oss_check 없는파일.txt; echo "exit=$?"
```

- 기대 결과: `분석하지 못함: …` 한 줄과 `exit=1`. 추적 정보(Traceback)가 나오지 않아야 함 (QR-R-01)

### 2. 웹 화면

```bash
python -m uvicorn oss_check.web.main:app
```

1. 브라우저에서 `http://127.0.0.1:8000/`을 엶
2. `tests/fixtures/at1_webapp_requirements.txt`를 「파일 선택」으로 올리거나, 내용을 붙여 넣음. 라이선스는 MIT
3. 「분석하기」를 누름

| 확인할 것 | 기대 결과 | 근거 |
|---|---|---|
| 상단 | 「의존성 점검 결과」, 전체 30개 · 직접 11개 · 따라온 19개 · 조회 실패 0개 | AT-1 2단계 |
| 목록 | 위험 순(안 됨 → 모름 → 조건 있음 → 판단보류 → 써도 됨), 「써도 됨」은 접혀 있음 | FR-OUT-02·03 |
| 하단 | 「이 결과는 법적 조언이 아닙니다」, 데이터 출처 SPDX · PyPI · OSV | AT-1 4단계, CR-01·04 |
| 판정 | 1번 명령줄 결과와 패키지별 판정이 같음 | AT-1 5단계 |

- 3단계 입력(붙여 넣기 끝에 `jsonschema[format]` 한 줄 추가)이면 맨 위가 「안 됨 · rfc3987」이어야 함
- 서버는 터미널에서 Ctrl+C로 끔

### 3. Docker (AT-1 6단계, DC-04)

```bash
docker build -t oss-check .
docker run --rm -p 8000:8000 oss-check
# 브라우저에서 http://127.0.0.1:8000/ 을 열고 2번과 같은 순서로 확인함

# 컨테이너 안에서 명령줄 실행 (Git Bash는 경로 변환을 끄는 MSYS_NO_PATHCONV=1 이 필요함)
MSYS_NO_PATHCONV=1 docker run --rm -v "$PWD/tests/fixtures:/data:ro" oss-check \
    python -m oss_check /data/at1_webapp_requirements.txt
```

- 기대 결과는 1·2번과 같음. 점검 기록은 `src/oss_check/web/DOCKER_CHECKLIST.md`

### 결과가 기대와 다를 때

| 증상 | 원인 | 조치 |
|---|---|---|
| 패키지 수가 30과 조금 다름 | 입력이 버전을 고정하지 않아, PyPI에 새 버전이 나오면 따라오는 패키지가 바뀜 | `python -m pytest`가 통과하면 코드 문제는 아님. 기대값을 바꿀지는 팀에서 정함 (`tests/fixtures/README.md`) |
| 조회 실패가 많음, `분석하지 못함: …` | 인터넷 연결 또는 PyPI 응답 문제 | 연결을 확인하고 다시 실행함 |
| `No module named …` | 가상환경이 꺼져 있음 | `source .venv/Scripts/activate` 후 `pip install -e ".[dev]"` |
