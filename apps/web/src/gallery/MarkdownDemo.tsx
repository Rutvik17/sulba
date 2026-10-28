import { Markdown } from '@sulba/editor/markdown';

const text = `## Context

Cards fail at random, and **most succeed a minute later**. Today a failed payment is final.

## Design

- Retry *once*, after 60 seconds
- Keep the same \`idempotency_key\`, so a card is never charged twice
- See [the card network's rules](https://example.com/rules)
`;

/** The Markdown editor as a spec's page shows it, to a member who can change it or a viewer. */
export default function MarkdownDemo({ readOnly = false }: { readOnly?: boolean }) {
  return (
    <Markdown
      defaultValue={readOnly ? (text.split('## Design')[0]?.trim() ?? '') : text}
      label={readOnly ? 'SPEC-3’s text' : 'SPEC-12’s text'}
      placeholder="Why this is needed, what it changes, and what it leaves out."
      readOnly={readOnly}
    />
  );
}
