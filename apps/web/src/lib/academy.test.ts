import { expect, test } from 'vitest';
import { academy, academyPage } from './academy';

test("the Review page, a course's page and a lab's sit under the Academy's home page", () => {
  expect(academy).toBe('/academy/');
  expect(academyPage('review')).toBe('/academy/review/');
  expect(academyPage('ai-engineering')).toBe('/academy/ai-engineering/');
  expect(academyPage('ai-engineering/models/autograd')).toBe(
    '/academy/ai-engineering/models/autograd/',
  );
});
