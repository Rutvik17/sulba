Write the brief's four points as the plan's test cases first: each is one scripted reply, or two, and what `triage` should give.

---

One regular expression finds the number in every form: `\b\d{3}[- ]?\d{2}[- ]?\d{4}\b`. The word boundaries keep it from matching inside a longer run of digits, such as a phone number.

---

Read a reply with a function that gives the queue or `None`, and ask at most twice. `httpx.HTTPError` covers a timeout and a dropped connection; `response.is_error` covers an error the model answers with.
