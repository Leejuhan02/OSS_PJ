from oss_check.domain.models import LicenseInfo
from oss_check.judge.rules import judge

# 예시 1: MIT 프로젝트에 LGPL-2.1 패키지 사용 (FR-JDG-05 -> '조건 있음')
lic1 = LicenseInfo("certifi", (frozenset({"LGPL-2.1-or-later"}),), "확실", "expression", "LGPL-2.1-or-later")
res1 = judge(lic1, project="MIT")
print(f"[{res1.verdict}] {res1.package}: {res1.reason}")
# 출력: [조건 있음] certifi: LGPL-2.1-or-later: 소스 코드를 직접 수정했다면 고친 부분만 공개해야 합니다.

# 예시 2: MIT 프로젝트에 GPL-3.0 패키지 사용 (FR-JDG-06 -> '안 됨')
lic2 = LicenseInfo("gpl-pkg", (frozenset({"GPL-3.0-only"}),), "확실", "expression", "GPL-3.0-only")
res2 = judge(lic2, project="MIT")
print(f"[{res2.verdict}] {res2.package}: {res2.reason}")
# 출력: [안 됨] gpl-pkg: GPL-3.0-only: 의존성 라이선스 조건이 내 프로젝트 라이선스보다 엄격합니다.

# 예시 3: OR 조건 (MIT OR GPL-3.0) -> 약한 조건인 MIT 선택 (FR-JDG-03 -> '써도 됨')
lic3 = LicenseInfo("dual-pkg", (frozenset({"MIT"}), frozenset({"GPL-3.0-only"})), "확실", "expression", "MIT OR GPL-3.0-only")
res3 = judge(lic3, project="MIT")
print(f"[{res3.verdict}] {res3.package}: {res3.reason}")
# 출력: [써도 됨] dual-pkg: MIT