import { useEffect } from 'react';

/** Names the browser's tab after the page, as the site does: "Members · Acme · Sulba". */
export function useTitle(...parts: readonly string[]): void {
  const title = [...parts, 'Sulba'].join(' · ');
  useEffect(() => {
    document.title = title;
  }, [title]);
}
