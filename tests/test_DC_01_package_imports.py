"""DC-01: 파이썬 3.11 이상에서 모든 모듈이 import 되어야 함.

설계지침 §3: domain 은 표준 라이브러리만 import 함.
설계지침 §4.0 흐름에 나오는 모듈을 하나씩 import 해 봄. 어느 하나라도 실패하면
그 모듈을 쓰는 단계 전체가 동작하지 않으므로, 다른 테스트가 그 모듈을 다루지 않아도 여기서 잡힘.
"""

import ast
import importlib
import sys
from pathlib import Path

import pytest

# 설계지침 §4.0·§2 의 모듈. 새 모듈이 생기면 여기에 추가함
MODULES = [
    "oss_check",
    "oss_check.domain.models",
    "oss_check.domain.ports",
    "oss_check.collect.parser",
    "oss_check.collect.walker",
    "oss_check.resolve",
    "oss_check.judge.judge_logic",
    "oss_check.adapters.pypi_adapter",
    "oss_check.web.main",
]

DOMAIN_DIR = Path(__file__).resolve().parents[1] / "src" / "oss_check" / "domain"


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    """DC-01: 각 모듈이 오류 없이 import 됨"""
    importlib.import_module(name)


def test_domain_imports_nothing_external():
    """설계지침 §3: domain 은 표준 라이브러리와 oss_check.domain 만 import 함"""
    allowed = set(sys.stdlib_module_names) | {"__future__"}
    for path in sorted(DOMAIN_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                assert top in allowed or name.startswith("oss_check.domain"), f"{path.name}: {name}"
