import { readFile } from 'node:fs/promises';
import { deflateRawSync } from 'node:zlib';
import { expect, type Page, test } from '@playwright/test';
import { strFromU8, unzipSync } from 'fflate';
import { signedIn, standIn } from './supabase';

// The fixture course's lab Ledger runs on the learner's machine (decision record 28): its stages,
// balance, audit, close, statement and receipt, run from its download, and the runner's links
// mark them done here.
const path = '/demo/ledgers/ledger/';

/** A link from the runner to the lab's page, carrying `payload` as sulba.py writes it. */
function linkOf(payload: object): string {
  return `${path}#run=${deflateRawSync(JSON.stringify(payload)).toString('base64url')}`;
}

const pass = (id: string, stage: string, review: object | null = null) => [
  id,
  stage,
  'v1',
  'pass',
  null,
  null,
  review,
  30,
  '2026-10-18T16:00:30.000Z',
  '2026-10-18',
];

const run = (id: string, stage: string) => [
  id,
  stage,
  'v1',
  'run',
  [2, 2],
  null,
  null,
  0,
  '2026-10-18T16:00:00.000Z',
  '2026-10-18',
];

const stages = (page: Page) => page.getByRole('navigation', { name: 'Stages' });

test('a lab that runs on the machine says how to run it there, and loads no Python here', async ({
  page,
}) => {
  const fetched: string[] = [];
  page.on('request', (request) => fetched.push(new URL(request.url()).pathname));
  await page.goto(path);

  await expect(page.getByRole('heading', { level: 2, name: 'Balance' })).toBeVisible();
  await expect(page.getByText('The ledger has 3 entries.')).toBeVisible();
  await expect(page.getByText('uv run sulba.py', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Download' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Run tests' })).toHaveCount(0);
  await expect(page.getByText('Runs on')).toBeVisible();
  expect(fetched.filter((each) => each.startsWith('/pyodide/'))).toEqual([]);
});

test('a lab that fetches files says how much its first run downloads, and from where', async ({
  page,
}) => {
  await page.goto(path);

  await expect(
    page.getByText(
      'The first time, it also downloads the files the lab needs into data: 5.1 kB, from fashion-mnist.s3.eu-central-1.amazonaws.com.',
    ),
  ).toBeVisible();
  const credit = page.getByText('Data: Fashion-MNIST, by Zalando Research, MIT.');
  await expect(credit).toBeVisible();
  await expect(credit.getByRole('link', { name: 'Fashion-MNIST' })).toHaveAttribute(
    'href',
    'https://github.com/zalandoresearch/fashion-mnist',
  );
});

test('a lab with TypeScript stages says what their first run downloads, and from where', async ({
  page,
}) => {
  await page.goto(path);

  await expect(
    page.getByText(
      'Its TypeScript stages run in Node.js. The first time, it downloads Node.js for your system from nodejs.org, and the lab’s packages from registry.npmjs.org.',
    ),
  ).toBeVisible();
});

test('a lab with Go stages says what their first run downloads, and from where', async ({
  page,
}) => {
  await page.goto(path);

  await expect(
    page.getByText(
      'Its Go stages run with Go. The first time, it downloads Go for your system from dl.google.com.',
    ),
  ).toBeVisible();
});

test('a lab with models says how to start them and what that downloads, and credits each', async ({
  page,
}) => {
  await page.goto(path);

  await expect(
    page.getByText(
      'uv run sulba.py model starts the lab’s models, stories260K, bge-small-en-v1.5 and jina-reranker-v1-tiny-en, on your machine, where your code can call each by its name at http://127.0.0.1:9931/v1. The first time, it downloads the models, 136.0 MB, from huggingface.co, and llama.cpp’s server for your system, from github.com.',
    ),
  ).toBeVisible();
  const credit = page.getByText('Model: stories260K, by Andrej Karpathy, MIT.');
  await expect(credit).toBeVisible();
  await expect(credit.getByRole('link', { name: 'stories260K' })).toHaveAttribute(
    'href',
    'https://huggingface.co/karpathy/tinyllamas',
  );
  await expect(page.getByText('Model: bge-small-en-v1.5, by BAAI, MIT.')).toBeVisible();
  await expect(
    page.getByText('Model: jina-reranker-v1-tiny-en, by Jina AI, Apache License 2.0.'),
  ).toBeVisible();
});

