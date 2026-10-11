// How Ruff checks and formats learners' Python: its default rules, which catch syntax errors,
// undefined and unused names and a few statement mistakes, and its default style.
import type { Diagnostic as RuffDiagnostic } from '@astral-sh/ruff-wasm-web';
import type { Diagnostic } from '@codemirror/lint';
import type { Text } from '@codemirror/state';

export const ruffSettings = {
  'line-length': 88,
  'indent-width': 4,
  lint: { select: ['E4', 'E7', 'E9', 'F'] },
};

// Names Python can't find raise an error the moment the line runs.
const errors = new Set(['invalid-syntax', 'F821', 'F822', 'F823']);

/** Ruff's findings as CodeMirror diagnostics. Ruff counts rows and columns from 1, in UTF-16. */
export function toDiagnostics(doc: Text, found: readonly RuffDiagnostic[]): Diagnostic[] {
  const at = ({ row, column }: { row: number; column: number }) => {
    if (row > doc.lines) return doc.length;
    const line = doc.line(Math.max(row, 1));
    return Math.min(line.from + Math.max(column, 1) - 1, line.to);
  };
  return found.map((each) => {
    const from = at(each.start_location);
    const to = Math.max(at(each.end_location), from);
    const unnecessary = each.tags.includes('unnecessary');
    return {
      from,
      to,
      severity: each.code && errors.has(each.code) ? 'error' : unnecessary ? 'hint' : 'warning',
      message: each.message,
      ...(each.code && each.code !== 'invalid-syntax' ? { source: each.code } : {}),
      ...(unnecessary ? { markClass: 'cm-lintRange-unnecessary' } : {}),
    };
  });
}
