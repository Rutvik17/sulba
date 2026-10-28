# 50. Prove criteria with the test reports a CI run sends, signed by GitHub

- Status: accepted
- Date: 2026-10-28

## Context

A team's tests prove its specs (decision record 46): a test claims an acceptance criterion by putting the criterion's ID in its name (decision record 49), and Sulba has to learn how each claimed test fared. The results come from the team's CI, which for most teams is GitHub Actions, and from whichever test runner each repository uses. Sulba has to know that a report really comes from the repository and commit it names, without a secret to hand out and rotate, and it has to stay on Cloudflare Workers' Free plan and Supabase's free plan. A criterion's wording can change after its tests were written, and a test that passed against the old wording proves nothing about the new one.

## Decision

- **Sending:** each GitHub Actions job that runs tests ends with a step that asks GitHub for the run's OpenID Connect token, made out to `https://sulba.dev`, and posts the job's JUnit XML to `/api/results?workspace=<address>&suite=<name>` with the token. The job needs the `id-token: write` permission, and the step runs unless the run was cancelled, so failing tests are sent too. Settings shows the step and the command that writes the report for pytest, Vitest, Jest, Playwright, Go (through gotestsum) and Maven.
- **Checking:** the Worker checks the token with jose against GitHub's published keys, its issuer, its audience and RS256, and takes the repository, its GitHub ID and its owner's, the branch, the commit, the run, its attempt and the workflow from the token's claims. It passes them and the report to Postgres's `record_report` with Supabase's secret key, a Worker secret, and only calls made with that key can run the function. Without that secret, `/api/results` answers 503. The token isn't kept.
- **Repositories:** an admin adds each repository by its owner/name and the branch whose runs prove criteria, up to 20 in a workspace. The first report pins the repository's GitHub ID, so a different repository given the same name later is refused. A run on any other branch, such as a pull request's, is answered and not kept.
- **Reading:** Postgres reads the report with XMLTABLE. A test case has passed unless it holds `failure` or `error`, or was skipped when it holds `skipped`. A test claims each criterion whose ID its name holds. Sulba keeps each claimed test's name, class, file, outcome and the first 500 characters of its failure, and each report's counts. A request holds at most 10 MB and a report 100,000 tests; a repository sends at most 120 reports an hour; each suite keeps its last 20 runs.
- **Proof:** for each repository and suite, the latest run on its branch counts: the highest run ID, then the highest attempt. A criterion is failing when any of its tests in those runs failed, proven when it has at least one test and every one passed, and otherwise unproven. Views work proof out when they're read, as the person reading, so row-level security applies to them.
- **Rewording:** when a criterion that tests claim is reworded, it's unproven until a member confirms that its tests check the new wording, and the confirmation joins its spec's history.
- **Pages:** Evidence lists the criteria of every spec that isn't abandoned or superseded, failing first, then unproven, then proven, and the runs received. A spec's page shows each criterion's proof and the tests that name it, and the list of specs shows each one's proof.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| A workflow step that sends the report with the run's OpenID Connect token (chosen) | No secret in the team's repository; the token, which GitHub signs, says which repository, branch, commit and run the report is from; any runner that writes JUnit XML works; Sulba registers nothing with GitHub | Each workflow that runs tests needs the step and a permission; it works on GitHub Actions only |
| A GitHub App that fetches each run's artifacts | Nothing to add to a workflow once it's installed | An app to register, its private key kept as a Worker secret, an install in each organisation, and artifacts to fetch and unzip inside the Worker's limits |
| A workspace key kept as a repository secret | Works from any CI | A long-lived secret in every repository, to rotate and to leak, and the repository and commit a report names are whatever its sender says |
| A published Action wrapping the step | One line in a workflow | Sulba's own code in every team's pipeline, to version and keep safe, with the same token underneath |
| Reading the XML in Postgres with XMLTABLE (chosen) | One transaction from report to proof, costing the Worker no CPU | XPath 1.0 only, so each outcome is read with `boolean()` |
| Reading the XML in the Worker | Ordinary JavaScript | sax spent 110 to 174 ms of CPU on a 20,000-test report, against the Free plan's 10 ms a request |
| Proof from the latest run of each suite (chosen) | Matches what the team's CI shows, and easy to trace to one run | A flaky test flips its criterion between runs |
| Proof from each test's history over many runs | Shows flaky tests | A criterion's state would no longer trace to one run |
| On rewording, keeping proof until the next run | Nothing to confirm | The next run would prove the new wording with tests written for the old one |

## Evidence

