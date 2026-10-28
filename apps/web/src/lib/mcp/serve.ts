/*
  Sulba's MCP server, at /mcp on the site's Worker (decision record 51). A coding agent signs in
  through Supabase's OAuth 2.1 server, which the protected resource metadata names, and sends the
  access token it gets with each request. The token is checked against the project's published
  keys, and each tool then calls Supabase with it, so row-level security sees the agent's person
  and Postgres sees that an agent is acting. The server keeps no session between requests.
*/
import {
  type AuthInfo,
  createMcpHandler,
  OAuthError,
  OAuthErrorCode,
  requireBearerAuth,
} from '@modelcontextprotocol/server';
import { connectWith } from '@sulba/data/client';
import { createRemoteJWKSet, type JWTVerifyGetKey, jwtVerify } from 'jose';
import { createServer } from './tools';

export interface Settings {
  readonly supabaseUrl: string;
  readonly publishableKey: string;
  /** The project's signing keys; by default its published ones. */
  readonly keys?: JWTVerifyGetKey;
  /** How the tools reach Supabase; by default the Worker's fetch. */
  readonly fetch?: typeof fetch;
}

/** The path of the server's protected resource metadata (RFC 9728), for a server at /mcp. */
export const metadataPath = '/.well-known/oauth-protected-resource/mcp';

const published = new Map<string, JWTVerifyGetKey>();

/** The project's published signing keys, which jose fetches once and keeps. */
function keysOf(supabaseUrl: string): JWTVerifyGetKey {
  let keys = published.get(supabaseUrl);
  if (!keys) {
    keys = createRemoteJWKSet(new URL(`${supabaseUrl}/auth/v1/.well-known/jwks.json`));
    published.set(supabaseUrl, keys);
  }
  return keys;
}

/**
 * Checks an access token: Supabase's, for its project's API, and issued to an OAuth client
 * through the authorization the person gave on the consent page. A browser session's token
 * carries no client, so it isn't taken here.
 */
export async function verifyAgent(token: string, settings: Settings): Promise<AuthInfo> {
  let payload: Awaited<ReturnType<typeof jwtVerify>>['payload'];
  try {
    ({ payload } = await jwtVerify(token, settings.keys ?? keysOf(settings.supabaseUrl), {
      issuer: `${settings.supabaseUrl}/auth/v1`,
      audience: 'authenticated',
      algorithms: ['ES256', 'RS256'],
    }));
  } catch {
    throw new OAuthError(OAuthErrorCode.InvalidToken, 'The token isn’t valid, or it has expired');
  }
  const clientId = payload.client_id;
  if (typeof payload.exp !== 'number') {
    throw new OAuthError(OAuthErrorCode.InvalidToken, 'The token has no expiry');
  }
  if (typeof clientId !== 'string' || typeof payload.sub !== 'string') {
    throw new OAuthError(
      OAuthErrorCode.InvalidToken,
      'Connect your agent to Sulba through its MCP settings, which sign it in for you',
    );
  }
  // Disconnecting an agent ends its session at once, while its token lasts until it expires, so
  // Supabase's Auth server is asked whether the session is still there.
  const session = await (settings.fetch ?? fetch)(`${settings.supabaseUrl}/auth/v1/user`, {
    headers: { apikey: settings.publishableKey, Authorization: `Bearer ${token}` },
  });
  await session.body?.cancel();
  if (session.status === 401 || session.status === 403) {
    throw new OAuthError(
      OAuthErrorCode.InvalidToken,
      'This agent was disconnected. Sign it in again from its MCP settings',
    );
  }
  if (!session.ok) {
    throw new OAuthError(OAuthErrorCode.ServerError, 'Sulba couldn’t reach its sign-in service');
  }
  return {
    token,
    clientId,
    scopes: typeof payload.scope === 'string' ? payload.scope.split(' ').filter(Boolean) : [],
    expiresAt: payload.exp,
    extra: { personId: payload.sub },
  };
}

/** Where agents sign in for the server at this origin, as RFC 9728 describes it. */
export function metadataOf(origin: string, settings: Settings): Response {
  return Response.json(
    {
      resource: `${origin}/mcp`,
      authorization_servers: [`${settings.supabaseUrl}/auth/v1`],
      bearer_methods_supported: ['header'],
      resource_name: 'Sulba',
    },
    { headers: { 'Cache-Control': 'public, max-age=3600' } },
  );
}

const forbidden = () =>
  Response.json(
    {
      jsonrpc: '2.0',
      error: { code: -32000, message: 'Requests from other sites aren’t taken' },
      id: null,
    },
    { status: 403 },
  );

/** Answers one request to /mcp. */
export async function serveMcp(request: Request, settings: Settings): Promise<Response> {
  const url = new URL(request.url);
  // A browser sends its page's origin; only Sulba's own pages may call the server from one, as
  // the MCP transport asks, so another site can't reach it through a person's browser.
  const origin = request.headers.get('Origin');
  if (origin !== null && origin !== url.origin) return forbidden();

  const gate = requireBearerAuth({
    verifier: { verifyAccessToken: (token) => verifyAgent(token, settings) },
    resourceMetadataUrl: `${url.origin}${metadataPath}`,
  });
  const auth = await gate(request);
  if (auth instanceof Response) return auth;

  const client = connectWith(settings.supabaseUrl, settings.publishableKey, auth.token, {
    fetch: settings.fetch,
  });
  const personId = String(auth.extra?.personId);
  const handler = createMcpHandler(() => createServer({ client, personId, origin: url.origin }), {
    maxRequestBodySize: 1024 * 1024,
  });
  return handler.fetch(request, { authInfo: auth });
}
