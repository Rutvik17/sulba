import pytest

from approvals import unapproved

NAMES = """
version = 1
revision = 5
requires-python = ">=3.14"

[[package]]
name = "python-dateutil"
version = "2.9.0.post0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "six" },
]

[[package]]
name = "pyyaml"
version = "6.0.3"
source = { registry = "https://pypi.org/simple" }

[[package]]
name = "service"
version = "0.1.0"
source = { editable = "." }
dependencies = [
    { name = "python-dateutil" },
    { name = "pyyaml" },
]

[[package]]
name = "six"
version = "1.17.0"
source = { registry = "https://pypi.org/simple" }
"""

VERSIONS = """
version = 1
revision = 5
requires-python = ">=3.14"

[[package]]
name = "numpy"
version = "2.5.3"
source = { registry = "https://pypi.org/simple" }

[[package]]
name = "scipy"
version = "1.17.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "numpy" },
]

[[package]]
name = "service"
version = "0.1.0"
source = { editable = "." }
dependencies = [
    { name = "numpy" },
    { name = "scipy" },
]
"""

# numpy at the newest version each range of Python versions can run, as uv locks it for a
# project that supports Python 3.10 and later.
FORKED = """
version = 1
revision = 5
requires-python = ">=3.10"
resolution-markers = [
    "python_full_version >= '3.12'",
    "python_full_version == '3.11.*'",
    "python_full_version < '3.11'",
]

[[package]]
name = "numpy"
version = "2.2.6"
source = { registry = "https://pypi.org/simple" }
resolution-markers = [
    "python_full_version < '3.11'",
]

[[package]]
name = "numpy"
version = "2.4.6"
source = { registry = "https://pypi.org/simple" }
resolution-markers = [
    "python_full_version == '3.11.*'",
]

[[package]]
name = "numpy"
version = "2.5.3"
source = { registry = "https://pypi.org/simple" }
resolution-markers = [
    "python_full_version >= '3.12'",
]

[[package]]
name = "service"
version = "0.1.0"
source = { editable = "." }
dependencies = [
    { name = "numpy", version = "2.2.6", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version < '3.11'" },
    { name = "numpy", version = "2.4.6", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version == '3.11.*'" },
    { name = "numpy", version = "2.5.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version >= '3.12'" },
]
"""


@pytest.mark.id("tst_1npumz")
def test_names():
    """Matches a name however it's written"""
    approved = {
        "python_dateutil": "==2.9.0.post0",
        "PyYAML": "==6.0.3",
        "Six": "==1.17.0",
    }
    assert unapproved(NAMES, approved) == []


@pytest.mark.id("tst_x54xnj")
def test_versions():
    """Compares versions, not their text"""
    assert unapproved(VERSIONS, {"numpy": "~=2.5.0", "scipy": ">=1.9"}) == []
    assert unapproved(VERSIONS, {"numpy": "==2.5.3", "scipy": "==1.17"}) == []
    assert unapproved(VERSIONS, {"numpy": "~=2.4.0", "scipy": "<1.10"}) == [
        "numpy 2.5.3 is outside the approved ~=2.4.0",
        "scipy 1.17.0 is outside the approved <1.10",
    ]


@pytest.mark.id("tst_2j7lrg")
def test_each_version():
    """Checks each version a package is locked at"""
    assert unapproved(FORKED, {"numpy": ">=2.4"}) == [
        "numpy 2.2.6 is outside the approved >=2.4"
    ]
    assert unapproved(FORKED, {"numpy": "<2.5"}) == [
        "numpy 2.5.3 is outside the approved <2.5"
    ]
