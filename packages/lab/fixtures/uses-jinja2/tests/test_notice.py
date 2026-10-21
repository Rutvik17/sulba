import jinja2.sandbox
import pytest
from notice import notice


@pytest.mark.id("tst_jnj001")
def test_notice():
    """Writes each repair on its own line"""
    repairs = [
        {"bike": "Ana's", "work": "new brakes", "parts": ["pads", "cable"]},
        {"bike": "Ben's", "work": "tune-up", "parts": []},
    ]
    assert notice(repairs) == "Ana&#39;s: New Brakes, with pads, cable\nBen&#39;s: Tune-Up"


@pytest.mark.id("tst_jnj002")
def test_sandbox():
    """Refuses a template that reaches into Python or changes what it was given"""
    sandbox = jinja2.sandbox.ImmutableSandboxedEnvironment()
    with pytest.raises(jinja2.exceptions.SecurityError):
        sandbox.from_string("{{ ''.__class__.__mro__ }}").render()
    with pytest.raises(jinja2.exceptions.SecurityError):
        sandbox.from_string("{{ parts.append('chain') }}").render(parts=["pads"])
