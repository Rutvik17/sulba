# 1. Render each route the way its content needs

- Status: accepted
- Date: 2026-10-08

## Context

Sulba has five kinds of page, with different needs:

- hundreds of lesson and problem pages that should load at once and rank in search
- personal pages: the dashboard, review and profile
- discussion threads, which should also rank in search (planned)
- API routes that hold secrets: the contact form now, grading later
- the workspace, which runs the learner's code

## Decision

- Pages that are the same for everyone are built ahead of time.
- Personal pages are built ahead of time too, then filled from the learner's own data, which local-first sync keeps on their device.
- Only the API and the pages search engines must index (discussion threads) run on the server.
- The workspace runs the learner's code in the browser.

## Options

| Option | Serves well | Falls short on |
| --- | --- | --- |
| Static only (the previous site's model) | Lesson pages | Personal pages show only after JavaScript loads; discussion threads are invisible to search; secrets need a separate API anyway |
| One client-side app with an API | Smooth navigation | The first view of every lesson waits for JavaScript; Google's guidance warns that client rendering grows JavaScript and hurts responsiveness |
| Server-render everything | Personal and indexed pages | Pays server time for pages that never change, and is slower than a cached file |
| Each route its own way (chosen) | All five | Two rendering modes to understand |

## Evidence

- Google's guidance, updated January 2026: "we encourage developers to consider server-side rendering or static rendering over a full rehydration approach", and "It's fine to mostly ship HTML with minimal JavaScript" ([Rendering on the Web](https://web.dev/articles/rendering-on-the-web)).
- What leading learning platforms served on 8 October 2026, read from their own pages: LeetCode, Codecademy, Brilliant, DataCamp, Educative and CodeCrafters serve Next.js, which renders on the server and builds pages ahead of time. Exercism and The Odin Project render on the server with Rails. freeCodeCamp builds its learning pages ahead of time with Gatsby and runs a separate Fastify API ([freeCodeCamp's repository](https://github.com/freeCodeCamp/freeCodeCamp)). Boot.dev serves Nuxt, and roadmap.sh serves React Router.

## Why

A static-only rule suits a site without accounts. Accounts, and the discussions planned after them, need a server for the reasons above. That is not because static pages are unprofessional: freeCodeCamp's learning pages are still static.

Personal pages don't render on the server because the learner's progress is already on their device. The dashboard can draw it at once, even offline, with no server request. That leaves server requests to the API and discussions, which keeps Sulba on free plans into the tens of thousands of daily learners. It also means a server outage or a used-up quota can't blank anyone's dashboard. freeCodeCamp's static pages with a separate API work the same way.

## Consequences

Every route has to be built in one of the modes above, and contributors need to know which mode a page uses.

## Revisit when

A page type appears that fits none of these modes.
