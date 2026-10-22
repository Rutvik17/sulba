"""The desk with its page: the app from Signing in, which also serves the chat page at
/, its styles, and the scripts that `uv run sulba.py build` compiles from the TypeScript
into static/."""

import os
from collections.abc import Mapping
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from app import create_app

STATIC = Path(__file__).with_name("static")

# The page runs only the scripts and styles the desk serves, so markup that reaches the
# page can't run a script of its own, and no other site can show the page in a frame.
POLICY = (
    "default-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)

PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Help desk</title>
    <link rel="stylesheet" href="/page.css">
    <script type="module" src="/static/page.js"></script>
  </head>
  <body data-prompt-price="{prompt}" data-completion-price="{completion}">
    <header>
      <h1>Help desk</h1>
      <p id="who"></p>
      <a id="sign-in" href="/auth/sign-in?back=/" hidden>Sign in</a>
      <button id="sign-out" type="button" hidden>Sign out</button>
    </header>
    <main id="desk" hidden>
      <nav aria-labelledby="yours-title">
        <h2 id="yours-title">Your conversations</h2>
        <button id="new" type="button">New conversation</button>
        <ul id="yours"></ul>
      </nav>
      <section aria-labelledby="chat-title">
        <h2 id="chat-title">Conversation</h2>
        <div id="log" role="log" aria-live="polite" aria-labelledby="chat-title"></div>
        <form id="ask">
          <label for="content">Message</label>
          <textarea id="content" name="content" maxlength="2000" rows="3"></textarea>
          <button id="send" type="submit">Send</button>
        </form>
        <p id="status" role="status" aria-live="polite"></p>
      </section>
      <section aria-labelledby="usage-title">
        <h2 id="usage-title">Usage</h2>
        <div id="usage"></div>
        <p id="usage-status" role="status" aria-live="polite"></p>
      </section>
    </main>
  </body>
</html>
"""

STYLES = """
body {
  font: 1rem/1.5 system-ui, sans-serif;
  margin: 0 auto;
  max-width: 60rem;
  padding: 1rem;
}
header { align-items: baseline; display: flex; flex-wrap: wrap; gap: 1rem; }
main { display: grid; gap: 2rem; }
#log { display: grid; gap: 0.75rem; }
.message { border-radius: 0.5rem; padding: 0.5rem 0.75rem; }
.message[data-role="caller"] { background: #eef2ff; }
.message[data-role="desk"] { background: #f4f4f5; }
.message p { margin: 0; }
.message .who { font-weight: 600; }
.message .text { white-space: pre-wrap; }
form { display: grid; gap: 0.5rem; }
textarea { font: inherit; }
table { border-collapse: collapse; }
th, td { border-bottom: 1px solid #d4d4d8; padding: 0.25rem 0.5rem; text-align: right; }
th[scope="row"], caption { text-align: left; }
[aria-current="true"] { font-weight: 600; }
"""

# What the desk's model costs, in dollars for a million tokens, if it isn't free.
PRICES = {"prompt": "DESK_PROMPT_PRICE", "completion": "DESK_COMPLETION_PRICE"}


def prices_from(environ: Mapping[str, str]) -> dict[str, float]:
    """Each price from its variable, 0 for one that isn't set."""
    prices = {}
    for kind, variable in PRICES.items():
        try:
            price = float(environ.get(variable, "0"))
        except ValueError:
            price = -1.0
        if not price >= 0:
            raise ValueError(f"{variable} should be a price of 0 or more.")
        prices[kind] = price
    return prices


def create() -> FastAPI:
    """The desk, with its page, once the page is built."""
    if not (STATIC / "page.js").is_file():
        raise RuntimeError("The page isn't built yet: run uv run sulba.py build first.")
    app = create_app()
    page = PAGE.format(**prices_from(os.environ))
    headers = {"Content-Security-Policy": POLICY}

    @app.get("/", include_in_schema=False)
    def chat_page() -> HTMLResponse:
        return HTMLResponse(page, headers=headers)

    @app.get("/page.css", include_in_schema=False)
    def styles() -> Response:
        return Response(STYLES, media_type="text/css")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app
