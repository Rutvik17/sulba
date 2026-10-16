// Which of a palette's colours each kind of Python token takes: in the editor, and in the sample of
// each theme the theme panel shows.
import { type Tag, tags } from '@lezer/highlight';

export type Role = 'kw' | 'fn' | 'bi' | 'str' | 'num' | 'com' | 'op' | 'prop';

export const roles: readonly { readonly role: Role; readonly tags: readonly Tag[] }[] = [
  {
    role: 'kw',
    tags: [
      tags.keyword,
      tags.controlKeyword,
      tags.definitionKeyword,
      tags.moduleKeyword,
      tags.operatorKeyword,
    ],
  },
  {
    role: 'fn',
    tags: [
      tags.function(tags.variableName),
      tags.function(tags.definition(tags.variableName)),
      tags.function(tags.propertyName),
    ],
  },
  {
    role: 'bi',
    tags: [
      tags.className,
      tags.definition(tags.className),
      tags.bool,
      tags.null,
      tags.self,
      tags.standard(tags.variableName),
    ],
  },
  { role: 'str', tags: [tags.string, tags.special(tags.string)] },
  { role: 'num', tags: [tags.number] },
  { role: 'com', tags: [tags.comment, tags.lineComment] },
  {
    role: 'op',
    tags: [
      tags.operator,
      tags.compareOperator,
      tags.arithmeticOperator,
      tags.logicOperator,
      tags.bitwiseOperator,
      tags.updateOperator,
      tags.punctuation,
    ],
  },
  { role: 'prop', tags: [tags.propertyName] },
];
