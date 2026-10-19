The model writes each call from what it has read, and some of that was written by someone who wants what isn't theirs: a customer asking for another's booking, or a review telling the model what to do. So the tools take each call as if a stranger wrote it. Who the customer is comes from the shop's sign-in, which the code holds and the model never sees as a parameter, and every query is held to that customer. Tools that act for a user, with only that user's rights, are among the defences against excessive agency in OWASP's Top 10 for LLM Applications.

A booking that belongs to someone else reads exactly as a missing one, so no answer says whether a reference exists for anyone else.

A reference is text the model wrote, and in SQL built by formatting, `B-2001' OR '1'='1` would close the string and add a condition every row meets. As a parameter, it's only ever a value to compare. The same goes for every value the model passes, which is why the arguments are checked before any tool runs.

Reviews are text other people wrote, so they reach the model only inside a tool's result, as JSON strings, and never in its instructions. They go without their authors' names, which no answer needs.
