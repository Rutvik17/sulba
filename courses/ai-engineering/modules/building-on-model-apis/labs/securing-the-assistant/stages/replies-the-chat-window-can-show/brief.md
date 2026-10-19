The shop's chat window shows each reply as HTML, so a customer gets the shop's links, and prices in bold. But the reply is text the model wrote, and whoever steers the model steers it: a `<script>` the browser would run, a link that looks like the shop's and leads somewhere else, or an image whose address carries the customer's details to someone else's server, fetched the moment the reply is shown.

In `render.py`, write `render(reply, hosts=HOSTS)`, the reply as HTML the window can show:

- Each block of lines between blank lines is a paragraph, `<p>...</p>`, with `<br>` between its lines. A line ends at `\n` or `\r\n`.
- `**text**` is bold, `<strong>text</strong>`.
- `[text](address)` is a link, `<a href="...">text</a>`, when the address leads to a page on one of `hosts`: `https`, with no user name, password or port. Read the address with `ada_url`'s `URL`, as a browser reads it, and link to its `href`. Any other link is its text alone. An address holds no spaces and no `)`.
- `![text](address)`, an image, is left out, wherever it leads.
- Everything else is text, escaped with `html.escape`, as are a link's text and its `href`.

The window shows nothing more: no other tag, and no attribute but a link's `href`.

```
render(reply, hosts=HOSTS) -> str
```
