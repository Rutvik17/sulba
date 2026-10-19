import html
from html.parser import HTMLParser

import pytest
from ada_url import URL

from render import HOSTS, render


class Shown(HTMLParser):
    """What a chat window would show of a piece of HTML that it shouldn't: any tag but p, br,
    strong and a, any attribute but an a's href, and any href that isn't an https page on one
    of the shop's hosts."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.problems = []

    def handle_starttag(self, tag, attrs):
        if tag in {"p", "br", "strong"} and not attrs:
            return
        if tag == "a" and len(attrs) == 1 and attrs[0][0] == "href":
            url = URL(attrs[0][1])
            if (url.protocol, url.username, url.password, url.port) == (
                "https:",
                "",
                "",
                "",
            ):
                if url.hostname in HOSTS and url.href == attrs[0][1]:
                    return
        self.problems.append((tag, attrs))


def problems(page):
    shown = Shown()
    shown.feed(page)
    shown.close()
    return shown.problems


@pytest.mark.id("tst_f6wv4m")
def test_text():
    """Paragraphs and lines, and every character as text"""
    assert render("We open at 9.\nWe close at 5.\n\nSee you then.") == (
        "<p>We open at 9.<br>We close at 5.</p><p>See you then.</p>"
    )
    assert render("One\r\ntwo\r\n \r\n\r\nthree\n") == "<p>One<br>two</p><p>three</p>"
    text = "<script>alert('hi')</script> & \"quotes\""
    assert render(text) == f"<p>{html.escape(text)}</p>"
    assert render("") == "" and render("\n\n") == ""


@pytest.mark.id("tst_34iue6")
def test_bold():
    """Bold text, escaped too"""
    assert render("New brakes are **£18** a bike.") == (
        "<p>New brakes are <strong>£18</strong> a bike.</p>"
    )
    assert render("**<b>x</b>**") == "<p><strong>&lt;b&gt;x&lt;/b&gt;</strong></p>"


@pytest.mark.id("tst_hy8s8m")
def test_links_to_the_shop():
    """A link to the shop's own pages, as a browser reads its address"""
    assert render("Book [online](https://bikes.example/book).") == (
        '<p>Book <a href="https://bikes.example/book">online</a>.</p>'
    )
    for address in [
        "HTTPS://BIKES.EXAMPLE/book",
        "https://www.bikes.example:443/prices",
        "https://bikes.example/a/../book",
        'https://bikes.example/find?q="><script>',
    ]:
        href = URL(address).href
        assert (
            render(f"[here]({address})")
            == f'<p><a href="{html.escape(href)}">here</a></p>'
        )


@pytest.mark.id("tst_nfougf")
def test_links_elsewhere():
    """A link anywhere else is its text alone"""
    for address in [
        "https://evil.example/pay",
        "http://bikes.example/book",
        "https://bikes.example.evil.example/",
        "https://bikes.example@evil.example/",
        "https://user:secret@bikes.example/",
        "https://bikes.example:8443/",
        "https:\\\\evil.example/pay",
        "https://evil.example\\@bikes.example/",
        "https://bikes.example%2eevil.example/",
        "https://bıkes.example/",
        "javascript:location='https://evil.example'",
        "data:text/html,hi",
        "//evil.example/",
        "/book",
    ]:
        assert render(f"[Pay here]({address})") == "<p>Pay here</p>", address


@pytest.mark.id("tst_wxh9uk")
def test_images():
    """No image is shown, wherever it leads"""
    assert render("![](https://evil.example/c.png?d=B-1042) Done.") == "<p> Done.</p>"
    assert render("![map](https://bikes.example/map.png)") == "<p></p>"


@pytest.mark.id("tst_qwkv5t")
def test_shows_nothing_else():
    """Whatever the reply, the HTML holds nothing the window shouldn't show"""
    replies = [
        "<img src=x onerror=alert(1)>",
        '<a href="https://evil.example">x</a>',
        '[x](https://bikes.example/" onclick="alert(1))',
        "[**x**](https://evil.example)",
        "![[x](https://bikes.example)](https://evil.example)",
        "**[x](https://evil.example)**",
        "[x](https://bikes.example/<script>)",
        "‮[x](https://evil.example)",
    ]
    for reply in replies:
        assert problems(render(reply)) == [], reply
