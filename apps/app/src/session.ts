// The app shares the site's origin, so it shares the site's session: a person signs in on the
// site's sign-in page, which sends them back here (decision record 47).

/** Where the app lives on the site. */
export const appPath = '/app/';

/** The site's sign-in page, set to send the person back to `page` once they're signed in. */
export function signInPath(page: string): string {
  return `/sign-in/?next=${encodeURIComponent(page)}`;
}
