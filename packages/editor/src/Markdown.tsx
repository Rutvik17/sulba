import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands';
import { markdown, markdownLanguage } from '@codemirror/lang-markdown';
import { HighlightStyle, syntaxHighlighting } from '@codemirror/language';
import { EditorState } from '@codemirror/state';
import { drawSelection, EditorView, placeholder as hint, keymap } from '@codemirror/view';
import { tags } from '@lezer/highlight';
import { classes } from '@sulba/ui/classes';
import { useEffect, useRef, useState } from 'react';
import styles from './markdown.module.css';

const css = classes(styles, 'markdown', 'text', 'count');

// Markdown as it's written, with its marks kept but quiet: headings in weight, emphasis in style,
// code in the code font, and the marks themselves dimmed. It draws in the page's own colours.
const style = HighlightStyle.define([
  { tag: tags.heading1, fontWeight: '600', fontSize: '1.25em' },
  { tag: tags.heading2, fontWeight: '600', fontSize: '1.125em' },
  { tag: [tags.heading3, tags.heading4, tags.heading5, tags.heading6], fontWeight: '600' },
  { tag: tags.strong, fontWeight: '600' },
  { tag: tags.emphasis, fontStyle: 'italic' },
  { tag: tags.strikethrough, textDecoration: 'line-through' },
  { tag: [tags.link, tags.url], color: 'var(--accent)', textDecoration: 'underline' },
  { tag: tags.monospace, fontFamily: 'var(--font-mono)', fontSize: '0.92em' },
  { tag: [tags.processingInstruction, tags.contentSeparator, tags.meta], color: 'var(--dim)' },
  { tag: tags.quote, color: 'var(--dim)' },
]);

export interface MarkdownProps {
  /** The text the editor opens with. */
  readonly defaultValue: string;
  /** The editor's name for screen readers. */
  readonly label: string;
  /** What the editor says while it's empty. */
  readonly placeholder?: string;
  /** The most characters it takes; typing past it does nothing. */
  readonly limit?: number;
  readonly onChange?: (text: string) => void;
  /** Called when the editor loses focus. */
  readonly onBlur?: () => void;
  readonly readOnly?: boolean;
}

/**
 * A Markdown editor for prose, such as a spec: lines wrap, there are no line numbers, Tab
 * indents a list and Escape then Tab leaves the editor. Near its limit it counts what's left.
 */
export function Markdown({
  defaultValue,
  label,
  placeholder,
  limit,
  onChange,
  onBlur,
  readOnly = false,
}: MarkdownProps) {
  const host = useRef<HTMLDivElement>(null);
  const changed = useRef(onChange);
  changed.current = onChange;
  const left = useRef(onBlur);
  left.current = onBlur;
  const [length, setLength] = useState(defaultValue.length);

  // The editor is made once; its text changes only through it.
  // biome-ignore lint/correctness/useExhaustiveDependencies: later props reach the editor through refs.
  useEffect(() => {
    if (!host.current) return;
    const editor = new EditorView({
      parent: host.current,
      state: EditorState.create({
        doc: defaultValue,
        extensions: [
          history(),
          drawSelection(),
          EditorView.lineWrapping,
          markdown({ base: markdownLanguage }),
          syntaxHighlighting(style),
          keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
          placeholder ? hint(placeholder) : [],
          limit === undefined
            ? []
            : EditorState.changeFilter.of((transaction) => transaction.newDoc.length <= limit),
          EditorState.readOnly.of(readOnly),
          EditorView.editable.of(!readOnly),
          EditorView.contentAttributes.of({ 'aria-label': label, tabindex: '0' }),
          EditorView.domEventHandlers({ blur: () => left.current?.() }),
          EditorView.updateListener.of((update) => {
            if (!update.docChanged) return;
            setLength(update.state.doc.length);
            changed.current?.(update.state.doc.toString());
          }),
        ],
      }),
    });
    return () => editor.destroy();
  }, []);

  const near = limit !== undefined && length > limit * 0.9;
  return (
    <div className={css.markdown}>
      <div className={css.text} ref={host} />
      {near ? (
        <p className={css.count} aria-live="polite">
          {(limit - length).toLocaleString()} characters left
        </p>
      ) : null}
    </div>
  );
}
