import {
  autocompletion,
  closeBrackets,
  closeBracketsKeymap,
  completionKeymap,
} from '@codemirror/autocomplete';
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands';
import { javascript } from '@codemirror/lang-javascript';
import { python } from '@codemirror/lang-python';
import { bracketMatching, indentOnInput, indentUnit } from '@codemirror/language';
import { forEachDiagnostic, lintGutter, lintKeymap } from '@codemirror/lint';
import { highlightSelectionMatches, searchKeymap } from '@codemirror/search';
import { Compartment, EditorState } from '@codemirror/state';
import {
  drawSelection,
  EditorView,
  highlightActiveLine,
  highlightActiveLineGutter,
  keymap,
  lineNumbers,
  tooltips,
} from '@codemirror/view';
import { classes } from '@sulba/ui/classes';
import {
  type Ref,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  useSyncExternalStore,
} from 'react';
import { chosenPalette, onChoice } from './choice.ts';
import styles from './editor.module.css';
import { sulba } from './palettes.ts';
import { formatCode, ruffLint } from './ruff.ts';
import { paletteTheme } from './themes.ts';

const css = classes(styles, 'editor', 'code', 'status');

// Tooltips, such as the completion list and Ruff's messages, sit in the page's body, so the
// editor's frame can't cut them off. Otherwise CodeMirror puts them inside the editor in Safari,
// always on an iPhone and at times on a Mac. The frame's CSS Module can't reach them in the body,
// so their look is part of the editor's theme.
const tooltipTheme = EditorView.theme({
  '.cm-tooltip': {
    overflow: 'hidden',
    border: '1px solid var(--line-2)',
    borderRadius: 'var(--radius-sm)',
    boxShadow: 'var(--shadow)',
    fontFamily: 'var(--font-sans)',
    fontSize: 'var(--text-sm)',
  },
  '.cm-diagnostic': { padding: 'var(--space-2) var(--space-3)' },
  '.cm-diagnosticSource': { opacity: '0.75' },
});

export interface EditorHandle {
  /** The code as it stands. */
  code(): string;
  /** Replace the code, as a reset to the starter does. Undo brings the old code back. */
  replace(code: string): void;
  /** Put the cursor at the start of a line, counted from 1, and focus the editor. */
  goTo(line: number): void;
}

/**
 * Each language the editor reads: how it highlights it, the spaces of an indent, and its name.
 * Ruff checks and formats Python only.
 */
const languages = {
  python: { highlight: () => python(), spaces: 4, name: 'Python' },
  typescript: { highlight: () => javascript({ typescript: true }), spaces: 2, name: 'TypeScript' },
};

export type Language = keyof typeof languages;

export interface EditorProps {
  /** The code the editor opens with. */
  readonly defaultValue: string;
  /** The code's language, Python unless it says otherwise. */
  readonly language?: Language;
  /** The editor's name for screen readers, such as the file's name. */
  readonly label: string;
  readonly onChange?: (code: string) => void;
  /** Called on Ctrl+Enter, or Cmd+Enter on a Mac. */
  readonly onRun?: () => void;
  readonly readOnly?: boolean;
  readonly ref?: Ref<EditorHandle>;
}

interface Status {
  readonly line: number;
  readonly column: number;
  readonly errors: number;
  readonly warnings: number;
}

function statusOf(state: EditorState): Status {
  const head = state.selection.main.head;
  const line = state.doc.lineAt(head);
  let errors = 0;
  let warnings = 0;
  forEachDiagnostic(state, (diagnostic) => {
    if (diagnostic.severity === 'error') errors++;
    else if (diagnostic.severity === 'warning') warnings++;
  });
  return { line: line.number, column: head - line.from + 1, errors, warnings };
}

function count(n: number, one: string, many: string) {
  return `${n} ${n === 1 ? one : many}`;
}

/**
 * A code editor: highlighting, completion, closing brackets and Ctrl+/ to comment, and in Python,
 * Ruff's checks as you type, with Shift+Alt+F to format. Tab indents; Escape then Tab leaves the
 * editor. It draws in the editor theme the learner chose (choice.ts).
 */
