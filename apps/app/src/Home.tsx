import type { Learner } from '@sulba/data/account';
import { hasSession, localStore } from '@sulba/data/session';
import { Button, buttonClass } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { useEffect, useState } from 'react';
import styles from './Home.module.css';
import { appPath, signInPath } from './session';

const css = classes(styles, 'page', 'title', 'note');

type Visitor = { state: 'loading' } | { state: 'out' } | { state: 'in'; learner: Learner };

/** supabase-js and the account's helpers, loaded once the browser holds a session. */
const account = () => Promise.all([import('@sulba/data/account'), import('./supabase')]);

/** The app's first page: a way to sign in, or who is signed in. */
export function Home() {
  const [visitor, setVisitor] = useState<Visitor>(() =>
    hasSession(localStore()) ? { state: 'loading' } : { state: 'out' },
  );

  useEffect(() => {
    if (visitor.state !== 'loading') return;
    account()
      .then(([{ currentLearner }, { supabase }]) => currentLearner(supabase()))
      .then((learner) => setVisitor(learner ? { state: 'in', learner } : { state: 'out' }))
      .catch(() => setVisitor({ state: 'out' }));
  }, [visitor.state]);

  if (visitor.state === 'loading') return null;
  if (visitor.state === 'out') {
    return (
      <section className={css.page}>
        <h1 className={css.title}>Sign in to Sulba</h1>
        <p className={css.note}>Sign in with GitHub or Google.</p>
        <a className={buttonClass('primary', 'regular')} href={signInPath(appPath)}>
          Sign in
        </a>
      </section>
    );
  }
  return (
    <section className={css.page}>
      <h1 className={css.title}>Sulba</h1>
      <p className={css.note}>Signed in as {visitor.learner.email ?? 'you'}.</p>
      <Button
        variant="outline"
        onPress={async () => {
          const [{ signOut }, { supabase }] = await account();
          await signOut(supabase());
          setVisitor({ state: 'out' });
        }}
      >
        Sign out
      </Button>
    </section>
  );
}
