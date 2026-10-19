"""The model's reply as HTML for the shop's chat window: its text escaped, and its links kept
only when they lead to the shop's own pages."""

import html
import re

from ada_url import URL, check_url

# The shop's own hosts. A link to any other host is shown as its text alone.
HOSTS = frozenset({"bikes.example", "www.bikes.example"})
INLINE = re.compile(
    r"!\[(?P<alt>[^\]\n]*)\]\((?P<src>[^)\s]*)\)"
    r"|\[(?P<text>[^\]\n]+)\]\((?P<address>[^)\s]+)\)"
    r"|\*\*(?P<bold>[^*\n]+)\*\*"
)
BLANK = re.compile(r"\n[ \t]*\n")


def render(reply: str, hosts: frozenset[str] = HOSTS) -> str:
    """The reply as HTML: a paragraph for each block of lines, <br> between its lines, its bold
    text, and its links to hosts. Everything else is text, and images are left out."""
    blocks = BLANK.split(reply.replace("\r\n", "\n"))
    return "".join(
        "<p>"
        + "<br>".join(line_html(line, hosts) for line in block.split("\n"))
        + "</p>"
        for block in (each.strip("\n") for each in blocks)
        if block.strip()
    )


def line_html(line: str, hosts: frozenset[str]) -> str:
    """One line as HTML: its bold text and its links to hosts, the rest escaped."""
    out, at = [], 0
    for match in INLINE.finditer(line):
        out.append(html.escape(line[at : match.start()]))
        at = match.end()
        if match["bold"] is not None:
            out.append(f"<strong>{html.escape(match['bold'])}</strong>")
        elif match["text"] is not None:
            text = html.escape(match["text"])
            href = link(match["address"], hosts)
            out.append(f'<a href="{html.escape(href)}">{text}</a>' if href else text)
    out.append(html.escape(line[at:]))
    return "".join(out)


def link(address: str, hosts: frozenset[str]) -> str | None:
    """The address a browser would follow, when it's an https page on one of hosts, with no
    user name, password or port, or None."""
    if not check_url(address):
        return None
    url = URL(address)
    if (
        url.protocol != "https:"
        or url.hostname not in hosts
        or url.username
        or url.password
        or url.port
    ):
        return None
    return url.href
