/**
 * The scoped names of a CSS Module's classes. A name the stylesheet doesn't define throws as soon
 * as the component loads, rather than leaving an element unstyled.
 */
export function classes<const Name extends string>(
  module: Readonly<Record<string, string>>,
  ...names: Name[]
): Readonly<Record<Name, string>> {
  return Object.fromEntries(
    names.map((name) => {
      const scoped = module[name];
      if (scoped === undefined) throw new Error(`The stylesheet has no .${name} class`);
      return [name, scoped];
    }),
  ) as Record<Name, string>;
}
