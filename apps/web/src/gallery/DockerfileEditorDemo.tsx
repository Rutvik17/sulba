import { Editor } from '@sulba/editor/editor';

const code = `# The service's image: its packages from the lock, run as a user without root.
FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /bin/
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
