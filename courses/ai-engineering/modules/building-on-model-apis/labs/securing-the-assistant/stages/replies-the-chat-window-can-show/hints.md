One regular expression with three alternatives, images first, then links, then bold text, finds them in a line. Escape the text between matches, and turn each match into what its kind becomes.

---

`check_url(address)` says whether an address is a URL at all, and `URL(address)` reads it. Its `protocol` is `https:`, with the colon, its `hostname` is in lower case, and its `port` is `""` for the default.

---

A browser reads `\` in an `https` address as `/`, so `https://evil.example\@bikes.example/` leads to `evil.example`. Check the host `URL` gives, and link to the `href` it gives, never to the address as the model wrote it.
