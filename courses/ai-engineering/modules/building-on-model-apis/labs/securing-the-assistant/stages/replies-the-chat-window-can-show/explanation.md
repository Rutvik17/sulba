A model's reply is output from outside the page, like anything a visitor wrote, so it's escaped like it. Improper output handling is one of the risks in OWASP's Top 10 for LLM Applications, and among its defences is encoding the model's output for where it goes, here HTML.

A link is only as safe as the address the browser follows, so the check reads the address with the browser's rules, the WHATWG URL Standard's, which `ada_url` follows, and the link carries the address as read. Python's `urllib.parse.urlsplit` reads `https://evil.example\@bikes.example/` as a page on `bikes.example` with a user name, but the URL Standard ends the host at the backslash, and a browser goes to `evil.example`. A check by `urlsplit` would let through a link the browser follows elsewhere.

Images are left out because the browser fetches them by itself, the moment the reply is shown. An injection that has the model write an image whose address holds the customer's details sends them out with nobody clicking anything. A link waits for a click, and only ever leads to the shop.

A link's host must be one of the shop's exactly: a host that only starts or ends with the shop's name, such as `bikes.example.evil.example`, can belong to anyone.
