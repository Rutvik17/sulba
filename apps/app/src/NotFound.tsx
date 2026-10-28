import { classes } from '@sulba/ui/classes';
import { Link } from '@tanstack/react-router';
import styles from './Home.module.css';

const css = classes(styles, 'page', 'title', 'note');

/** An address under /app/ that the app has no page for. */
export function NotFound() {
  return (
    <section className={css.page}>
      <h1 className={css.title}>Page not found</h1>
      <p className={css.note}>There's nothing at this address.</p>
      <Link to="/">Go to Sulba</Link>
    </section>
  );
}
