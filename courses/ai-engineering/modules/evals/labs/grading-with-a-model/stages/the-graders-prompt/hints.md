`environment.globals["raise_exception"] = refuse` makes a function of yours one the template can call.

---

A keyword argument to `render` passes anything the template uses, a function included: `strftime_now=lambda _: today`.

---

`reply.json()["choices"][0]["logprobs"]["content"][0]["top_logprobs"]` holds the likeliest first tokens, each with its `token` and its `logprob`.
