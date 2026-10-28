// The learning site's pages sit under /academy/ (src/pages/academy), and every link to one is made
// here. public/_redirects sends the addresses they had before to them.

/** The Academy's home page. */
export const academy = '/academy/';

/** A page under it, from its path there: `review`, a course's slug, or a lab's path (labs.ts). */
export function academyPage(path: string): string {
  return `${academy}${path}/`;
}
