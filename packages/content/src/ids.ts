// Every course, level, module, lab, stage and test has a permanent id: written once and never
// changed, so progress stored against it survives renaming or reordering (decision record 7).

export const prefixes = {
  course: 'crs',
  level: 'lvl',
  module: 'mod',
  lab: 'lab',
  stage: 'stg',
  test: 'tst',
} as const;

export type IdKind = keyof typeof prefixes;

export function idPattern(kind: IdKind): RegExp {
  return new RegExp(`^${prefixes[kind]}_[0-9a-z]{6}$`);
}
