A broadband company takes {% $fig.calls %} support calls a day over {% $fig.hours %} hours, and its phone system writes a transcript of each one. Managers want each call summarised within an hour of its end: the problem, what the agent did, and whether it was solved. They also want a weekly view of the most common problems.

Design it. Take these as given:

- a transcript is about {% $fig.transcript %} tokens, the instructions {% $fig.instructions %} more, and a summary about {% $fig.summary %};
- the model costs {% $fig.price_in %} per million tokens in and {% $fig.price_out %} per million out.
