# 10. Reserve all rights to course content

- Status: accepted
- Date: 2026-10-09

## Context

Course content in `courses/` was licensed CC BY-NC-SA 4.0 when the repository was set up, and no lesson has been committed yet. Sulba plans to pay for itself through subscriptions, including licences that companies buy for their staff, and to make the repository private when marketing starts. A Creative Commons licence can't be withdrawn: anything released under it stays free to copy and share on its terms.

## Decision

Course content is all rights reserved, under the notice "© 2026 Sulba" in `courses/LICENSE`. Anyone may read it, fork the repository on GitHub and keep a private copy for their own learning. Republishing it, adapting it, selling it or teaching from it needs written permission. Code stays AGPL-3.0-only, the repository stays public, and course content takes no outside contributions.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| All rights reserved (chosen) | Keeps every option open: content can be opened later, and companies license it from Sulba | Less open; GitHub's terms still let anyone view and fork the public repository |
| CC BY-NC-SA 4.0, the original choice | Open, and stops others selling copies | Can't be withdrawn: every lesson stays free to copy and share non-commercially after the repository goes private. Whether a company training its staff counts as non-commercial is unclear |
| MIT or Apache | The most open; suits a business whose product is something else | Anyone, competitors included, may sell copies |
| Course content in a private repository now | Hides it | A second repository, and CI on private repositories is capped at 2,000 minutes a month on GitHub's free plan |

## Evidence

- freeCodeCamp licenses its software under BSD-3-Clause and keeps its curriculum "copyright © 2014 freeCodeCamp.org" ([README](https://github.com/freeCodeCamp/freeCodeCamp#license)).
- fast.ai's book licenses its code under GPL v3, says its prose "is not licensed for any redistribution", and has contributors assign copyright to the authors ([README](https://github.com/fastai/fastbook)).
- roadmap.sh allows personal use only ([licence](https://github.com/kamranahmedse/developer-roadmap/blob/master/license)).
- CodeCrafters publishes its course stages, starter code and solutions under MIT ([build-your-own-redis](https://github.com/codecrafters-io/build-your-own-redis)), and Hugging Face's course is under Apache 2.0 ([repository](https://github.com/huggingface/course)).
- The Odin Project ([licence](https://github.com/TheOdinProject/curriculum)) and Full Stack Open ([licence](https://github.com/fullstack-hy2020/fullstack-hy2020.github.io)) use CC BY-NC-SA.
- "CC licenses are not revocable" ([Creative Commons FAQ](https://creativecommons.org/faq/)).
- Making a repository public lets other users view and fork it ([GitHub Terms of Service, D.5](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)).
- GitHub Actions is free for public repositories, and private repositories get 2,000 minutes a month on the free plan ([GitHub docs](https://docs.github.com/en/billing/concepts/product-billing/github-actions)).
- Copyright exists once a work is created and fixed; registration is voluntary ([U.S. Copyright Office](https://www.copyright.gov/help/faq/faq-general.html)). It "does not extend to purely AI-generated material", and prompts alone are not enough control; human contributions perceptible in the output, and creative selection, arrangement or modification, are protected ([Copyright and Artificial Intelligence, Part 2](https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf), January 2025).

## Why

Sulba sells the course, so the course has to stay Sulba's. Projects that publish their code but treat their lessons as their own (freeCodeCamp, fast.ai, roadmap.sh) split their licences the same way; open content licences come from non-profits, universities and companies whose product is something else. Reserving rights is also the only choice that can still be changed later. The strongest case against it: an open licence builds goodwill and invites others to improve the course, which matters less while Sulba writes and reviews every lesson itself.

## Consequences

Lessons stay readable in the public repository, and copying them anywhere else is infringement that only a takedown request can stop. The protection covers what people author: lessons drafted with AI are protected for the selection, arrangement and changes made by people, not for text a model produced on its own. Datasets and other material from third parties keep their own licences, noted beside them. The notice names Sulba, the product; the rights are the founder's until a company takes them over. A legal review before launch checks the notice.

## Revisit when

Sulba registers a company, which then takes over the rights, or the business model changes so that open content would serve it better.
