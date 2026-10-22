// A reporter for Node's test runner, which the runner gives it for a session's TypeScript tests
// (decision record 39). It writes a line of JSON for each test's result, for each piece of output,
// and for a test file that doesn't load, with paths from the session's folder, where the run
// starts. Node's own reporters write for people, and their output may change.
import { isAbsolute, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { inspect } from 'node:util';

// The assertions whose failure compares the value a test got with the one it expected.
const comparisons = new Set([
  'deepEqual',
  'deepStrictEqual',
  'equal',
  'partialDeepStrictEqual',
  'strictEqual',
]);

// A frame of a stack, or the line Node prints above an error that stopped a file loading.
const frame = /(file:\/\/\/[^\s()]+?):(\d+)(?::\d+)?\)?$/;

/** The path of a file under the session's folder, with forward slashes, or null for another. */
function inSession(path) {
  const found = relative(process.cwd(), path);
  if (found === '' || found.startsWith('..') || isAbsolute(found)) return null;
  return found.split(sep).join('/');
}

/** The deepest place in the session's own files, outside its tests, that the lines pass. */
function location(lines) {
  for (const line of lines) {
    const match = frame.exec(line.trim());
    if (match === null) continue;
    const file = inSession(fileURLToPath(match[1]));
    if (file !== null && !file.startsWith('tests/') && !file.startsWith('node_modules/')) {
      return { file, line: Number(match[2]) };
    }
  }
  return null;
}

function shown(value) {
  return inspect(value, { depth: 6, breakLength: Number.POSITIVE_INFINITY });
}

function result(data) {
  const error = data.details.error;
  const entry = {
    kind: 'test',
    name: data.name,
    file: inSession(data.file ?? '') ?? data.file,
    status: 'pass',
    message: null,
    expected: null,
    actual: null,
    location: null,
    durationMs: Math.round(data.details.duration_ms ?? 0),
  };
  if (error === undefined) return entry;
  // The test runner wraps what a test threw; a test that ran out of time has nothing inside.
  const cause = error.cause instanceof Error ? error.cause : error;
  const failed = cause.code === 'ERR_ASSERTION';
  entry.status = failed ? 'fail' : 'error';
  const message = String(cause.message ?? '').trim();
  if (failed) {
    entry.message = message.split('\n')[0] || 'The check failed.';
    if (comparisons.has(cause.operator)) {
      entry.expected = shown(cause.expected);
      entry.actual = shown(cause.actual);
    }
  } else {
    entry.message = message ? `${cause.name ?? 'Error'}: ${message}` : (cause.name ?? 'Error');
  }
  entry.location = location(String(cause.stack ?? '').split('\n'));
  return entry;
}

/**
 * What stopped a test file loading, from what Node printed: the place, then the error's name and
 * message under the line of code, as in `Error: message`.
 */
function problem(printed) {
  const lines = printed.split('\n');
  const said = lines.map((line) => /^([A-Za-z_$][\w$]*)(?: \[\w+\])?: (.*)$/.exec(line));
  const found = said.find((match) => match !== null);
  return {
    kind: 'problem',
    problem: {
      kind: found?.[1] ?? 'Error',
      message: found?.[2] ?? 'The test file stopped as it loaded.',
      location: location(lines),
    },
  };
}

export default async function* reporter(source) {
  // What each test file printed to stderr, which holds the error when it doesn't load.
  const printed = new Map();
  for await (const event of source) {
    const data = event.data;
    if (event.type === 'test:stdout' || event.type === 'test:stderr') {
      if (event.type === 'test:stderr') {
        printed.set(data.file, (printed.get(data.file) ?? '') + data.message);
      }
      yield `${JSON.stringify({ kind: 'output', text: data.message })}\n`;
    } else if (event.type === 'test:pass' || event.type === 'test:fail') {
      if (data.details.type === 'suite') continue;
      const file = inSession(data.file ?? '');
      // A file that stops as it loads is reported as a test named after the file.
      if (
        event.type === 'test:fail' &&
        data.nesting === 0 &&
        data.name.split(sep).join('/') === file
      ) {
        yield `${JSON.stringify(problem(printed.get(data.name) ?? printed.get(file) ?? ''))}\n`;
        continue;
      }
      yield `${JSON.stringify(result(data))}\n`;
    }
  }
}
