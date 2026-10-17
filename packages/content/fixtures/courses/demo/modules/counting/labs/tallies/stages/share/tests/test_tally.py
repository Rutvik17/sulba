import json
from pathlib import Path

import pytest
from tally import share


@pytest.mark.id("tst_demo03")
def test_share():
    """Two of three votes for yes"""
    poll = json.loads(Path("references/shares.json").read_text())["polls"][0]
    assert share(poll["choices"], poll["choice"]) == pytest.approx(poll["share"])
