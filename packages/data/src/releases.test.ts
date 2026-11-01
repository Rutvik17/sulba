import { describe, expect, it } from 'vitest';
import type { CriterionProof } from './evidence.ts';
import { type Release, releaseBlockers, releaseDocument } from './releases.ts';

const proof = (
  spec: number,
  criterion: number,
  state: CriterionProof['state'],
): CriterionProof => ({
  criterionId: `c${spec}${criterion}`,
  specId: `s${spec}`,
  specNumber: spec,
  specTitle: `Spec ${spec}`,
  specStatus: 'approved',
  criterionNumber: criterion,
  text: `Criterion ${criterion}`,
  state,
  tests: state === 'unproven' ? 0 : 1,
  passed: state === 'proven' ? 1 : 0,
  failed: state === 'failing' ? 1 : 0,
  skipped: 0,
  suspectSince: null,
  checkedAt: null,
});

describe('releaseBlockers', () => {
  it('asks for a spec when none is drafted, leaving out abandoned and superseded ones', () => {
    expect(releaseBlockers([], [])).toEqual(['Draft at least one spec from it.']);
    expect(releaseBlockers([{ number: 1, status: 'abandoned' }], [])).toEqual([
      'Draft at least one spec from it.',
    ]);
  });

  it('names the specs not approved, without criteria, or with criteria not proven', () => {
    expect(
      releaseBlockers(
        [
          { number: 1, status: 'in_review' },
          { number: 2, status: 'approved' },
          { number: 3, status: 'implemented' },
          { number: 4, status: 'superseded' },
        ],
        [proof(3, 1, 'proven'), proof(3, 2, 'failing'), proof(3, 3, 'unproven')],
      ),
    ).toEqual([
      'SPEC-1 is in review, not approved.',
      'SPEC-2 has no criteria.',
      'SPEC-3 has 2 of 3 criteria not proven yet: AC-2, AC-3.',
    ]);
  });

  it('is empty once every spec is approved and every criterion proven', () => {
    expect(
      releaseBlockers(
        [{ number: 1, status: 'approved' }],
        [proof(1, 1, 'proven'), proof(1, 2, 'proven')],
      ),
    ).toEqual([]);
  });
});

describe('releaseDocument', () => {
  const release: Release = {
    id: 'r1',
    number: 1,
    note: 'First release for the front desk.',
    approvedBy: 'ada',
    approvedAt: '2026-10-31T09:00:00Z',
    specs: [
      {
        number: 3,
        title: 'Book a class',
        status: 'implemented',
        criteria: [
          { number: 1, text: 'A member books a class', tests: 2 },
          { number: 2, text: 'A full class | refuses a booking', tests: 1 },
        ],
        tasks: [
          {
            number: 7,
            title: 'Build the booking API',
            role: 'build',
            status: 'done',
            pullRequest: 'https://github.com/acme-co/booking/pull/12',
          },
        ],
      },
    ],
  };

  it('writes what was asked, the answers given, and how each criterion was proven', () => {
    expect(
      releaseDocument(
        {
          number: 2,
          title: 'A booking app',
          body: 'Members book classes from their phones.',
          questions: [
            {
              id: 'q1',
              text: 'Do members pay when they book?',
              answer: 'Yes, by card.',
              askedBy: 'ada',
              askedByAgent: 'Claude Code',
              answeredBy: 'ada',
              askedAt: '2026-10-30T09:00:00Z',
              answeredAt: '2026-10-30T10:00:00Z',
            },
            {
              id: 'q2',
              text: 'Can a member cancel?',
              answer: null,
              askedBy: 'ada',
              askedByAgent: 'Claude Code',
              answeredBy: null,
              askedAt: '2026-10-30T09:00:00Z',
              answeredAt: null,
            },
          ],
        },
        release,
        'Ada Lovelace',
      ),
    ).toBe(
      [
        '# REQ-2 A booking app: release 1',
        '',
        'Approved by Ada Lovelace on October 31, 2026 (UTC).',
        '',
        '> First release for the front desk.',
        '',
        '## What was asked',
        '',
        'Members book classes from their phones.',
        '',
        '## Questions answered',
        '',
        '- **Do members pay when they book?**',
        '  Yes, by card.',
        '',
        '## What was built',
        '',
        '### SPEC-3 Book a class',
        '',
        'Implemented. Every criterion was proven by the tests that name it when the release was approved.',
        '',
        '| Criterion | Proven by |',
        '| --- | --- |',
        '| AC-1 A member books a class | 2 tests |',
        '| AC-2 A full class \\| refuses a booking | 1 test |',
        '',
        'Tasks:',
        '',
        '- TASK-7 Build the booking API (Build; Done, https://github.com/acme-co/booking/pull/12)',
        '',
      ].join('\n'),
    );
  });
});