test('its download holds the project, the runner, its stages and the first stage’s code', async ({
  page,
}) => {
  await page.goto(path);
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'Download' }).click(),
  ]);

  expect(download.suggestedFilename()).toBe('ledger.zip');
  const files = unzipSync(new Uint8Array(await readFile(await download.path())));
  expect(Object.keys(files).sort()).toEqual([
    'ledger/.sulba/lab.json',
    'ledger/.sulba/sulba_fixtures.py',
    'ledger/.sulba/sulba_reporter.mjs',
    'ledger/.sulba/sulba_runner.py',
    'ledger/README.md',
    'ledger/data/entries.csv',
    'ledger/entries.py',
    'ledger/go.mod',
    'ledger/ledger.py',
    'ledger/package-lock.json',
    'ledger/package.json',
    'ledger/pyproject.toml',
    'ledger/sulba.py',
    'ledger/tsconfig.build.json',
    'ledger/tsconfig.json',
    'ledger/uv.lock',
  ]);
  const text = (name: string) => strFromU8(files[`ledger/${name}`] ?? new Uint8Array());
  expect(text('ledger.py')).toContain('return 0');
  expect(text('sulba.py')).toContain('uv run sulba.py next');
  const lab = JSON.parse(text('.sulba/lab.json'));
  expect(lab).toMatchObject({ format: 1, id: 'lab_demo03', start: 0 });
  expect(lab.page).toMatch(/\/demo\/ledgers\/ledger\/$/);
  // The runner fetches the lab's larger files itself, so the zip doesn't carry them.
  expect(lab.data).toEqual(['data/entries.csv']);
  expect(lab.fetch).toEqual([
    {
      file: 't10k-labels-idx1-ubyte.gz',
      url: 'https://fashion-mnist.s3.eu-central-1.amazonaws.com/t10k-labels-idx1-ubyte.gz',
      bytes: 5148,
      sha256: '67da17c76eaffca5446c3361aaab5c3cd6d1c2608764d35dfb1850b086bf8dd5',
    },
  ]);
  // `uv run sulba.py model` fetches the models too, into the cache folder every lab shares.
  expect(
    lab.models.map((model: { title: string; kind: string }) => [model.title, model.kind]),
  ).toEqual([
    ['stories260K', 'chat'],
    ['bge-small-en-v1.5', 'embedding'],
    ['jina-reranker-v1-tiny-en', 'reranking'],
  ]);
  expect(lab.models[0]).toEqual({
    title: 'stories260K',
    kind: 'chat',
    url: 'https://huggingface.co/ggml-org/test-model-stories260K/resolve/479896ec924af6d40fd419ab8f4d1eb2101de00d/stories260K-f32.gguf',
    bytes: 1185376,
    sha256: '270cba1bd5109f42d03350f60406024560464db173c0e387d91f0426d3bd256d',
  });
  expect(lab.stages.map((stage: { slug: string }) => stage.slug)).toEqual([
    'balance',
    'audit',
    'close',
    'statement',
    'receipt',
  ]);
  // A Ship stage's checks come in plain words, for the terminal.
  expect(lab.stages[2].checks).toEqual([
    {
      id: 'tst_demo25',
      title: 'The books balance',
      requires: "The closing balance must be the ledger's balance.",
      failure: 'The closing balance is wrong.',
    },
  ]);
});

