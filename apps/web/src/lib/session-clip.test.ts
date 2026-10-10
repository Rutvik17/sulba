import { DatabaseSync } from 'node:sqlite';
import { describe, expect, test } from 'vitest';
import { at, checkLines, checks, END, edits, frameAt, injection, select } from './session-clip';

// The clip's claims, checked against a real SQLite database. Python's sqlite3 runs the same engine
// and gives the same results: checked with Python 3.12 and SQLite 3.42 on 9 October 2026.
function orders() {
  const db = new DatabaseSync(':memory:');
  db.exec('CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT, total REAL)');
  const insert = db.prepare('INSERT INTO orders (customer, total) VALUES (?, ?)');
  for (const [customer, total] of [
    ['ada', 19],
    ['ada', 42.5],
    ["o'brien", 12],
    ['grace', 30],
  ] as const) {
    insert.run(customer, total);
  }
  return {
    count: 4,
    // The assistant's draft: the name pasted into the query.
    draft: (name: string) => db.prepare(`${select}'${name}'`).all(),
    // The fix: the name sent as a parameter.
    fixed: (name: string) => db.prepare(`${select}?`).all(name),
  };
}

describe('what the clip claims is what SQLite does', () => {
  test("the assistant's tests pass before and after the fix", () => {
    const { draft, fixed } = orders();

    expect(draft('ada')).toHaveLength(2);
    expect(fixed('ada')).toHaveLength(2);
    expect(draft('zoe')).toEqual([]);
    expect(fixed('zoe')).toEqual([]);
  });

  test('the draft treats a name as SQL, and the fix treats it as text', () => {
    const { count, draft, fixed } = orders();

    expect(draft(injection)).toHaveLength(count);
    expect(() => draft("o'brien")).toThrow('near "brien": syntax error');
    expect(fixed(injection)).toEqual([]);
    expect(fixed("o'brien")).toHaveLength(1);
  });

  test('both versions return only ids and totals', () => {
    const { draft, fixed } = orders();

    expect(Object.keys(draft('ada')[0] ?? {})).toEqual(['id', 'total']);
    expect(Object.keys(fixed('ada')[0] ?? {})).toEqual(['id', 'total']);
  });

  test('so one of the two checks fails on the draft and both pass on the fix', () => {
    expect(checks).toHaveLength(2);
    expect(checkLines.some).toBe('1 of 2 pass');
    expect(checkLines.all).toBe('2 of 2 pass');
  });

  test('the edits turn the draft into the fix', () => {
    const before = `f"${select}${edits.b.remove}"`;
    const after = `"${select}${edits.b.insert}"`;

    expect(
      before.replace(edits.a.remove, edits.a.insert).replace(edits.b.remove, edits.b.insert),
    ).toBe(after);
    expect(edits.c.insert).toBe(', (name,)');
  });
});

describe('the session plays once, in order', () => {
  test('nothing has run at the start', () => {
    const frame = frameAt(0);

    expect(frame.tests).toEqual(['idle', 'idle']);
    expect(frame.checks).toBe('idle');
    expect(frame.edits.a.removed).toBe(false);
  });

  test("the first run passes the assistant's tests and one of the two checks", () => {
    const frame = frameAt(at.checked1 + 200);

    expect(frame.tests).toEqual(['pass', 'pass']);
    expect(frame.checks).toBe('some');
    expect(frame.hiddenNote).toBe(true);
  });

  test('the f goes, the quoted name is selected and replaced, and the name becomes a parameter', () => {
    expect(frameAt(at.deleteA).edits.a.removed).toBe(true);
    expect(frameAt(5200).edits.b.selected).toBeGreaterThan(0);
    expect(frameAt(at.typeB - 50).edits.b.selected).toBe(edits.b.remove.length);
    expect(frameAt(at.typeB).edits.b).toMatchObject({ removed: true, selected: 0, typed: 1 });
    expect(frameAt(at.press2).edits.c.typed).toBe(edits.c.insert.length);
  });

  test('the second run passes both checks and the review is done', () => {
    const frame = frameAt(at.done + 100);

    expect(frame.tests).toEqual(['pass', 'pass']);
    expect(frame.checks).toBe('all');
    expect(frame.hiddenNote).toBe(false);
    expect(frame.done).toBe(true);
  });

  test('it rests on the last frame: every edit made and both checks passing', () => {
    const frame = frameAt(END);

    expect(frame).toMatchObject({ checks: 'all', done: true, away: false });
    expect(frame.edits.a.removed && frame.edits.b.removed).toBe(true);
    expect(frame.edits.c.typed).toBe(edits.c.insert.length);
    expect(frameAt(END + 60_000)).toEqual(frame);
  });
});

describe('the pointer behaves like a real one', () => {
  test('it hides while typing and comes back where the typing ended', () => {
    expect(frameAt(at.deleteA + 100).away).toBe(true);
    expect(frameAt(at.typeB + 100).away).toBe(true);
    expect(frameAt(at.typeC + 100).away).toBe(true);
    expect(frameAt(4500)).toMatchObject({ away: false, pointer: { from: 'a-end', to: 'b' } });
    expect(frameAt(6000)).toMatchObject({ away: false, pointer: { from: 'b-end', to: 'c' } });
    expect(frameAt(7800)).toMatchObject({ away: false, pointer: { from: 'c-end', to: 'run' } });
  });

  test('it drags across the quoted name with the button held down', () => {
    expect(frameAt(5200)).toMatchObject({ press: true, pointer: { from: 'b', to: 'b-sel' } });
  });

  test('it presses Run tests twice', () => {
    expect(frameAt(at.press1 + 60)).toMatchObject({ down: true, press: true });
    expect(frameAt(at.press2 + 60)).toMatchObject({ down: true, press: true });
    expect(frameAt(at.press1 + 200).down).toBe(false);
  });
});
