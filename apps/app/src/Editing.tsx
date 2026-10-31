import { bodyLimit } from '@sulba/data/specs';
import { Markdown } from '@sulba/editor/markdown';
import { classes } from '@sulba/ui/classes';
import { useEffect, useRef, useState } from 'react';
import styles from './spec.module.css';

// The title and the Markdown text of a spec's or a request's page, which members edit in place.

const css = classes(styles, 'title', 'unseen', 'note', 'saved');

/** A title members edit in place, saved on Enter or on leaving the field; Escape undoes. */
export function EditableTitle({
  title: saved,
  canWrite,
  problemOf,
  onSave,
}: {
  title: string;
  canWrite: boolean;
  /** What's wrong with a title, or null. */
  problemOf: (title: string) => string | null;
  onSave: (title: string) => void;
}) {
  const [title, setTitle] = useState(saved);
  const problem = problemOf(title);
  useEffect(() => setTitle(saved), [saved]);

  if (!canWrite) return <h1 className={css.title}>{saved}</h1>;
  const save = () => {
    if (problem || title.trim() === saved) return;
    onSave(title);
  };
  return (
    <>
      <h1 className={css.unseen}>{saved}</h1>
      <input
        className={css.title}
        aria-label="Title"
        value={title}
        maxLength={200}
        onChange={(event) => setTitle(event.target.value)}
        onBlur={save}
        onKeyDown={(event) => {
          if (event.key === 'Enter') event.currentTarget.blur();
          if (event.key === 'Escape') {
            setTitle(saved);
            event.currentTarget.blur();
          }
        }}
        aria-invalid={problem !== null}
        aria-describedby={problem ? 'title-problem' : undefined}
      />
      {problem ? (
        <p id="title-problem" className={css.note} role="alert">
          {problem}
        </p>
      ) : null}
    </>
  );
}

type Saving = 'saved' | 'saving' | 'unsaved' | 'failed';

/** Markdown text, saved a moment after the writer stops typing, and on leaving the page. */
export function SavedText({
  text,
  label,
  placeholder,
  canWrite,
  save,
}: {
  text: string;
  label: string;
  /** What the editor says while it's empty, to someone who can write. */
  placeholder: string;
  canWrite: boolean;
  save: (text: string) => Promise<void>;
}) {
  const [saving, setSaving] = useState<Saving>('saved');
  const pending = useRef<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const flush = async () => {
    clearTimeout(timer.current);
    const changed = pending.current;
    if (changed === null) return;
    pending.current = null;
    setSaving('saving');
    try {
      await save(changed);
      setSaving(pending.current === null ? 'saved' : 'unsaved');
    } catch {
      pending.current ??= changed;
      setSaving('failed');
    }
  };

  // What's still unsaved when the page closes is saved on the way out.
  // biome-ignore lint/correctness/useExhaustiveDependencies: flush reads the latest text from a ref.
  useEffect(() => () => void flush(), []);

  const said: Record<Saving, string> = {
    saved: 'Saved',
    saving: 'Saving…',
    unsaved: 'Not saved yet',
    failed: 'Couldn’t save. Check your connection; it saves again as you type.',
  };
  return (
    <>
      <Markdown
        defaultValue={text}
        label={label}
        placeholder={canWrite ? placeholder : 'No text yet.'}
        limit={bodyLimit}
        readOnly={!canWrite}
        onChange={(changed) => {
          pending.current = changed;
          setSaving('unsaved');
          clearTimeout(timer.current);
          timer.current = setTimeout(() => void flush(), 1200);
        }}
        onBlur={() => void flush()}
      />
      {canWrite ? (
        <p className={css.saved} aria-live="polite">
          {said[saving]}
        </p>
      ) : null}
    </>
  );
}