test('a link from the runner marks its stage done, and the next opens from there', async ({
  page,
}) => {
  await page.goto(
    linkOf({
      format: 1,
      lab: 'lab_demo03',
      passed: { stg_demo06: null },
      attempts: [
        run('0b7f2f4e-5d3c-4e1a-9a52-7c6f0e2d8b11', 'stg_demo06'),
        pass('5a0c7d2b-9e41-4f6a-8c3d-2b1e0f9a7c64', 'stg_demo06'),
      ],
    }),
  );

  await expect(page.getByRole('status')).toHaveText('Stage 1 done on your machine.');
  await expect(page.getByRole('heading', { level: 2, name: 'Balance' })).toBeVisible();
  await expect(page.getByText('Stage 1 done.', { exact: true })).toBeVisible();
  await expect(stages(page).getByRole('button', { name: /Balance/ })).toContainText('Done');
  // The link's fragment comes out of the address, so a reload doesn't bring it again.
  expect(new URL(page.url()).hash).toBe('');
  await page.getByRole('button', { name: 'Next stage' }).click();
  await expect(
    page.getByRole('heading', { level: 2, name: "The assistant's audit" }),
  ).toBeVisible();
  await page.reload();
  await expect(page.getByRole('status')).toHaveCount(0);
  await expect(stages(page).getByRole('button', { name: /Balance/ })).toContainText('Done');
});

test('a link pasted into the lab’s own page, where only the fragment changes, counts too', async ({
  page,
}) => {
  await page.goto(path);
  await expect(page.getByRole('heading', { level: 2, name: 'Balance' })).toBeVisible();
  await page.goto(
    linkOf({ format: 1, lab: 'lab_demo03', passed: { stg_demo06: null }, attempts: [] }),
  );

  await expect(page.getByRole('status')).toHaveText('Stage 1 done on your machine.');
  await expect(stages(page).getByRole('button', { name: /Balance/ })).toContainText('Done');
  expect(new URL(page.url()).hash).toBe('');
});

test('a Catch review finished on the machine shows each problem, caught or missed', async ({
  page,
}) => {
  await page.goto(
    linkOf({
      format: 1,
      lab: 'lab_demo03',
      passed: { stg_demo06: null, stg_demo07: { caught: [], problems: 1 } },
      attempts: [],
    }),
  );

  await expect(page.getByRole('status')).toHaveText('Stages 1 and 2 done on your machine.');
  await expect(
    page.getByRole('heading', { level: 2, name: "The assistant's audit" }),
  ).toBeVisible();
  await expect(page.getByText('Review finished. You caught 0 of 1 problems.')).toBeVisible();
  await page.getByRole('button', { name: 'See each problem' }).click();
  await expect(
    page.getByRole('heading', { level: 3, name: 'Its largest entry was the smallest' }),
  ).toBeVisible();
  await expect(page.getByText('Missed', { exact: true })).toBeVisible();
});

test('a link that doesn’t hold up marks nothing done', async ({ page }) => {
  await page.goto(
    linkOf({ format: 1, lab: 'lab_demo01', passed: { stg_demo06: null }, attempts: [] }),
  );

  await expect(page.getByRole('heading', { level: 2, name: 'Balance' })).toBeVisible();
  await expect(page.getByRole('status')).toHaveCount(0);
  await expect(stages(page).getByRole('button', { name: /Balance/ })).not.toContainText('Done');
});

test('signed in, the attempts a link carries go to the account, each once', async ({ page }) => {
  const calls = await standIn(page);
  await signedIn(page);
  await page.goto(
    linkOf({
      format: 1,
      lab: 'lab_demo03',
      passed: { stg_demo06: null },
      attempts: [
        run('0b7f2f4e-5d3c-4e1a-9a52-7c6f0e2d8b11', 'stg_demo06'),
        pass('5a0c7d2b-9e41-4f6a-8c3d-2b1e0f9a7c64', 'stg_demo06'),
      ],
    }),
  );

  await expect.poll(() => calls.attempts.length).toBe(2);
  expect(calls.attempts.map(({ id, kind, stage_id }) => ({ id, kind, stage_id }))).toEqual([
    { id: '0b7f2f4e-5d3c-4e1a-9a52-7c6f0e2d8b11', kind: 'run', stage_id: 'stg_demo06' },
    { id: '5a0c7d2b-9e41-4f6a-8c3d-2b1e0f9a7c64', kind: 'pass', stage_id: 'stg_demo06' },
  ]);
  expect(calls.attempts[0]).toMatchObject({ tests_passed: 2, tests_total: 2, day: '2026-10-18' });
});
