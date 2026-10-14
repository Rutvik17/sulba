import type { User } from '@supabase/supabase-js';
import { describe, expect, it } from 'vitest';
import { learnerOf } from './account.ts';

function user(provider: unknown, email?: string): User {
  return {
    id: 'a0000000-0000-4000-8000-000000000001',
    aud: 'authenticated',
    app_metadata: { provider },
    user_metadata: {},
    created_at: '2026-10-14T10:00:00Z',
    ...(email === undefined ? {} : { email }),
  } as User;
}

describe('learnerOf', () => {
  it('names the provider the learner signed in with', () => {
    expect(learnerOf(user('github', 'a@example.com'))).toEqual({
      email: 'a@example.com',
      provider: 'github',
    });
    expect(learnerOf(user('google', 'a@example.com')).provider).toBe('google');
  });

  it('names no provider the site doesn’t offer, and no email it wasn’t given', () => {
    expect(learnerOf(user('email'))).toEqual({ email: null, provider: null });
  });
});
