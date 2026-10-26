import { Editor } from '@sulba/editor/editor';

const code = `# The service's image: its packages from the lock, run as a user without root.
FROM python:3.14-slim@sha256:35caba83af2fe6da9a5d922f9b0156f21d1246a48278c58a08bd253303ba42e8
COPY --from=ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21 /uv /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY *.py ./
USER nobody
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0"]
`;

/** A Dockerfile solution, as a lab that runs on the learner's machine shows it. */
export default function DockerfileEditorDemo() {
  return (
    <div className="editor-frame fit">
      <Editor defaultValue={code} label="Solution" language="dockerfile" readOnly />
    </div>
  );
}
