# Architecture decisions

Each record covers one decision: the context, the options compared, the evidence, the choice, what it costs and when to revisit it. An accepted record is not rewritten. When a decision changes, a new record supersedes the old one, or amends the part that changed, and the old one's status links to it.

| Record | Status |
| --- | --- |
| [1. Render each route the way its content needs](0001-render-each-route-the-way-its-content-needs.md) | Accepted |
| [2. Use Astro 7, with React for the interactive parts](0002-use-astro-with-react-for-interactive-parts.md) | Accepted |
| [3. Host on Cloudflare Workers](0003-host-on-cloudflare-workers.md) | Accepted |
| [4. Keep learner data and sign-in in Supabase](0004-keep-learner-data-and-sign-in-in-supabase.md) | Accepted |
| [5. Run learners' code in the browser and on their machine](0005-run-learner-code-in-the-browser-and-on-their-machine.md) | Superseded by 17 |
| [6. Use CodeMirror 6 with language servers](0006-use-codemirror-with-language-servers.md) | Superseded by 14 |
| [7. Keep course content as validated files with permanent ids](0007-keep-course-content-as-validated-files.md) | Accepted |
| [8. Monitor with free services, each with one job](0008-monitor-with-free-services.md) | Accepted |
| [9. Keep branch previews behind Cloudflare Access](0009-keep-previews-behind-cloudflare-access.md) | Accepted |
| [10. Reserve all rights to course content](0010-reserve-all-rights-to-course-content.md) | Accepted |
| [11. Build the interface on tokens, CSS and React Aria Components](0011-build-the-interface-on-tokens-css-and-react-aria.md) | Accepted |
| [12. Send contact messages through Resend, after a Turnstile check](0012-send-contact-messages-through-resend-after-turnstile.md) | Accepted |
| [13. Leave the EEA, the UK and Switzerland out of visit counts](0013-leave-the-eea-uk-and-switzerland-out-of-visit-counts.md) | Accepted |
| [14. Use CodeMirror 6, with each language's own browser build](0014-use-codemirror-with-each-languages-own-browser-build.md) | Accepted |
| [15. Render formulas as MathML at build time, in Noto Sans Math](0015-render-formulas-as-mathml-in-noto-sans-math.md) | Accepted |
| [16. Draw charts in SVG, from the data a stage's chart.py returns](0016-draw-charts-in-svg-from-data-chart-py-returns.md) | Accepted |
| [17. Run every lab and model on the learner's device](0017-run-every-lab-and-model-on-the-learners-device.md) | Accepted |
| [18. Keep progress as a log of attempts](0018-keep-progress-as-a-log-of-attempts.md) | Accepted |
| [19. Sign in with GitHub or Google, in the browser](0019-sign-in-with-github-or-google-in-the-browser.md) | Accepted |
| [20. Schedule review with FSRS, from a log of reviews](0020-schedule-review-with-fsrs-from-a-log-of-reviews.md) | Accepted |
| [21. Test asyncio code on an event loop with a virtual clock](0021-test-asyncio-code-on-a-virtual-clock.md) | Accepted |
| [22. Type-check a stage's code with mypy, in Pyodide and CPython alike](0022-type-check-a-stages-code-with-mypy-in-pyodide.md) | Accepted |
| [23. Time an interview problem from its start, with the plan before the code](0023-time-an-interview-problem-from-its-start.md) | Accepted |
| [24. Test a FastAPI app in process, through httpx on the test's loop](0024-test-a-fastapi-app-in-process-through-httpx.md) | Accepted |
| [25. Download a lab as a project the learner runs with uv](0025-download-a-lab-as-a-project-run-with-uv.md) | Accepted |
| [26. Show a course as a map of its modules](0026-show-a-course-as-a-map-of-its-modules.md) | Accepted |
| [27. Check a from-scratch build against a library's recorded results](0027-check-a-from-scratch-build-against-recorded-results.md) | Accepted |
| [28. Run a lab that needs PyTorch from its download, and bring its results back by a link](0028-run-a-pytorch-lab-from-its-download.md) | Accepted |
| [29. Fetch a machine lab's large files from their publishers, pinned by size and sha256](0029-fetch-a-machine-labs-large-files-from-their-publishers.md) | Accepted |
| [30. Give a lab's make.py the lab's data, fetched files included](0030-give-a-labs-make-py-the-labs-data.md) | Accepted |
| [31. Test a lab's model calls against a scripted model](0031-test-a-labs-model-calls-against-a-scripted-model.md) | Accepted |
| [32. Run a lab's model on the learner's machine with llama.cpp's server](0032-run-a-labs-model-with-llama-cpps-server.md) | Superseded by 34 |
| [33. Run a lab's database on the learner's machine with Postgres and pgvector](0033-run-a-labs-database-with-postgres-and-pgvector.md) | Accepted |
| [34. Serve a lab's models on the learner's machine with llama.cpp's server](0034-serve-a-labs-models-with-llama-cpps-server.md) | Accepted, amended by 36 |
| [35. Answer a lab's models through a forwarder that keeps each connection open](0035-answer-a-labs-models-through-a-forwarder.md) | Accepted |
| [36. Let a lab give its chat model a longer context](0036-let-a-lab-give-its-chat-model-a-longer-context.md) | Accepted |
| [37. Give a machine lab code its learner builds on](0037-give-a-machine-lab-code-its-learner-builds-on.md) | Accepted |

New records start from [the template](template.md) and take the next number.
