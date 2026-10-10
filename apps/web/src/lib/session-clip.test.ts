import { DatabaseSync } from 'node:sqlite';
import { describe, expect, test } from 'vitest';
import { at, edits, failure, finished, frameAt, injection, LOOP, select } from './session-clip';

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
  test('the draft returns every order for the injected name, and the fix returns none', () => {
    const { count, draft, fixed } = orders();

    expect(draft(injection)).toHaveLength(count);
    expect(fixed(injection)).toEqual([]);
    expect(failure.message).toBe('Returned every order in the table, expected none');
  });

  test('the draft breaks on a name with an apostrophe, and the fix finds the order', () => {
    const { draft, fixed } = orders();

    expect(() => draft("o'brien")).toThrow('near "brien": syntax error');
    expect(fixed("o'brien")).toHaveLength(1);
  });

  test('both versions find a customer and return nothing for an unknown one', () => {
    const { draft, fixed } = orders();

    expect(draft('ada')).toHaveLength(2);
    expect(fixed('ada')).toHaveLength(2);
    expect(draft('zoe')).toEqual([]);
    expect(fixed('zoe')).toEqual([]);
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

describe('the session plays in order', () => {
  test('nothing has run at the start', () => {
    const frame = frameAt(0);

    expect(frame.tests).toEqual(['idle', 'idle', 'idle', 'idle']);
    expect(frame.summary).toBe('idle');
    expect(frame.edits.a.removed).toBe(false);
  });

  test('the first run fails the attack and apostrophe tests', () => {
    const frame = frameAt(at.failed + 100);

    expect(frame.tests).toEqual(['pass', 'fail', 'fail', 'pass']);
    expect(frame.summary).toBe('fail');
    expect(frame.failNote).toBe(true);
  });

  test('the f goes, the quoted name is selected and replaced, and the name becomes a parameter', () => {
    expect(frameAt(at.deleteA).edits.a.removed).toBe(true);
    expect(frameAt(5200).edits.b.selected).toBeGreaterThan(0);
    expect(frameAt(at.typeB - 50).edits.b.selected).toBe(edits.b.remove.length);
    expect(frameAt(at.typeB).edits.b).toMatchObject({ removed: true, selected: 0, typed: 1 });
    expect(frameAt(at.press2).edits.c.typed).toBe(edits.c.insert.length);
  });

  test('the second run passes every test and the session is done', () => {
    const frame = frameAt(at.done + 100);

    expect(frame.tests).toEqual(['pass', 'pass', 'pass', 'pass']);
    expect(frame.summary).toBe('pass');
    expect(frame.failNote).toBe(false);
    expect(frame.done).toBe(true);
  });

  test('the finished frame shown for reduced motion has every edit made and every test passed', () => {
    const frame = frameAt(finished);

    expect(frame).toMatchObject({ summary: 'pass', done: true, hidden: false });
    expect(frame.edits.a.removed && frame.edits.b.removed).toBe(true);
    expect(frame.edits.c.typed).toBe(edits.c.insert.length);
  });

  test('the loop resets behind a fade and starts again from nothing', () => {
    expect(frameAt(at.fadeOut).hidden).toBe(true);
    expect(frameAt(at.reset)).toMatchObject({ summary: 'idle', done: false, hidden: true });
    expect(frameAt(at.reset).edits.b.removed).toBe(false);
    expect(frameAt(LOOP - 1)).toMatchObject({ summary: 'idle', hidden: false });
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
