import { describe, expect, it, vi } from 'vitest';
import { agentsOf, answer, destinationOf, disconnect, requestOf } from './agents.ts';
import type { Client } from './client.ts';
import { Refusal } from './refusal.ts';

const failure = { name: 'AuthApiError', message: 'Service unavailable', status: 503 };

function client(oauth: Record<string, unknown>): Client {
  return { auth: { oauth } } as unknown as Client;
}

const agent = (id: string, name: string, at: string) => ({
  client: { id, name, uri: '', logo_uri: '' },
  scopes: [],
  granted_at: at,
});

describe('agentsOf', () => {
  it('lists the connected agents newest first, naming one that gave no name', async () => {
    const listGrants = async () => ({
      data: [
        agent('c1', 'Claude Code', '2026-10-21T09:00:00Z'),
        agent('c2', '', '2026-10-27T09:00:00Z'),
      ],
      error: null,
    });
    expect(await agentsOf(client({ listGrants }))).toEqual([
      { clientId: 'c2', name: 'An unnamed agent', connectedAt: '2026-10-27T09:00:00Z' },
      { clientId: 'c1', name: 'Claude Code', connectedAt: '2026-10-21T09:00:00Z' },
    ]);
  });

  it('says when the sign-in service can’t be reached', async () => {
    const listGrants = async () => ({ data: null, error: failure });
    await expect(agentsOf(client({ listGrants }))).rejects.toThrow(
      new Refusal('Sulba couldn’t reach its sign-in service. Try again.'),
    );
  });
});

describe('disconnect', () => {
  it('revokes the agent’s grant', async () => {
    const revokeGrant = vi.fn(async () => ({ data: {}, error: null }));
    await disconnect(client({ revokeGrant }), 'c1');
    expect(revokeGrant).toHaveBeenCalledWith({ clientId: 'c1' });
  });
});

describe('destinationOf', () => {
  it('knows an app on the person’s computer by its loopback address or its own scheme', () => {
    expect(destinationOf('http://127.0.0.1:33418/callback')).toEqual({
      kind: 'computer',
      address: '127.0.0.1:33418',
    });
    expect(destinationOf('http://localhost:8080/callback')).toEqual({
      kind: 'computer',
      address: 'localhost:8080',
    });
    expect(destinationOf('http://[::1]:5000/')).toEqual({
      kind: 'computer',
      address: '[::1]:5000',
    });
    expect(destinationOf('cursor://anysphere.cursor-mcp/oauth/callback')).toEqual({
      kind: 'app',
      scheme: 'cursor',
    });
  });

  it('knows a website by its host, over HTTPS only', () => {
    expect(destinationOf('https://claude.ai/api/mcp/auth_callback')).toEqual({
      kind: 'website',
      host: 'claude.ai',
    });
  });

  it('refuses plain HTTP to another computer, scripts, credentials and addresses it can’t read', () => {
    for (const address of [
      'http://agent.example/callback',
      'http://localhost.example/callback',
      'http://127.0.0.1.nip.io/callback',
      'https://user:secret@agent.example/callback',
      'javascript:alert(1)',
      'data:text/html,hello',
      'file:///etc/passwd',
      'not an address',
    ]) {
      expect(destinationOf(address), address).toEqual({ kind: 'refused', address });
    }
  });
});

describe('requestOf', () => {
  it('gives the agent asking and where answering sends the person back to', async () => {
    const getAuthorizationDetails = async () => ({
      data: {
        authorization_id: 'r1',
        redirect_uri: 'http://127.0.0.1:33418/callback',
        client: { id: 'c1', name: 'Claude Code', uri: '', logo_uri: '' },
        user: { id: 'u1', email: 'ada@example.com' },
        scope: '',
      },
      error: null,
    });
    expect(await requestOf(client({ getAuthorizationDetails }), 'r1')).toEqual({
      request: {
        id: 'r1',
        agent: 'Claude Code',
        destination: { kind: 'computer', address: '127.0.0.1:33418' },
      },
    });
  });

  it('sends back an agent the person allowed before', async () => {
    const getAuthorizationDetails = async () => ({
      data: { redirect_url: 'http://127.0.0.1:33418/callback?code=x' },
      error: null,
    });
    expect(await requestOf(client({ getAuthorizationDetails }), 'r1')).toEqual({
      redirectTo: 'http://127.0.0.1:33418/callback?code=x',
    });
  });

  it('says a request that expired or was answered can’t be answered', async () => {
    const getAuthorizationDetails = async () => ({ data: null, error: failure });
    await expect(requestOf(client({ getAuthorizationDetails }), 'r1')).rejects.toThrow(
      'This request has expired or was already answered. Connect again from your agent.',
    );
  });
});

describe('answer', () => {
  it('allows or denies without leaving the page, and gives the agent’s address', async () => {
    const approveAuthorization = vi.fn(async () => ({
      data: { redirect_url: 'http://127.0.0.1:33418/callback?code=x' },
      error: null,
    }));
    const denyAuthorization = vi.fn(async () => ({
      data: { redirect_url: 'http://127.0.0.1:33418/callback?error=access_denied' },
      error: null,
    }));
    const oauth = client({ approveAuthorization, denyAuthorization });

    expect(await answer(oauth, 'r1', true)).toBe('http://127.0.0.1:33418/callback?code=x');
    expect(approveAuthorization).toHaveBeenCalledWith('r1', { skipBrowserRedirect: true });
    expect(await answer(oauth, 'r1', false)).toBe(
      'http://127.0.0.1:33418/callback?error=access_denied',
    );
    expect(denyAuthorization).toHaveBeenCalledWith('r1', { skipBrowserRedirect: true });
  });
});
