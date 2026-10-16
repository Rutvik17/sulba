// A few lines of Python split into tokens, each with the colour the editor gives it, for the sample
// of each theme in the theme panel. It runs when the site is built, so no page loads the parser to
// show it.
import { pythonLanguage } from '@codemirror/lang-python';
import { highlightCode, tagHighlighter } from '@lezer/highlight';
import { type Role, roles } from './roles.ts';

export interface Token {
  readonly text: string;
  /** The palette colour the editor gives it; text without one takes the palette's own. */
  readonly role?: Role;
}

const highlighter = tagHighlighter(
  roles.flatMap(({ role, tags }) => tags.map((tag) => ({ tag, class: role }))),
);

const isRole = (name: string): name is Role => roles.some(({ role }) => role === name);

/** Each line of the code, as its tokens. */
export function specimen(code: string): Token[][] {
  const lines: Token[][] = [[]];
  highlightCode(
    code,
    pythonLanguage.parser.parse(code),
    highlighter,
    (text, role) => lines.at(-1)?.push(isRole(role) ? { text, role } : { text }),
    () => lines.push([]),
  );
  return lines;
}
