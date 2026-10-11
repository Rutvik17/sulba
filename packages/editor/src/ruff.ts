// Ruff in the editor: a lint source that checks the code as the learner types, and a command
// that formats it. One worker serves every editor on the page and starts when first needed.
import { linter } from '@codemirror/lint';
import type { Command } from '@codemirror/view';
import type { FromRuff, ToRuff } from './ruff.worker.ts';
import { toDiagnostics } from './ruff-settings.ts';

let worker: Worker | null = null;
let next = 0;
const waiting = new Map<number, (reply: FromRuff) => void>();

function ask(request: Omit<ToRuff, 'id'>): Promise<FromRuff> {
  if (!worker) {
    worker = new Worker(new URL('./ruff.worker.ts', import.meta.url), { type: 'module' });
    worker.addEventListener('message', ({ data }: MessageEvent<FromRuff>) => {
      waiting.get(data.id)?.(data);
      waiting.delete(data.id);
    });
  }
  const id = next++;
  return new Promise((resolve) => {
    waiting.set(id, resolve);
    worker?.postMessage({ ...request, id } satisfies ToRuff);
  });
}

/** Marks syntax errors and likely mistakes a moment after the learner stops typing. */
export const ruffLint = linter(
  async (view) => {
    const code = view.state.doc.toString();
    const reply = await ask({ type: 'check', code });
    // Typing since the check began moves every position; the next check marks the new code.
    if (!('diagnostics' in reply) || view.state.doc.toString() !== code) return [];
    return toDiagnostics(view.state.doc, reply.diagnostics);
  },
  { delay: 300 },
);

/** Formats the whole file in Ruff's style, unless the learner has typed since asking. */
export const formatCode: Command = (view) => {
  const code = view.state.doc.toString();
  void ask({ type: 'format', code }).then((reply) => {
    if (!('formatted' in reply) || reply.formatted === null) return;
    if (reply.formatted === code || view.state.doc.toString() !== code) return;
    const line = view.state.doc.lineAt(view.state.selection.main.head).number;
    view.dispatch({ changes: { from: 0, to: code.length, insert: reply.formatted } });
    const kept = view.state.doc.line(Math.min(line, view.state.doc.lines));
    view.dispatch({ selection: { anchor: kept.to }, scrollIntoView: true });
  });
  return true;
};