- [GitHub Docs, OpenID Connect reference](https://docs.github.com/en/actions/reference/security/oidc): the token's claims, among them `repository_id`, `repository_owner_id`, `ref`, `sha`, `run_id`, `run_attempt` and `workflow`, and the `id-token: write` permission; its example token expires five minutes after it's issued.
- [GitHub Docs, OpenID Connect](https://docs.github.com/en/actions/concepts/security/openid-connect): how a job's token, with the claims its run gives it, stands in for a long-lived secret.
- [GitHub Actions' OpenID configuration](https://token.actions.githubusercontent.com/.well-known/openid-configuration): the issuer, the keys' address, the claims supported and RS256, read on 2026-10-28.
- [actions/toolkit, oidc-utils.ts](https://github.com/actions/toolkit/blob/main/packages/core/src/oidc-utils.ts): how a job asks for its token, from `ACTIONS_ID_TOKEN_REQUEST_URL` with the audience encoded and `ACTIONS_ID_TOKEN_REQUEST_TOKEN` as the bearer, and the answer's `value`.
- [GitHub Docs, Variables reference](https://docs.github.com/en/actions/reference/workflows-and-actions/variables): a run's address is `GITHUB_SERVER_URL/GITHUB_REPOSITORY/actions/runs/GITHUB_RUN_ID`.
- [Testmo, Common JUnit XML format](https://github.com/testmoapp/junitxml): the format has no official specification, and a test case has passed unless it holds `skipped`, `failure` or `error`.
- [PostgreSQL 17, XML functions](https://www.postgresql.org/docs/17/functions-xml.html): XMLTABLE, and XPath 1.0 alone.
- [Supabase, API keys](https://supabase.com/docs/guides/api/api-keys): secret keys stand in for the service role's key and are refused when a browser sends them.
- [Cloudflare Workers, Limits](https://developers.cloudflare.com/workers/platform/limits/): 10 ms of CPU a request on the Free plan, and request bodies up to 100 MB.
- [jose](https://github.com/panva/jose): runs on Cloudflare Workers, with `jwtVerify` and `createRemoteJWKSet`.
- Each runner's report: [pytest's `--junit-xml`](https://docs.pytest.org/en/stable/how-to/output.html), [Vitest's reporters](https://github.com/vitest-dev/vitest/blob/main/docs/guide/reporters.md) and [`outputFile`](https://github.com/vitest-dev/vitest/blob/main/docs/config/outputfile.md), [jest-junit](https://github.com/jest-community/jest-junit), [Playwright's JUnit reporter](https://github.com/microsoft/playwright/blob/main/docs/src/test-reporters-js.md), [gotestsum's `--junitfile`](https://github.com/gotestyourself/gotestsum), at v1.13.0 from proxy.golang.org, and [Maven Surefire's `reportsDirectory`](https://maven.apache.org/surefire/maven-surefire-plugin/test-mojo.html).
- Measured on 2026-10-28: `record_report` read a 1.5 MB report of 20,000 tests in 235 ms in a local Postgres 17; sax 1.6.1 spent 110 to 174 ms of CPU in Node.js on a 2.7 MB one. The step ran in bash against local stand-ins for GitHub's token and `/api/results`. Supabase's secret key called `record_report` locally and its publishable key was refused. `packages/data/supabase/tests/evidence.test.sql` runs 41 pgTAP tests, among them that a report from another branch or a different repository with the same name isn't kept, that rewording a claimed criterion leaves it unproven until a member confirms it, and that signed-in people can't send reports.

## Why

The token is the one thing in a run that GitHub vouches for, so taking it as the report's credential means no secret for a team to keep and no way to send results for a repository from outside its own runs. A step is a few lines a team can read before adding, works with every runner that writes JUnit XML, and asks GitHub for nothing but the token. Reading the XML in Postgres keeps the Worker within its Free plan, whatever a report's size, and puts the report, its claims and the proof they make in one transaction. Proof from the latest run on the repository's branch is what the team's own CI shows, so every state on the Evidence page traces to one run, one commit and one test.

The strongest case against it is that a team has to edit each workflow that runs tests, where an installed app would need nothing more. The step is the same few lines in every workflow, and an app can be added later beside it, sending reports to the same function.

## Consequences

- Only GitHub Actions can send reports; another CI needs a token of its own kind to be checked.
- A Supabase secret key has to be made in the dashboard and set as the Worker secret `SUPABASE_SECRET_KEY` before any report is taken.
- A flaky test makes its criterion's proof change from run to run, until the team fixes the test.
- Tests are matched to criteria by name alone, so a test misnamed for another criterion proves the wrong one; the run's log lists each criterion a report names, and those the workspace doesn't have.

## Revisit when

A team asks for a CI other than GitHub Actions, or for proof that looks past the latest run, or reports outgrow what Postgres reads within a request's time.
