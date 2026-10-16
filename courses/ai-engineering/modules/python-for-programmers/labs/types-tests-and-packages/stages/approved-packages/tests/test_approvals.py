import pytest

from approvals import unapproved

# The service's lock file as uv writes it, without each package's files and their hashes.
LOCK = """
version = 1
revision = 5
requires-python = ">=3.14"

[[package]]
name = "numpy"
version = "2.4.6"
source = { registry = "https://pypi.org/simple" }

[[package]]
name = "pandas"
version = "3.0.2"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "numpy" },
    { name = "python-dateutil" },
    { name = "tzdata", marker = "sys_platform == 'emscripten' or sys_platform == 'win32'" },
]

[[package]]
name = "python-dateutil"
version = "2.9.0.post0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "six" },
]

[[package]]
name = "service"
version = "0.1.0"
source = { editable = "." }
dependencies = [
    { name = "numpy" },
    { name = "pandas" },
]

[package.metadata]
requires-dist = [
    { name = "numpy", specifier = ">=2.4" },
    { name = "pandas", specifier = ">=3.0" },
]

[[package]]
name = "six"
version = "1.17.0"
source = { registry = "https://pypi.org/simple" }

[[package]]
name = "tzdata"
version = "2025.3"
source = { registry = "https://pypi.org/simple" }
"""

APPROVED = {
    "numpy": ">=2.4,<2.5",
    "pandas": "~=3.0.0",
    "python-dateutil": ">=2.9",
    "six": "==1.17.0",
    "tzdata": ">=2025.2",
}


@pytest.mark.id("tst_2mqodz")
def test_approved():
    """Passes a lock file whose packages are all approved"""
    assert unapproved(LOCK, APPROVED) == []


@pytest.mark.id("tst_ddz0u0")
def test_not_listed():
    """Reports each package that isn't on the list, in the lock file's order"""
    assert unapproved(LOCK, {}) == [
        "numpy 2.4.6 isn't on the approved list",
        "pandas 3.0.2 isn't on the approved list",
        "python-dateutil 2.9.0.post0 isn't on the approved list",
        "six 1.17.0 isn't on the approved list",
        "tzdata 2025.3 isn't on the approved list",
    ]
    listed = {name: versions for name, versions in APPROVED.items() if name != "six"}
    assert unapproved(LOCK, listed) == ["six 1.17.0 isn't on the approved list"]


@pytest.mark.id("tst_ta3jye")
def test_outside():
    """Reports a version outside the approved ones"""
    approved = APPROVED | {"pandas": "~=3.1.0", "tzdata": "<2025"}
    assert unapproved(LOCK, approved) == [
        "pandas 3.0.2 is outside the approved ~=3.1.0",
        "tzdata 2025.3 is outside the approved <2025",
    ]


@pytest.mark.id("tst_3jzdt9")
def test_types(typecheck):
    """Passes mypy --strict"""
    assert typecheck("approvals.py") == []
