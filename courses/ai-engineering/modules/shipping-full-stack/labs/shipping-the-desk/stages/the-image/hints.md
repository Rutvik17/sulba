`FROM node:24.22.1-slim AS page` names a stage, and `COPY --from=page /page/static static` copies what it made into a later one.

---

uv's image holds only uv: `COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /bin/` puts it in a stage. `uv sync --locked --no-dev` installs the lock's packages into `.venv`, and fails if the lock no longer matches `pyproject.toml`.

---

`groupadd` and `useradd` with `--system` make a user, and `USER` runs everything after it, the `CMD` included, as that user. The slim Python image has no curl, so the health check can be a line of Python with `urllib.request`.
