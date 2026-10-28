import type { User } from '@supabase/supabase-js';
import { describe, expect, it, vi } from 'vitest';
import { closeAccount, learnerOf, OnlyOwner } from './account.ts';
import type { Client } from './client.ts';

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

describe('closeAccount', () => {
  const client = (error: { code: string; message: string } | null) => {
    const signOut = vi.fn(async () => ({ error: null }));
    return {
      signOut,
      client: { rpc: async () => ({ error }), auth: { signOut } } as unknown as Client,
    };
  };

  it('signs this browser out once the account is closed', async () => {
    const { client: closing, signOut } = client(null);
    await closeAccount(closing);
    expect(signOut).toHaveBeenCalledWith({ scope: 'local' });
  });

  it('says when the account is the only owner of a workspace others are in, and stays signed in', async () => {
    const { client: refused, signOut } = client({
      code: '23514',
      message: 'Make someone else an owner of each workspace you own first',
    });
    await expect(closeAccount(refused)).rejects.toBeInstanceOf(OnlyOwner);
    expect(signOut).not.toHaveBeenCalled();
  });
});
