import { buttonClass } from '@sulba/ui/button';
import { Centered } from './Centered';
import { signInPath } from './session';

/** Asks someone who isn't signed in to sign in, and brings them back to the page they were on. */
export function SignIn() {
  const back = `${window.location.pathname}${window.location.search}`;

  return (
    <Centered title="Sign in to Sulba" tab="Sign in" lead="Sign in with GitHub or Google.">
      <a className={buttonClass('primary', 'regular')} href={signInPath(back)}>
        Sign in
      </a>
    </Centered>
  );
}
