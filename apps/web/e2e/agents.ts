import type { Page } from '@playwright/test';
import { learner, supabase } from './supabase';
import { answer } from './workspaces';

// Stands in for Supabase's OAuth server as the consent page asks it about an agent's request,
// and for the agent's own page, where the person goes back to (decision record 51).

/** Where Claude Code waits for the person's answer, on their machine. */
export const callback = 'http://127.0.0.1:33418/callback';

export interface Asking {
  readonly id: string;
  readonly agent: string;
  /** Whether the person allowed this agent before, so Supabase sends them straight back. */
  readonly allowedBefore?: boolean;
  /** Whether the request has expired or was already answered. */
  readonly expired?: boolean;
}

/** What the person answered. */
export interface Answers {
  readonly actions: string[];
}

export async function standInConsent(page: Page, asking: Asking): Promise<Answers> {
  const answers: Answers = { actions: [] };
  const path = `${supabase}/auth/v1/oauth/authorizations/${asking.id}`;

  await page.route(path, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    if (asking.expired) {
      return answer(route, 404, {
        code: 404,
        error_code: 'oauth_authorization_not_found',
        msg: 'authorization not found',
      });
    }
    if (asking.allowedBefore) return answer(route, 200, { redirect_url: `${callback}?code=again` });
    return answer(route, 200, {
      authorization_id: asking.id,
      redirect_uri: callback,
      client: {
        id: 'e0000000-0000-4000-8000-000000000005',
        name: asking.agent,
        uri: '',
        logo_uri: '',
      },
      user: { id: learner.id, email: learner.email },
      scope: '',
    });
  });
  await page.route(`${path}/consent`, (route) => {
    if (route.request().method() === 'OPTIONS') return answer(route, 204);
    const { action } = route.request().postDataJSON() as { action: string };
    answers.actions.push(action);
    const back = new URL(callback);
    if (action === 'approve') back.searchParams.set('code', 'code-for-the-agent');
    else back.searchParams.set('error', 'access_denied');
    back.searchParams.set('state', 'agent-state');
    return answer(route, 200, { redirect_url: back.href });
  });
  await page.route(`${callback}**`, (route) =>
    route.fulfill({
      contentType: 'text/html',
      body: '<title>Claude Code</title><p>Signed in.</p>',
    }),
  );
  return answers;
}
