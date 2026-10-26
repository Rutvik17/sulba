A software company of {% $fig.engineers %} engineers opens about {% $fig.prs %} pull requests a day. It wants a bot that comments on each one with the problems a reviewer would raise: bugs, missing tests and security mistakes. Engineers dislike noisy tools: the last linter added was turned off within a month.

Design it: what the bot reads, what it comments, and how you keep its comments worth reading. Take these as given:

- a pull request's diff is about {% $fig.diff %} tokens, and the code the bot adds around it about {% $fig.context %} more;
- the bot's comments are about {% $fig.output %} tokens a pull request;
- the model costs {% $fig.price_in %} per million tokens in and {% $fig.price_out %} per million out.
