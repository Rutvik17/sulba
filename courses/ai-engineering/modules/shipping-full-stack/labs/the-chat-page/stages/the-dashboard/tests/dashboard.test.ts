import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { Window } from 'happy-dom';
import { type Day, Desk } from '#api.ts';
import { Dashboard, type Prices, usageTable } from '#dashboard.ts';

const windows: Window[] = [];
after(async () => {
  for (const window of windows) await window.happyDOM.close();
});

function page(): Document {
  const window = new Window({ url: 'https://desk.test/' });
  windows.push(window);
  return window.document as unknown as Document;
}

const prices: Prices = { prompt: 0.4, completion: 1.6 };

function day(date: string, turns = 0, done = 0, prompt = 0, completion = 0, p50 = 0, p90 = 0): Day {
  return {
    day: date,
    turns,
    done,
    prompt_tokens: prompt,
    completion_tokens: completion,
    p50_seconds: p50,
    p90_seconds: p90,
  };
}

/** The text of each cell of each row of a part of the table. */
function cells(section: HTMLTableSectionElement | null | undefined): string[][] {
  assert.ok(section, 'The table is missing a part.');
  return Array.from(section.querySelectorAll('tr'), (row) =>
    Array.from(row.children, (cell) => cell.textContent ?? ''),
  );
}

test("tst_lflo5s Each day of the range is a row, earliest first and today's last", async () => {
  const document = page();
  const place = document.createElement('div');
  const status = document.createElement('p');
  const asked: string[] = [];
  const fetcher: typeof fetch = async (input) => {
    asked.push(String(input));
    const usage = [day('2026-10-21', 25, 24, 51_000, 6_000, 1.5, 3.25)];
    return Response.json(usage);
  };
  const dashboard = new Dashboard(new Desk(fetcher), prices, { place, status });
  await dashboard.show(3, new Date('2026-10-22T15:00:00Z'));
  assert.deepEqual(asked, ['/usage?days=3']);
  const table = place.querySelector('table');
  assert.ok(table, 'The dashboard shows no table.');
  assert.deepEqual(
    cells(table.tBodies[0]).map((row) => row.slice(0, 2)),
    [
      ['Tue, Oct 20', '0'],
      ['Wed, Oct 21', '25'],
      ['Thu, Oct 22', '0'],
    ],
  );
});

test('tst_36dpfm A day shows its turns, the share done, its tokens and its times', () => {
  const usage = [day('2026-10-22', 1234, 1135, 2_345_678, 123_456, 1.234, 4.56)];
  const table = usageTable(page(), usage, 1, new Date('2026-10-22T15:00:00Z'), prices);
  const [row] = cells(table.tBodies[0]);
  assert.deepEqual(row?.slice(0, 5), ['Thu, Oct 22', '1,234', '92%', '2,345,678', '123,456']);
  assert.deepEqual(row?.slice(6), ['1.2 sec', '4.6 sec']);
  assert.deepEqual(cells(table.tHead)[0], [
    'Day',
    'Turns',
    'Done',
    'Prompt tokens',
    'Reply tokens',
    'Cost',
    'Median',
    '90th percentile',
  ]);
});

test("tst_c0qn31 A day's cost is its tokens at the model's prices", () => {
  const usage = [
    day('2026-10-21', 1234, 1135, 2_345_678, 123_456, 1.234, 4.56),
    day('2026-10-22', 10, 10, 2_500, 500, 1, 2),
  ];
  const table = usageTable(page(), usage, 2, new Date('2026-10-22T15:00:00Z'), prices);
  assert.deepEqual(
    cells(table.tBodies[0]).map((row) => row[5]),
    ['$1.1358', '$0.0018'],
  );
});

test('tst_4i23bg The total adds up the days, and has no median or 90th percentile', () => {
  const usage = [
    day('2026-10-21', 1234, 1135, 2_345_678, 123_456, 1.234, 4.56),
    day('2026-10-22', 766, 765, 654_322, 76_544, 0.9, 2),
  ];
  const table = usageTable(page(), usage, 3, new Date('2026-10-22T15:00:00Z'), prices);
  assert.deepEqual(cells(table.tFoot), [
    ['Total', '2,000', '95%', '3,000,000', '200,000', '$1.52', '—', '—'],
  ]);
});
