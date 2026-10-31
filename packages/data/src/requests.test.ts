import { describe, expect, it, vi } from 'vitest';
import type { Client } from './client.ts';
import {
  actorName,
  answerProblem,
  answerQuestion,
  createRequest,
  requestKey,
  requestNumberOf,
  requestTitleProblem,
} from './requests.ts';

describe('requestKey and requestNumberOf', () => {
  it('write and read a request’s ID, in either case', () => {
    expect(requestKey(3)).toBe('REQ-3');
    expect(requestNumberOf('REQ-3')).toBe(3);
    expect(requestNumberOf('req-12')).toBe(12);
  });

  it('read nothing from what isn’t a request’s ID', () => {
    for (const key of ['REQ-0', 'REQ-03', 'REQ-', 'SPEC-3', 'REQ-3x', 'REQ-1234567890']) {
      expect(requestNumberOf(key), key).toBeNull();
    }
  });
});

describe('requestTitleProblem', () => {
  it('asks for a title of at most 200 characters', () => {
    expect(requestTitleProblem('  ')).toBe('Say what you want built.');
    expect(requestTitleProblem('x'.repeat(201))).toBe('A title has at most 200 characters.');
    expect(requestTitleProblem('A booking app')).toBeNull();
  });
});

describe('answerProblem', () => {
  it('asks for an answer of at most 5,000 characters', () => {
    expect(answerProblem('')).toBe('Write an answer.');
    expect(answerProblem('x'.repeat(5001))).toBe('An answer has at most 5,000 characters.');
    expect(answerProblem('Yes, by card.')).toBeNull();
  });
});

describe('actorName', () => {
  it('names an agent by its person and its name, and someone who left as such', () => {
    expect(actorName('Ben Ortiz', 'Claude Code')).toBe('Ben Ortiz’s agent, Claude Code');
    expect(actorName('Ben Ortiz', null)).toBe('Ben Ortiz');
    expect(actorName(null, 'Claude Code')).toBe('Someone who has left’s agent, Claude Code');
  });
});

describe('createRequest and answerQuestion', () => {
  it('send their words trimmed', async () => {
    const rpc = vi.fn(async () => ({ data: 4, error: null }));
    const client = { rpc } as unknown as Client;

    expect(await createRequest(client, 'w1', '  A booking app ', ' Members book classes. ')).toBe(
      4,
    );
    expect(rpc).toHaveBeenLastCalledWith('create_request', {
      workspace: 'w1',
      title: 'A booking app',
      body: 'Members book classes.',
    });
    await answerQuestion(client, 'q1', '  Yes, by card. ');
    expect(rpc).toHaveBeenLastCalledWith('answer_question', {
      question: 'q1',
      answer: 'Yes, by card.',
    });
  });

  it('give Postgres’s refusal in its words', async () => {
    const rpc = vi.fn(async () => ({
      data: null,
      error: {
        code: '42501',
        message: 'An agent can’t answer a question. A person does that in Sulba',
        details: '',
        hint: '',
      },
    }));
    const client = { rpc } as unknown as Client;

    await expect(answerQuestion(client, 'q1', 'Yes')).rejects.toThrow(
      'An agent can’t answer a question. A person does that in Sulba.',
    );
  });
});
