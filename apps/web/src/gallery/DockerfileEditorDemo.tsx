import { Editor } from '@sulba/editor/editor';

const code = `# The service's image: its packages from the lock, run as a user without root.
FROM python:3.15-slim@sha256:533b0b2f9b5d46fd097091cf826f27902f1d6c3bca714b6dc74551356aa97a51
COPY --from=ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff /uv /bin/
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
