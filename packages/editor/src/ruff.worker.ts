// Runs Ruff off the page's thread: it checks the learner's code as they type and formats it on
// request. Its WebAssembly loads the first time it's needed.
import init, { type Diagnostic, PositionEncoding, Workspace } from '@astral-sh/ruff-wasm-web';
import wasm from '@astral-sh/ruff-wasm-web/ruff_wasm_bg.wasm?url';
import { ruffSettings } from './ruff-settings.ts';

export interface ToRuff {
  readonly id: number;
  readonly type: 'check' | 'format';
  readonly code: string;
}

export type FromRuff =
  | { readonly id: number; readonly diagnostics: Diagnostic[] }
  /** The formatted code, or null when the code can't be parsed. */
  | { readonly id: number; readonly formatted: string | null };

interface Scope {
  postMessage(message: FromRuff): void;
  addEventListener(type: 'message', listener: (event: MessageEvent<ToRuff>) => void): void;
}

const scope = self as unknown as Scope;
const workspace = init({ module_or_path: wasm }).then(
  () => new Workspace(ruffSettings, PositionEncoding.Utf16),
);

scope.addEventListener('message', async ({ data }) => {
  const ruff = await workspace;
  if (data.type === 'check') {
    scope.postMessage({ id: data.id, diagnostics: ruff.check(data.code) as Diagnostic[] });
    return;
  }
  let formatted: string | null = null;
  try {
    formatted = ruff.format(data.code);
  } catch {
    // Code that doesn't parse can't be formatted; the syntax error is already marked.
  }
  scope.postMessage({ id: data.id, formatted });
});
