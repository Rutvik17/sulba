// The CodeMirror extensions that draw each colour theme in palettes.ts.
import { HighlightStyle, syntaxHighlighting, type TagStyle } from '@codemirror/language';
import type { Extension } from '@codemirror/state';
import { EditorView } from '@codemirror/view';
import type { Palette } from './palettes.ts';
import { roles } from './roles.ts';

/** The CodeMirror extensions that draw a palette. */
export function paletteTheme(palette: Palette): Extension {
  const { bg, fg, ln, cursor, sel } = palette;
  const view = EditorView.theme(
    {
      '&': { color: fg, backgroundColor: bg },
      '.cm-content': { caretColor: cursor },
      '.cm-cursor, .cm-dropCursor': { borderLeftColor: cursor },
      '&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection':
        { backgroundColor: sel },
      '.cm-gutters': { backgroundColor: bg, color: ln, border: 'none' },
      '.cm-activeLine': { backgroundColor: `color-mix(in srgb, ${fg} 4%, transparent)` },
      '.cm-activeLineGutter': { backgroundColor: 'transparent', color: fg },
      '.cm-matchingBracket, &.cm-focused .cm-matchingBracket': {
        backgroundColor: `color-mix(in srgb, ${cursor} 20%, transparent)`,
        outline: 'none',
      },
      '.cm-tooltip, .cm-panels': { backgroundColor: bg, color: fg },
      '.cm-tooltip-autocomplete > ul > li[aria-selected]': { backgroundColor: sel, color: fg },
    },
    { dark: palette.kind === 'dark' },
  );
  const code = HighlightStyle.define(
    roles.map(({ role, tags }) => {
      const style: TagStyle = { tag: tags, color: palette[role] };
      if (role === 'kw') style.fontWeight = palette.boldKeywords ? '600' : 'normal';
      if (role === 'com') style.fontStyle = palette.italicComments ? 'italic' : 'normal';
      return style;
    }),
  );
  return [view, syntaxHighlighting(code)];
}
