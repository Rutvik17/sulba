import io

from PIL import Image


def encoded(rows, form, **options):
    """An RGB image of rows of (red, green, blue) pixels, saved in form, such as "PNG", with
    the options the form takes."""
    image = Image.new("RGB", (len(rows[0]), len(rows)))
    image.frombytes(bytes(value for row in rows for pixel in row for value in pixel))
    out = io.BytesIO()
    image.save(out, form, **options)
    return out.getvalue()


def decoded(data):
    """The image in data as rows of (red, green, blue) pixels."""
    with Image.open(io.BytesIO(data)) as image:
        rgb = image.convert("RGB")
    values = rgb.tobytes()
    pixels = [tuple(values[i : i + 3]) for i in range(0, len(values), 3)]
    return [pixels[i : i + rgb.width] for i in range(0, len(pixels), rgb.width)]
