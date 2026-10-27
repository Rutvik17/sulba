# 46. Make Sulba where a team specifies its software, agents build it and its tests prove it

- Status: accepted
- Date: 2026-10-27

## Context

Records 1 to 45 build a course site, and the AI Engineering course's Beginner and Intermediate levels are done. The founder wants Sulba to be a product that engineering teams pay for, in the software and AI infrastructure space, with the course kept as the Academy under `/academy/`. Costs stay at $0 until customers pay, one founder sells it, and coding agents build it.

Coding agents now write much of a team's work, and what they are asked to build is scattered across trackers, documents, chats and people's heads. An agent gets part of the context and drifts from what was meant, a reviewer can't tell whether a pull request meets the requirement behind it, and documents go stale as the code changes.

## Decision

- Sulba is where a team's software is defined, and the record of what was built. It holds:
  - **Specs:** what to build and why, each with acceptance criteria written so that a test can check them.
  - **Architecture:** the system's diagrams, interfaces and data model.
  - **Decisions:** each choice, with the options weighed and the sources read.
  - **Standards:** the team's rules for people and agents.
  - **Tasks:** work sized for an agent, each with the specs, architecture, files, standards and definition of done it needs.
  - **Evidence:** the tests and CI results that check each acceptance criterion, so that each spec shows as proven, unproven or failing.
  - **Map:** the links between all of them, and who changed what, person or agent.
- Coding agents take tasks and report back through an MCP server, and a GitHub app links pull requests to tasks and their CI results to evidence.
- It starts beside the team's tracker, Jira, Linear or GitHub Issues, kept in step with it, rather than replacing it.
- The names are Sulba's own. "8090 SOFTWARE FACTORY" is a registered mark, so Sulba never calls itself a software factory.
- The Academy stays at `/academy/`. Where documents are kept, the app's framework and its hosting each get a record of their own.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| The Academy as the product | Built, tested and live | Its buyers are individual learners, not engineering teams |
| Proof of AI savings: replay a company's traffic on cheaper setups and prove the answers hold | Uses Sulba's evals work, and runs on the customer's keys | AI gateways already route and report on that traffic, and security companies are buying them: Palo Alto Networks closed its purchase of Portkey on May 29, 2026 |
| A fast lane: move a company's AI features to open models on Cerebras, with that proof | Faster and cheaper answers | Rests on one supplier, whose speed anyone can rent at the same price |
| Code review that comments only on bugs it proves with a failing test | A market teams already pay for | GitHub, Cursor and Anthropic each ship a reviewer of their own |
| An app builder like Lovable | A proven market: Lovable is valued at $13.3 billion after a $400 million round, with a $600 million run rate | Every prompt costs model tokens, so free users can't cost $0 |
| Specs, tasks and evidence for software agents build (chosen) | Agents already create half of the work in Linear, and 8090 sells its version at $200 per user a month; spec-driven tools work one repository at a time | Teams rarely change trackers, and 8090, Linear, Atlassian, GitHub and AWS are all moving into it |

## Evidence

- [Pulse 2.0, Linear Completes $99 Million Tender At $2.5 Billion Valuation](https://pulse2.com/linear-completes-99-million-tender-at-2-5-billion-valuation-as-arr-tops-100-million-and-net-retention-hits-177/) (August 28, 2026): Linear passed $100 million in annual recurring revenue with more than 40,000 paying customers; agents are installed in 95% of its paid workspaces, and the share of work agents create rose from 3% a year earlier to 50%.
- [Ry Walker, 8090 Software Factory](https://rywalker.com/research/8090-software-factory) (updated September 15, 2026): its modules hold requirements, technical blueprints, work orders, tests and feedback, which coding agents read through MCP; self-serve costs $200 per user a month plus tokens, and Enterprise starts at $1 million a year.
- [8090, Changelog](https://www.8090.ai/docs/resources/changelog): work orders show the status of their linked GitHub and GitLab pull requests and list the agent chats that worked on them.
- [TrademarkRegistration.app, 8090 SOFTWARE FACTORY](https://trademarkregistration.app/Trademark/Details/99287889): serial number 99287889, registration 8416691, registered and in good standing.
- [U.S. Copyright Office, Circular 33: Works Not Protected by Copyright](https://www.copyright.gov/circs/circ33.pdf): words and short phrases, such as names, titles and slogans, can't be copyrighted, though trademark law may protect them.
- [Augment Code, 6 Best Spec-Driven Development Tools for AI Coding in 2026](https://www.augmentcode.com/tools/best-spec-driven-development-tools) (updated June 18, 2026): compares Amazon Kiro, GitHub Spec Kit, OpenSpec, BMAD-METHOD and Cursor's rules on a spec's lifecycle, how far it coordinates agents, and whether agents read a spec once or work against it.
- [Intelligence Community News, Palo Alto acquires Portkey](https://intelligencecommunitynews.com/palo-alto-acquires-portkey/) (June 8, 2026): Palo Alto Networks closed the acquisition on May 29, 2026, to make the AI gateway a control plane for enterprise agents.
- [VC Value Add, Lovable Valuation 2026](https://valueaddvc.com/blog/lovable-valuation-2026-13-2b-and-500m-arr-how-vibe-coding-actually-makes-money) (updated October 21, 2026): $13.3 billion after a $400 million Series C, with a $600 million run rate.

## Why

Engineering teams adopting coding agents have money and a problem that grows as agents do more of the work, and the incumbents' trackers hold tickets, not the specs, architecture and proof behind them. Sulba's difference is evidence: each acceptance criterion is tied to the tests that check it, the way every number on Sulba's own pages comes from code that runs in CI. It is also how this repository is built, with written standards in CLAUDE.md, a decision record for each choice and CI that must pass, so Sulba can build itself in Sulba. It is software that runs on the free plans already in use, so it costs nothing until customers pay.

The strongest case against it is that it's crowded with better-funded players, and that a team's tracker is the hardest tool to replace. Starting beside the tracker, and competing on evidence and price rather than on tracking, is the answer to both.

## Consequences

- A second app to build and keep: the product, beside the Academy.
- The Privacy Policy and the Terms are rewritten before the first customer's data arrives, and enterprise buyers will ask for a security review.
- The Academy's courses pause after Intermediate.

## Revisit when

Five teams that use coding agents have tried it, and none of them is still using it a month later.
