# The desk's image: the page compiled in a stage of its own, the packages the lock pins in
# another, and the desk with only what it runs on, as a user without root.
#
#   docker build --tag desk .

# The page: the TypeScript compiled to static/, with the packages package-lock.json pins.
FROM node:24.22.1-slim AS page
WORKDIR /page
COPY package.json package-lock.json tsconfig.json tsconfig.build.json ./
RUN npm ci --ignore-scripts
COPY *.ts ./
RUN ./node_modules/.bin/tsc --project tsconfig.build.json

# The packages the lock pins, without the dev group, which only the tests use.
FROM python:3.14.9-slim-trixie AS packages
COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /desk
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

# The desk: its packages, code, help pages and page, run as a user without root.
FROM python:3.14.9-slim-trixie
RUN groupadd --system --gid 999 desk \
    && useradd --system --gid 999 --uid 999 --no-create-home desk
WORKDIR /desk
COPY --from=packages /desk/.venv .venv
COPY *.py ./
COPY data data
COPY --from=page /page/static static
ENV PATH="/desk/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER desk
EXPOSE 8000
HEALTHCHECK --start-period=60s --timeout=5s \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health', timeout=4)"]
CMD ["python", "main.py"]
