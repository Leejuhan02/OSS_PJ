# OSS_PJ — 의존성 라이선스·취약점 점검 도구

한밭대학교 「오픈소스 소프트웨어 프로그래밍」(COME210014) 2팀 프로젝트임.

## 무엇을 하는가

- `requirements.txt`를 올리면 실제로 설치되는 패키지 전부(전이 의존성 포함)를 펼침
- 패키지마다 라이선스를 찾아, 내 프로젝트 라이선스 기준으로 「써도 됨 / 조건 있음 / 안 됨 / 모름」을 판정함
- 알려진 취약점을 함께 표시함 (OSV 조회)
- 각 결과가 확실한지, 추정인지도 함께 표시함
- 웹 화면과 명령줄(CLI) 두 가지로 씀

## 디렉터리 구조

```
OSS_PJ/
├── .github/ISSUE_TEMPLATE/   이슈·PR 양식
├── docs/                     SRS, 설계지침, 수행계획서
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

| 코드 | 역할 | 담당 폴더 | 이름 |
|---|---|---|---|
| R0 | 팀장·통합 | `domain/`, `app/` | 이주한 |
| R1 | 수집 | `collect/` | |
| R2 | 해석 | `resolve/`, `data/` | |
| R3 | 판정 | `judge/`, `data/` | |
| R4 | 조회 | `adapters/`, `vuln/` | |
| R5 | 화면·배포 | `web/`, Dockerfile | |

## 작업 규칙

- `main`에 직접 푸시하지 않음. 브랜치에서 작업 후 PR로 합침
- 브랜치 이름: `feat/<모듈>-<요구사항ID>` (예: `feat/judge-FR-JDG-03`)
- PR에는 GPT 등 AI 도구 사용 여부와 사용한 프롬프트를 적음
- 강의 개념을 적용한 곳에는 `# [강의] 개념명` 주석을 닮

## 실행 방법

구현 후 작성 예정임.
