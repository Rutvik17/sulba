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

test('tst_ol2xfc A screen reader can tell which day and column each number is', () => {
  const usage = [day('2026-10-22', 25, 24, 51_000, 6_000, 1.5, 3.25)];
  const table = usageTable(page(), usage, 2, new Date('2026-10-22T15:00:00Z'), prices);
  assert.ok(table.caption?.textContent?.trim(), 'The table has no caption.');
  const head = table.tHead?.querySelector('tr');
  assert.ok(head, 'The table has no header row.');
  for (const cell of Array.from(head.children)) {
    assert.equal(`${cell.tagName} ${cell.getAttribute('scope')}`, 'TH col');
  }
  for (const section of [...Array.from(table.tBodies), table.tFoot]) {
    for (const row of Array.from(section?.querySelectorAll('tr') ?? [])) {
      const kinds = Array.from(
        row.children,
        (cell) => `${cell.tagName} ${cell.getAttribute('scope')}`,
      );
      assert.deepEqual(kinds, ['TH row', ...Array(7).fill('TD null')]);
    }
  }
});

test('tst_vl4u3h The days are UTC days, whatever the time zone', () => {
  const zone = process.env.TZ;
  try {
    for (const [timeZone, now] of [
      // 20:00 on 21 October there, and 04:00 on 23 October.
      ['America/Los_Angeles', '2026-10-22T03:00:00Z'],
      ['Pacific/Auckland', '2026-10-22T15:00:00Z'],
    ] as const) {
      process.env.TZ = timeZone;
      const usage = [day('2026-10-21', 25, 24, 51_000, 6_000, 1.5, 3.25)];
      const table = usageTable(page(), usage, 2, new Date(now), prices);
      assert.deepEqual(
        cells(table.tBodies[0]).map((row) => row.slice(0, 2)),
        [
          ['Wed, Oct 21', '25'],
          ['Thu, Oct 22', '0'],
        ],
        `In ${timeZone}`,
      );
    }
  } finally {
    if (zone === undefined) delete process.env.TZ;
    else process.env.TZ = zone;
  }
});

test('tst_9bfm9o A day without turns shows no share done and no times', () => {
  const table = usageTable(page(), [], 2, new Date('2026-10-22T15:00:00Z'), prices);
  for (const row of [...cells(table.tBodies[0]), ...cells(table.tFoot)]) {
    assert.deepEqual([row[2], row[6], row[7]], ['—', '—', '—']);
  }
});

test('tst_udihjx A request that fails shows its problem, and no numbers from before', async () => {
  const document = page();
  const place = document.createElement('div');
  const status = document.createElement('p');
  const answers = [
    Response.json([day('2026-10-22', 25, 24, 51_000, 6_000, 1.5, 3.25)]),
    Response.json(
      { type: 'about:blank', title: 'Forbidden', status: 403, detail: 'Sign in first.' },
      { status: 403, headers: { 'Content-Type': 'application/problem+json' } },
    ),
    Response.json([]),
  ];
  const fetcher: typeof fetch = async () => {
    const answer = answers.shift();
    assert.ok(answer, 'The dashboard asked once too often.');
    return answer;
  };
  const dashboard = new Dashboard(new Desk(fetcher), prices, { place, status });
  const now = new Date('2026-10-22T15:00:00Z');
  await dashboard.show(7, now);
  assert.equal(place.querySelectorAll('table').length, 1);
  await dashboard.show(7, now);
  assert.equal(status.textContent, 'Sign in first.');
  assert.equal(place.querySelectorAll('table').length, 0, 'The numbers from before still show.');
  await dashboard.show(7, now);
  assert.equal(status.textContent, '');
  assert.equal(place.querySelectorAll('table').length, 1);
});
