import pytest

from prompts import SEPARATOR, count, pack, shop_encoding, stream

TITLES = [
    "Stainless Steel Water Bottle, 32 oz",
    "Wireless Mouse for Laptop, Silent Clicks",
    "Cotton Bath Towels, Set of 4",
]


@pytest.fixture(scope="module")
def encoding():
    return shop_encoding()


@pytest.mark.id("tst_3bw89g")
def test_count(encoding):
    """Counts more tokens for a longer title"""
    assert count("Water Bottle", encoding) < count(TITLES[0], encoding)


@pytest.mark.id("tst_svzff8")
def test_order(encoding):
    """Packs the titles in order, each followed by the separator"""
    separator = encoding.encode(SEPARATOR, allowed_special={SEPARATOR})
    wanted = []
    for title in TITLES:
        wanted += encoding.encode_ordinary(title) + separator
    assert pack(TITLES, 10_000, encoding) == wanted


@pytest.mark.id("tst_jvp2mh")
def test_limit(encoding):
    """Stops at the first title that doesn't fit"""
    first, second = (len(encoding.encode_ordinary(title)) + 1 for title in TITLES[:2])
    packed = pack(TITLES, first + second, encoding)
    assert encoding.decode(packed) == f"{TITLES[0]}{SEPARATOR}{TITLES[1]}{SEPARATOR}"


@pytest.mark.id("tst_gpp3d6")
def test_stream(encoding):
    """Shows a reply as it streams in"""
    reply = "The bottle keeps drinks cold for 24 hours."
    shown = list(stream(encoding.encode_ordinary(reply), encoding))
    assert shown[-1] == reply
    assert all(reply.startswith(text) for text in shown)