export function Editor({
  defaultValue,
  language = 'python',
  label,
  onChange,
  onRun,
  readOnly = false,
  ref,
}: EditorProps) {
  const palette = useSyncExternalStore(onChoice, chosenPalette, () => sulba);
  const host = useRef<HTMLDivElement>(null);
  const view = useRef<EditorView | null>(null);
  const theme = useRef(new Compartment());
  const changed = useRef(onChange);
  changed.current = onChange;
  const run = useRef(onRun);
  run.current = onRun;
  const [status, setStatus] = useState<Status>({ line: 1, column: 1, errors: 0, warnings: 0 });
  const { highlight, spaces, name } = languages[language];
  const ruff = language === 'python';

  // The editor is made once. Its theme changes in place; its text changes only through it.
  // biome-ignore lint/correctness/useExhaustiveDependencies: later props reach the editor through refs and compartments.
  useEffect(() => {
    if (!host.current) return;
    const editor = new EditorView({
      parent: host.current,
      state: EditorState.create({
        doc: defaultValue,
        extensions: [
          lineNumbers(),
          highlightActiveLineGutter(),
          history(),
          drawSelection(),
          indentUnit.of(' '.repeat(spaces)),
          EditorState.tabSize.of(spaces),
          indentOnInput(),
          bracketMatching(),
          closeBrackets(),
          autocompletion(),
          highlightActiveLine(),
          highlightSelectionMatches(),
          highlight(),
          // Code that can't be changed, such as a solution, is shown without Ruff's marks.
          ruff && !readOnly ? [ruffLint, lintGutter()] : [],
          keymap.of([
            {
              key: 'Mod-Enter',
              run: () => {
                run.current?.();
                return run.current !== undefined;
              },
            },
            ...(ruff ? [{ key: 'Shift-Alt-f', run: formatCode }] : []),
            ...closeBracketsKeymap,
            ...defaultKeymap,
            ...searchKeymap,
            ...historyKeymap,
            ...completionKeymap,
            ...lintKeymap,
            indentWithTab,
          ]),
          EditorState.readOnly.of(readOnly),
          // The code area takes focus already; the tabindex says so to checkers such as axe, which
          // otherwise see the scrolling area around it as one a keyboard can't reach.
          EditorView.contentAttributes.of({ 'aria-label': label, tabindex: '0' }),
          tooltips({ parent: document.body }),
          tooltipTheme,
          theme.current.of(paletteTheme(palette)),
          EditorView.updateListener.of((update) => {
            if (update.docChanged) changed.current?.(update.state.doc.toString());
            setStatus(statusOf(update.state));
          }),
        ],
      }),
    });
    view.current = editor;
    return () => {
      editor.destroy();
      view.current = null;
    };
  }, []);

  useEffect(() => {
    view.current?.dispatch({ effects: theme.current.reconfigure(paletteTheme(palette)) });
  }, [palette]);

  useImperativeHandle(ref, () => ({
    code: () => view.current?.state.doc.toString() ?? '',
    replace(code) {
      const editor = view.current;
      if (!editor) return;
      editor.dispatch({ changes: { from: 0, to: editor.state.doc.length, insert: code } });
    },
    goTo(line) {
      const editor = view.current;
      if (!editor) return;
      const { from } = editor.state.doc.line(Math.min(Math.max(line, 1), editor.state.doc.lines));
      editor.dispatch({ selection: { anchor: from }, scrollIntoView: true });
      editor.focus();
    },
  }));

  return (
    <div className={css.editor}>
      <div className={css.code} ref={host} />
      {!readOnly && (
        <div className={css.status}>
          <span>
            Ln {status.line}, Col {status.column}
          </span>
          <span>
            {count(status.errors, 'error', 'errors')},{' '}
            {count(status.warnings, 'warning', 'warnings')}
          </span>
          <span>Spaces: {spaces}</span>
          <span>{name}</span>
        </div>
      )}
    </div>
  );
}
