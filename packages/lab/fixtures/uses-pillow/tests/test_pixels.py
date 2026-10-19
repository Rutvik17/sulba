import pytest
from pixels import decoded, encoded


@pytest.mark.id("tst_pil001")
def test_png():
    """Reads a PNG's pixels back as they were"""
    rows = [[(255, 0, 0), (0, 255, 0), (0, 0, 255)], [(0, 0, 0), (128, 128, 128), (255, 255, 255)]]
    assert decoded(encoded(rows, "PNG")) == rows


@pytest.mark.id("tst_pil002")
def test_jpeg():
    """Reads a JPEG's pixels back close to what they were"""
    rows = [[(8 * x, 8 * y, 128) for x in range(16)] for y in range(16)]
    back = decoded(encoded(rows, "JPEG", quality=95))
    assert [len(row) for row in back] == [16] * 16
    errors = [
        abs(a - b)
        for row, read in zip(rows, back, strict=True)
        for pixel, got in zip(row, read, strict=True)
        for a, b in zip(pixel, got, strict=True)
    ]
    assert max(errors) <= 16
