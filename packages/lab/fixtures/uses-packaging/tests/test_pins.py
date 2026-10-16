import pytest
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from pins import pinned


@pytest.mark.id("tst_pack01")
def test_pinned():
    """Reads a pinned requirement"""
    assert pinned("PyYAML==6.0.3") == ("pyyaml", "6.0.3")
    assert pinned("numpy>=2") is None


@pytest.mark.id("tst_pack02")
def test_versions():
    """Orders versions as PEP 440 does"""
    assert Version("1.10") > Version("1.9")
    assert Version("2.0rc1") < Version("2.0")
    assert "1.10" in SpecifierSet(">=1.9,<2")
