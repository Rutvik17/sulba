The first piece comes once the prompt is read. With five passages, half the replies show their first piece within {% $fig.first_median_five %} seconds and 95% within {% $fig.first_five %}; with three, {% $fig.first_median_three %} and {% $fig.first_three %}. The server takes from its cache only the start a prompt shares with the one before it, the instructions and at times a first passage, {% $fig.cached %} tokens a request on average, so it reads nearly all of each prompt afresh.

Writing takes the rest. Half the whole replies take {% $fig.whole_median_five %} seconds or less with five passages and {% $fig.whole_median_three %} with three, and 95% take {% $fig.whole_five %} and {% $fig.whole_three %}. One after another, the server writes {% $fig.hourly_five %} replies an hour with five passages and {% $fig.hourly_three %} with three.

A percentile says what most students wait, where a mean hides the slowest. The busy share says how close the server comes to its limit: near 1, it's answering all hour, and a question that comes while it's busy waits for the ones ahead of it, on top of its own reply.

These timings are of one reply at a time. llama-server can take several requests at once, in its slots (`--parallel`), and how much faster that makes an hour's replies on the office's server is for timings of replies taken at once to say.
