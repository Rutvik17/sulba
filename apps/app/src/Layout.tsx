import { classes } from '@sulba/ui/classes';
import { Link, Outlet } from '@tanstack/react-router';
import styles from './Layout.module.css';
import { Mark } from './Mark';

const css = classes(styles, 'bar', 'brand', 'main');

/** Every page of the app: the bar across the top, and the page below it. */
export function Layout() {
  return (
    <>
      <header className={css.bar}>
        <Link to="/" className={css.brand}>
          <Mark />
          <span>Sulba</span>
        </Link>
      </header>
      <main className={css.main}>
        <Outlet />
      </main>
    </>
  );
}
