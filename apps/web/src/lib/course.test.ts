import { expect, test } from 'vitest';
import { courseOutlines } from './course';
import type { LabEntry } from './labs';

function lab(order: number, path: string, level: string, module: string): LabEntry {
  return {
    id: `lab_${String(order).padStart(6, '0')}`,
    order,
    path,
    runs: 'browser',
    title: path.split('/')[2] ?? '',
    summary: '',
    course: path.startsWith('other') ? 'Other' : 'AI Engineering',
    level,
    levelNeeds: level === 'Intermediate' ? 'A laptop with 16 GB of memory' : 'Any laptop',
    module,
    data: [],
    references: [],
    fetch: [],
    models: [],
    given: [],
    project: [],
    code: [],
    stages: [],
    files: {},
    projectFiles: {},
    cards: [],
  };
}

test("a course's labs come back grouped by level and module, in the course's order", () => {
  const labs = [
    lab(2, 'ai-engineering/learning-from-data/cross-validation', 'Beginner', 'Learning from data'),
    lab(0, 'ai-engineering/maths-as-code/arrays', 'Beginner', 'The maths behind ML'),
    lab(3, 'ai-engineering/models/autograd', 'Intermediate', 'Models'),
    lab(1, 'ai-engineering/learning-from-data/linear-regression', 'Beginner', 'Learning from data'),
  ];
  const [course] = courseOutlines(labs);
  expect(course?.slug).toBe('ai-engineering');
  expect(course?.title).toBe('AI Engineering');
  expect(
    course?.levels.map(({ title, needs, modules }) => ({
      title,
      needs,
      modules: modules.map(({ slug, title, labs }) => ({
        slug,
        title,
        labs: labs.map((each) => each.path.split('/')[2]),
      })),
    })),
  ).toEqual([
    {
      title: 'Beginner',
      needs: 'Any laptop',
      modules: [
        { slug: 'maths-as-code', title: 'The maths behind ML', labs: ['arrays'] },
        {
          slug: 'learning-from-data',
          title: 'Learning from data',
          labs: ['linear-regression', 'cross-validation'],
        },
      ],
    },
    {
      title: 'Intermediate',
      needs: 'A laptop with 16 GB of memory',
      modules: [{ slug: 'models', title: 'Models', labs: ['autograd'] }],
    },
  ]);
});

test('each course gets its own outline', () => {
  const outlines = courseOutlines([
    lab(0, 'ai-engineering/learning-from-data/linear-regression', 'Beginner', 'Learning from data'),
    lab(0, 'other/first/one', 'First', 'First'),
  ]);
  expect(outlines.map(({ slug, title }) => [slug, title])).toEqual([
    ['ai-engineering', 'AI Engineering'],
    ['other', 'Other'],
  ]);
});
