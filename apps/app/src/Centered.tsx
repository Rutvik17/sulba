import { classes } from '@sulba/ui/classes';
import type { ReactNode } from 'react';
import styles from './Centered.module.css';
import { Mark } from './Mark';
import { useTitle } from './title';

const css = classes(styles, 'bar', 'brand', 'main', 'column', 'form', 'title', 'lead');

/** The class of a form in a centred page's column. */
export const centeredForm = css.form;

/**
 * A page outside any workspace, such as signing in, creating a workspace or joining one: the mark
 * across the top, and one column in the middle with its title and what it's for.
 */
export function Centered({
  title,
  tab = title,
  lead,
  children,
}: {
  title: string;
  /** The browser tab's name for the page, when it isn't the title. */
  tab?: string;
  lead?: ReactNode;
  children?: ReactNode;
}) {
  useTitle(tab);
  return (
    <>
      <header className={css.bar}>
        <a href="/app/" className={css.brand}>
          <Mark />
          <span>Sulba</span>
        </a>
      </header>
      <main className={css.main}>
        <section className={css.column}>
          <h1 className={css.title}>{title}</h1>
          {lead ? <p className={css.lead}>{lead}</p> : null}
          {children}
        </section>
      </main>
    </>
  );
}
